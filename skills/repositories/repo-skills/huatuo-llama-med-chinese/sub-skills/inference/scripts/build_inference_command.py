#!/usr/bin/env python3
"""Build safe dry-run Huatuo/BenTsao inference commands.

This helper intentionally uses only the Python standard library. It never imports
model-serving libraries, loads checkpoints, downloads weights, or starts Gradio.
"""

from __future__ import annotations

import argparse
import os
import shlex
import sys
from pathlib import Path
from typing import Iterable, List, Tuple

WORKFLOWS = ("medical-qa", "literature-single", "literature-multi", "gradio")
MODEL_FAMILIES = ("llama-alpaca", "bloom-huozi", "custom")


def fire_bool(value: bool) -> str:
    return "True" if value else "False"


def auto_template(workflow: str, model_family: str) -> str:
    if workflow in {"literature-single", "literature-multi"}:
        return "literature_template"
    if model_family == "bloom-huozi":
        return "bloom_deploy"
    return "med_template"


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Print a shell-safe dry-run command for Huatuo/BenTsao medical QA, "
            "literature, or Gradio inference workflows. The command is not executed."
        )
    )
    parser.add_argument(
        "--workflow",
        choices=WORKFLOWS,
        required=True,
        help="Inference workflow to plan.",
    )
    parser.add_argument(
        "--base-model",
        required=True,
        help="Base model path or Hugging Face id; must match the LoRA adapter family.",
    )
    parser.add_argument(
        "--lora-weights",
        required=True,
        help="LoRA adapter path or id. Required for the command plan even when --no-lora is used as a baseline flag.",
    )
    parser.add_argument(
        "--instruct-dir",
        help="Medical QA JSONL input path. Required for --workflow medical-qa.",
    )
    parser.add_argument(
        "--prompt-template",
        help="Override the workflow/model-family default prompt template name.",
    )
    parser.add_argument(
        "--model-family",
        choices=MODEL_FAMILIES,
        default="llama-alpaca",
        help="Model family hint used to choose a default prompt template. Default: %(default)s.",
    )
    parser.add_argument(
        "--python",
        dest="python_executable",
        default="python",
        help="Python executable to place in the printed command. Default: %(default)s.",
    )
    parser.add_argument(
        "--workdir",
        help="Optional working directory prefix for the printed command; useful when templates are resolved relative to cwd.",
    )
    parser.add_argument(
        "--load-8bit",
        action="store_true",
        help="Add --load_8bit True to the printed command.",
    )
    parser.add_argument(
        "--no-lora",
        action="store_true",
        help="Print --use_lora False for baseline medical/literature comparisons. Not valid for Gradio.",
    )
    parser.add_argument(
        "--server-name",
        default="127.0.0.1",
        help="Gradio server interface for --workflow gradio. Safe default: %(default)s.",
    )
    parser.add_argument(
        "--share-gradio",
        action="store_true",
        help="For --workflow gradio, print --share_gradio True. Requires explicit serving-risk acceptance.",
    )
    parser.add_argument(
        "--check-local-paths",
        action="store_true",
        help="Lightweight existence checks for local-looking paths. Still does not import or download models.",
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Accepted for clarity; dry-run behavior is always enabled and commands are never executed.",
    )
    return parser


def validate_args(parser: argparse.ArgumentParser, args: argparse.Namespace) -> None:
    if args.workflow == "medical-qa" and not args.instruct_dir:
        parser.error("--instruct-dir is required for --workflow medical-qa")
    if args.workflow != "medical-qa" and args.instruct_dir:
        # Not fatal; the warning list will explain that it is ignored.
        pass
    if args.workflow == "gradio" and args.no_lora:
        parser.error("--no-lora is not valid for --workflow gradio because the serving workflow always loads a LoRA adapter")


def command_tokens(args: argparse.Namespace, template: str) -> List[str]:
    if args.workflow == "medical-qa":
        cmd = [
            args.python_executable,
            "infer.py",
            "--base_model",
            args.base_model,
        ]
        if args.load_8bit:
            cmd.extend(["--load_8bit", "True"])
        if args.no_lora:
            cmd.extend(["--use_lora", "False"])
        else:
            cmd.extend(["--lora_weights", args.lora_weights, "--use_lora", "True"])
        cmd.extend([
            "--instruct_dir",
            args.instruct_dir,
            "--prompt_template",
            template,
        ])
        return cmd

    if args.workflow in {"literature-single", "literature-multi"}:
        mode = "single" if args.workflow == "literature-single" else "multi"
        cmd = [
            args.python_executable,
            "infer_literature.py",
            "--base_model",
            args.base_model,
        ]
        if args.load_8bit:
            cmd.extend(["--load_8bit", "True"])
        if args.no_lora:
            cmd.extend(["--use_lora", "False"])
        else:
            cmd.extend(["--lora_weights", args.lora_weights, "--use_lora", "True"])
        cmd.extend([
            "--single_or_multi",
            mode,
            "--prompt_template",
            template,
        ])
        return cmd

    # gradio
    cmd = [
        args.python_executable,
        "generate.py",
        "--base_model",
        args.base_model,
    ]
    if args.load_8bit:
        cmd.extend(["--load_8bit", "True"])
    cmd.extend([
        "--lora_weights",
        args.lora_weights,
        "--prompt_template",
        template,
        "--server_name",
        args.server_name,
        "--share_gradio",
        fire_bool(args.share_gradio),
    ])
    return cmd


