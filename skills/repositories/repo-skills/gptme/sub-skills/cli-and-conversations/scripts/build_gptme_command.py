#!/usr/bin/env python3
"""Build a shell-quoted gptme command without executing it."""

from __future__ import annotations

import argparse
import json
import re
import shlex
import sys
from pathlib import Path
from typing import Any

_CONTROL_RE = re.compile(r"[\x00-\x1f\x7f]")


def split_csv(values: list[str] | None) -> list[str]:
    result: list[str] = []
    for value in values or []:
        result.extend(part.strip() for part in value.split(",") if part.strip())
    return result


def validate_conversation_name(name: str | None) -> None:
    if name is None:
        return
    if not name.strip():
        raise ValueError("conversation name must not be empty or whitespace-only")
    if name != name.strip():
        raise ValueError("conversation name cannot start or end with whitespace")
    if name in {".", ".."} or "/" in name or "\\" in name:
        raise ValueError("conversation name must be a single path component")
    if _CONTROL_RE.search(name):
        raise ValueError("conversation name cannot contain control characters")


def validate_model(model: str | None) -> None:
    if model is None:
        return
    if not model.strip():
        raise ValueError("model name cannot be empty")
    if "/" in model and any(part == "" for part in model.split("/")):
        raise ValueError("model path components cannot be empty")


def looks_like_custom_tool(spec: str) -> bool:
    stripped = spec.removeprefix("+").removeprefix("-")
    return (
        stripped.endswith(".py")
        or stripped.startswith(("/", "./", "../", "~"))
        or (len(stripped) > 2 and stripped[1] == ":" and stripped[2] in "/\\")
    )


def validate_tools(tool_specs: list[str], check_custom_paths: bool) -> list[str]:
    flattened = split_csv(tool_specs)
    if not flattened:
        return []

    lowered = [item.lower() for item in flattened]
    if "none" in lowered and len(flattened) > 1:
        others = [item for item in flattened if item.lower() != "none"]
        raise ValueError("cannot combine 'none' with other tools: " + ", ".join(others))

    additive = any(item.startswith("+") for item in flattened)
    exclusion = any(item.startswith("-") for item in flattened)
    if additive and exclusion:
        raise ValueError("cannot mix '+tool' additive syntax with '-tool' exclusion syntax")
    if exclusion:
        bare = [item for item in flattened if not item.startswith("-")]
        if bare:
            raise ValueError(
                "cannot mix bare tool names with '-tool' exclusion syntax: "
                + ", ".join(bare)
            )

    for item in flattened:
        clean = item.removeprefix("+").removeprefix("-")
        if not clean:
            raise ValueError(f"empty tool name in spec {item!r}")
        if looks_like_custom_tool(item):
            expanded = Path(clean).expanduser()
            if expanded.suffix != ".py":
                raise ValueError(f"custom tool path must be a .py file: {clean}")
            if check_custom_paths and not expanded.exists():
                raise ValueError(f"custom tool file does not exist: {clean}")

    return flattened


def is_explicit_local_path(value: str) -> bool:
    candidate = value.removeprefix("@")
    return candidate.startswith(("/", "~/", "./", "../")) or (
        len(candidate) >= 3
        and candidate[1] == ":"
        and candidate[2] in ("/", "\\")
        and candidate[0].isalpha()
    )


def add_option(cmd: list[str], option: str, value: str | None = None) -> None:
    if value is None:
        cmd.append(option)
    elif value.startswith("-"):
        cmd.append(f"{option}={value}")
    else:
        cmd.extend([option, value])


