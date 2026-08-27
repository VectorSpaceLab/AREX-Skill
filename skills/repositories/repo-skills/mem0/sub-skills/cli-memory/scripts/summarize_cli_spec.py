#!/usr/bin/env python3
"""Summarize a Mem0 CLI spec JSON file without network access.

Examples:
  python summarize_cli_spec.py mem0-cli-spec.json
  mem0 help --json | python summarize_cli_spec.py - --format json
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any


class SpecError(ValueError):
    """Raised when a CLI spec is missing required structure."""


def _read_json(path: str) -> Any:
    if path == "-":
        raw = sys.stdin.read()
        source = "stdin"
    else:
        raw = Path(path).read_text(encoding="utf-8")
        source = path
    try:
        return json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SpecError(f"{source}: invalid JSON: {exc}") from exc


def _as_list(value: Any) -> list[Any]:
    return value if isinstance(value, list) else []


def _require_spec(spec: Any) -> dict[str, Any]:
    if not isinstance(spec, dict):
        raise SpecError("spec root must be a JSON object")
    commands = spec.get("commands")
    if commands is not None and not isinstance(commands, list):
        raise SpecError("spec.commands must be a list when present")
    cli = spec.get("cli")
    if cli is not None and not isinstance(cli, dict):
        raise SpecError("spec.cli must be an object when present")
    return spec


def _flags(option: dict[str, Any]) -> str:
    flags = option.get("flags", [])
    if isinstance(flags, list):
        return ", ".join(str(flag) for flag in flags)
    return str(flags or option.get("name", ""))


def _option_summary(option: Any) -> dict[str, Any]:
    if not isinstance(option, dict):
        return {"name": str(option), "flags": [], "type": None, "default": None, "help": ""}
    summary: dict[str, Any] = {
        "name": option.get("name"),
        "flags": option.get("flags", []),
        "type": option.get("type"),
        "help": option.get("help", ""),
    }
    if "default" in option:
        summary["default"] = option.get("default")
    if option.get("envVar"):
        summary["envVar"] = option.get("envVar")
    if option.get("panel"):
        summary["panel"] = option.get("panel")
    return summary


def build_summary(spec: dict[str, Any], only_commands: set[str] | None = None) -> dict[str, Any]:
    cli = spec.get("cli", {}) if isinstance(spec.get("cli"), dict) else {}
    config = spec.get("config", {}) if isinstance(spec.get("config"), dict) else {}
    commands: list[dict[str, Any]] = []

    for command in _as_list(spec.get("commands")):
        if not isinstance(command, dict):
            continue
        name = str(command.get("name", ""))
        if only_commands and name not in only_commands:
            continue
        commands.append(
            {
                "name": name,
                "description": command.get("description", ""),
                "usage": command.get("usage"),
                "needsBackend": command.get("needsBackend"),
                "needsConfig": command.get("needsConfig"),
                "resolveIds": command.get("resolveIds"),
                "resolveGraph": command.get("resolveGraph"),
                "confirmDangerous": command.get("confirmDangerous"),
                "defaultOutput": command.get("defaultOutput"),
                "outputFormats": command.get("outputFormats", []),
                "arguments": command.get("arguments", []),
                "options": [_option_summary(option) for option in _as_list(command.get("options"))],
                "apiEndpoint": command.get("apiEndpoint"),
            }
        )

    env_vars: list[dict[str, str]] = []
    sections = config.get("sections", {}) if isinstance(config.get("sections"), dict) else {}
    for section_name, section in sections.items():
        fields = section.get("fields", {}) if isinstance(section, dict) else {}
        for field_name, field in fields.items():
            if not isinstance(field, dict):
                continue
            if field.get("envVar"):
                env_vars.append(
                    {
                        "section": str(section_name),
                        "field": str(field_name),
                        "envVar": str(field.get("envVar")),
                        "type": str(field.get("type", "")),
                    }
                )

    global_options = [_option_summary(option) for option in _as_list(spec.get("globalOptions"))]

    return {
        "specVersion": spec.get("specVersion"),
        "cli": {
            "name": cli.get("name", "mem0"),
            "version": cli.get("version"),
            "description": cli.get("description", ""),
        },
        "config": {
            "configDir": config.get("configDir"),
            "configFile": config.get("configFile"),
            "defaultBaseUrl": config.get("defaultBaseUrl"),
            "envVars": env_vars,
        },
        "globalOptions": global_options,
        "commands": commands,
    }


def _markdown_table(headers: list[str], rows: list[list[str]]) -> str:
    out = ["| " + " | ".join(headers) + " |", "| " + " | ".join("---" for _ in headers) + " |"]
    for row in rows:
        out.append("| " + " | ".join(cell.replace("\n", " ") for cell in row) + " |")
    return "\n".join(out)


def render_markdown(summary: dict[str, Any], include_options: bool = True) -> str:
    cli = summary["cli"]
    lines = [
        f"# {cli.get('name', 'mem0')} CLI Summary",
        "",
        f"- Spec version: `{summary.get('specVersion')}`",
        f"- CLI version in spec: `{cli.get('version')}`",
        f"- Description: {cli.get('description') or 'n/a'}",
        f"- Config: `{summary['config'].get('configDir') or '~/.mem0'}/{summary['config'].get('configFile') or 'config.json'}`",
        f"- Default base URL: `{summary['config'].get('defaultBaseUrl') or 'https://api.mem0.ai'}`",
        "",
    ]

    env_rows = [
        [item["envVar"], f"{item['section']}.{item['field']}", item.get("type", "")]
        for item in summary["config"].get("envVars", [])
    ]
    if env_rows:
        lines.extend(["## Environment Variables", "", _markdown_table(["Variable", "Field", "Type"], env_rows), ""])

    command_rows = []
    for command in summary["commands"]:
        outputs = command.get("outputFormats") or []
        command_rows.append(
            [
                f"`{command.get('name')}`",
                str(command.get("usage") or ""),
                str(command.get("defaultOutput") or ""),
                ", ".join(f"`{item}`" for item in outputs),
                "yes" if command.get("needsBackend") else "no",
            ]
        )
    lines.extend([
        "## Commands",
        "",
        _markdown_table(["Command", "Usage", "Default output", "Formats", "Backend"], command_rows),
        "",
    ])

    if include_options:
        for command in summary["commands"]:
            lines.extend([f"## `{command.get('name')}`", "", command.get("description") or "", ""])
            args = command.get("arguments") or []
            if args:
                arg_rows = []
                for arg in args:
                    if not isinstance(arg, dict):
                        continue
                    arg_rows.append(
                        [
                            f"`{arg.get('name')}`",
                            str(arg.get("type", "")),
                            "yes" if arg.get("required") else "no",
                            str(arg.get("help", "")),
                        ]
                    )
                if arg_rows:
                    lines.extend(["Arguments:", "", _markdown_table(["Name", "Type", "Required", "Help"], arg_rows), ""])
            opts = command.get("options") or []
            if opts:
                opt_rows = []
                for opt in opts:
                    opt_rows.append(
                        [
                            f"`{_flags(opt)}`",
                            str(opt.get("type") or ""),
                            json.dumps(opt.get("default")) if "default" in opt else "",
                            str(opt.get("help") or ""),
                        ]
                    )
                lines.extend(["Options:", "", _markdown_table(["Flags", "Type", "Default", "Help"], opt_rows), ""])

    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Summarize a Mem0 CLI spec JSON file. Reads only local files/stdin and never contacts Mem0."
    )
    parser.add_argument("spec", help="Path to cli-spec JSON, or '-' for stdin.")
    parser.add_argument("--format", choices=["markdown", "json"], default="markdown", help="Output format.")
    parser.add_argument(
        "--command",
        action="append",
        dest="commands",
        help="Limit output to one command name. May be repeated.",
    )
    parser.add_argument("--no-options", action="store_true", help="In markdown mode, omit per-command option tables.")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        spec = _require_spec(_read_json(args.spec))
        summary = build_summary(spec, set(args.commands) if args.commands else None)
    except (OSError, SpecError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2

    if args.format == "json":
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        sys.stdout.write(render_markdown(summary, include_options=not args.no_options))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