def shell_command(args: argparse.Namespace, tokens: List[str]) -> str:
    command = shlex.join(tokens)
    if args.workdir:
        return f"cd {shlex.quote(args.workdir)} && {command}"
    return command


def localish(value: str) -> bool:
    if not value:
        return False
    expanded = os.path.expanduser(value)
    return (
        value.startswith(("/", "./", "../", "~"))
        or Path(expanded).exists()
        or Path(expanded).is_absolute()
    )


def resolve_for_check(value: str, workdir: str | None) -> Path:
    path = Path(os.path.expanduser(value))
    if not path.is_absolute() and workdir:
        path = Path(os.path.expanduser(workdir)) / path
    return path


def append_path_warnings(args: argparse.Namespace, warnings: List[str]) -> None:
    if not args.check_local_paths:
        return

    if args.workdir:
        workdir_path = Path(os.path.expanduser(args.workdir))
        if not workdir_path.exists():
            warnings.append(f"--workdir does not exist from this dry-run process: {args.workdir!r}")
        elif not workdir_path.is_dir():
            warnings.append(f"--workdir is not a directory from this dry-run process: {args.workdir!r}")

    if args.workflow == "medical-qa" and args.instruct_dir:
        instruct_path = resolve_for_check(args.instruct_dir, args.workdir)
        if not instruct_path.exists():
            warnings.append(f"Medical QA --instruct-dir was not found by lightweight path check: {args.instruct_dir!r}")

    for label, value in (("base model", args.base_model), ("LoRA weights", args.lora_weights)):
        if localish(value):
            candidate = resolve_for_check(value, args.workdir)
            if not candidate.exists():
                warnings.append(f"Local-looking {label} path was not found by lightweight path check: {value!r}")
        else:
            warnings.append(
                f"{label.title()} {value!r} does not look like a local path; assuming it is an id or runtime-resolved value."
            )


def warning_lines(args: argparse.Namespace, template: str, template_was_auto: bool) -> List[str]:
    warnings: List[str] = [
        "Dry run only: this helper prints a command and never imports model libraries, loads checkpoints, downloads weights, or starts Gradio.",
        "The printed command assumes a Huatuo/BenTsao-compatible runtime project with the named workflow entrypoint and templates available from the command working directory.",
        "Actual medical outputs are research artifacts and must not be treated as clinical advice.",
    ]

    if template_was_auto:
        warnings.append(
            f"No --prompt-template override was supplied; selected {template!r} from workflow={args.workflow!r} and model-family={args.model_family!r}."
        )
    else:
        warnings.append(f"Using explicit prompt template override: {template!r}.")

    if args.workflow in {"medical-qa", "literature-single", "literature-multi"}:
        warnings.append(
            "The medical QA and literature CLI runners are effectively CUDA-required in the evidenced implementation; without CUDA they can fail with NameError: device is not defined."
        )

    if args.workflow == "medical-qa" and args.model_family == "bloom-huozi" and template != "bloom_deploy":
        warnings.append("Bloom/Huozi medical QA usually expects bloom_deploy; verify response_split if overriding it.")

    if args.workflow in {"literature-single", "literature-multi"} and template != "literature_template":
        warnings.append("Literature workflows usually expect literature_template; wrong response_split markers can echo prompts or break parsing.")

    if args.workflow in {"literature-single", "literature-multi"} and args.model_family == "bloom-huozi":
        warnings.append(
            "Repository literature workflow evidence is strongest for the LLaMA literature adapter; validate Bloom/Huozi literature behavior before trusting outputs."
        )

    if args.workflow == "literature-multi":
        warnings.append("The multi-turn workflow is interactive, reads five stdin turns, and accumulates <user>/<bot> history.")

    if args.workflow == "gradio":
        warnings.append(
            "Gradio serving can expose a medical model. The builder defaults to server_name=127.0.0.1 and share_gradio=False for safety."
        )
        if args.server_name in {"0.0.0.0", "::"}:
            warnings.append("server_name binds broadly; use only after explicit network exposure approval.")
        if args.share_gradio:
            warnings.append("share_gradio=True can create an externally reachable Gradio share link; use only after explicit approval.")

    if args.workflow != "medical-qa" and args.instruct_dir:
        warnings.append("--instruct-dir is ignored for literature and Gradio workflows.")

    if args.no_lora:
        warnings.append("--no-lora produces a baseline/base-model command, not a Huatuo/BenTsao LoRA medical model command.")
    elif args.lora_weights == "tloen/alpaca-lora-7b":
        warnings.append("The default-looking Alpaca LoRA id is a placeholder for baseline examples; use the intended medical or literature adapter for Huatuo/BenTsao behavior.")

    if args.load_8bit:
        warnings.append("--load-8bit requires a compatible bitsandbytes/CUDA stack during real execution; this dry run does not verify it.")

    append_path_warnings(args, warnings)
    return warnings


def print_report(args: argparse.Namespace, command: str, warnings: Iterable[str]) -> None:
    print("DRY-RUN COMMAND")
    print(command)
    print()
    print("WARNINGS")
    for item in warnings:
        print(f"- {item}")


def main(argv: List[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    validate_args(parser, args)

    template_was_auto = args.prompt_template is None
    template = args.prompt_template or auto_template(args.workflow, args.model_family)
    tokens = command_tokens(args, template)
    command = shell_command(args, tokens)
    warnings = warning_lines(args, template, template_was_auto)
    print_report(args, command, warnings)
    return 0


if __name__ == "__main__":
    sys.exit(main())