def build_command(args: argparse.Namespace) -> tuple[list[str], list[str]]:
    warnings: list[str] = []
    validate_conversation_name(args.name)
    validate_model(args.model)
    tool_values = validate_tools(args.tools or [], args.check_custom_tool_paths)

    context_values = split_csv(args.context)
    if args.no_workspace and context_values:
        raise ValueError("--no-workspace and --context are mutually exclusive")
    if args.output_format == "json" and not args.non_interactive:
        raise ValueError("--output-format json requires --non-interactive")
    if args.non_interactive and not args.prompts and not args.resume and not args.show_prompt_stats:
        raise ValueError("--non-interactive requires --prompt, --resume, or --show-prompt-stats")

    prompts = args.prompts or []
    includes = args.includes or []
    if includes and not prompts:
        warnings.append("--include values were supplied without --prompt; they will become prompt arguments")
    for value in prompts + includes:
        if is_explicit_local_path(value):
            warnings.append(f"ensure explicit local path exists in the target working directory: {value}")
    if len(prompts) > 1:
        warnings.append("multiple --prompt values are emitted as chained turns separated by standalone '-'")
    if len(prompts) > 1 and any(prompt == "-" for prompt in prompts):
        warnings.append("a prompt exactly equal to '-' cannot be represented literally inside a multiprompt chain")
    if args.resume and args.name:
        warnings.append("--resume with --name requires that exact conversation to exist; it will not fall back to latest")
    elif args.resume:
        warnings.append("--resume without --name selects the latest conversation, normally filtered by workspace")
    if args.no_confirm or args.non_interactive:
        warnings.append("confirmation prompts will be skipped")
    if args.no_workspace:
        warnings.append("--no-workspace skips project prompt files and context commands, but tools/core prompt still load")

    cmd = ["gptme"]
    if args.name:
        add_option(cmd, "--name", args.name)
    if args.resume:
        add_option(cmd, "--resume")
    if args.workspace:
        add_option(cmd, "--workspace", args.workspace)
    if args.agent_path:
        add_option(cmd, "--agent-path", args.agent_path)
    if args.model:
        add_option(cmd, "--model", args.model)
    if args.system:
        add_option(cmd, "--system", args.system)
    for value in context_values:
        add_option(cmd, "--context", value)
    if args.no_workspace:
        add_option(cmd, "--no-workspace")
    if tool_values:
        # Emit a single normalized spec so gptme's own parser sees the same semantics.
        add_option(cmd, "--tools", ",".join(tool_values))
    if args.agent_profile:
        add_option(cmd, "--agent-profile", args.agent_profile)
    if args.tool_format:
        add_option(cmd, "--tool-format", args.tool_format)
    if args.no_confirm:
        add_option(cmd, "--no-confirm")
    if args.non_interactive:
        add_option(cmd, "--non-interactive")
    if args.output_format:
        add_option(cmd, "--output-format", args.output_format)
    if args.stream is False:
        add_option(cmd, "--no-stream")
    elif args.stream is True:
        add_option(cmd, "--stream")
    if args.show_prompt_stats:
        add_option(cmd, "--show-prompt-stats")

    if prompts:
        for index, prompt in enumerate(prompts):
            if index > 0:
                cmd.append("-")
            cmd.append(prompt)
            if index == 0:
                cmd.extend(includes)
    elif includes:
        cmd.extend(includes)

    return cmd, warnings


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Construct a safe shell-quoted gptme command without executing it.",
        epilog=(
            "Example: build_gptme_command.py --name refactor --system short "
            "--tools shell,read,patch,save --context files --prompt 'read the test' "
            "--prompt 'fix it' --prompt 'run the test'"
        ),
    )
    parser.add_argument("--prompt", dest="prompts", action="append", help="prompt turn; repeat for multiprompt chains")
    parser.add_argument("--include", dest="includes", action="append", help="file, URL, image, or extra context argument appended after the first prompt")
    parser.add_argument("--name", help="conversation ID/name")
    parser.add_argument("--resume", action="store_true", help="resume a previous conversation")
    parser.add_argument("--workspace", help="workspace directory or @log")
    parser.add_argument("--agent-path", help="agent workspace directory")
    parser.add_argument("--model", help="model string, e.g. provider/model")
    parser.add_argument("--system", help="system prompt selector such as full, full-noexamples, short, or custom text")
    parser.add_argument("--context", action="append", help="context section: all, files, or cmd; repeat or comma-separate")
    parser.add_argument("--no-workspace", action="store_true", help="skip project prompt files and context commands")
    parser.add_argument("--tools", action="append", help="tool spec, e.g. none, shell,read, +subagent, or -browser")
    parser.add_argument("--check-custom-tool-paths", action="store_true", help="verify custom .py tool paths exist on this machine")
    parser.add_argument("--agent-profile", help="agent profile name")
    parser.add_argument("--tool-format", choices=("markdown", "xml", "tool"), help="tool call format")
    parser.add_argument("--no-confirm", action="store_true", help="skip confirmation prompts")
    parser.add_argument("--non-interactive", "-n", action="store_true", help="build a non-interactive command")
    parser.add_argument("--output-format", choices=("text", "json"), help="output format; json requires --non-interactive")
    stream_group = parser.add_mutually_exclusive_group()
    stream_group.add_argument("--stream", dest="stream", action="store_true", help="force streaming responses")
    stream_group.add_argument("--no-stream", dest="stream", action="store_false", help="disable streaming responses")
    parser.set_defaults(stream=None)
    parser.add_argument("--show-prompt-stats", action="store_true", help="print prompt stats and exit")
    parser.add_argument("--json", dest="as_json", action="store_true", help="emit command and warnings as JSON")
    parser.add_argument("--explain", action="store_true", help="print explanatory notes after the command")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        cmd, warnings = build_command(args)
    except ValueError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    command_string = shlex.join(cmd)
    if args.as_json:
        payload: dict[str, Any] = {
            "command": command_string,
            "argv": cmd,
            "warnings": warnings,
            "executes": False,
        }
        print(json.dumps(payload, indent=2))
        return 0

    print(command_string)
    if args.explain or warnings:
        print()
        print("Notes:")
        print("- This helper only builds the command; it does not execute gptme.")
        for warning in warnings:
            print(f"- {warning}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
