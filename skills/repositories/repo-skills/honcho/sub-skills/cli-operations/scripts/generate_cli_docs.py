#!/usr/bin/env python3
"""Generate Honcho CLI command documentation from an installed honcho-cli.

This helper imports ``honcho_cli.main:app`` from the active Python environment,
walks the Click/Typer command tree, and emits either a JSON inventory or a
Mintlify-style MDX snippet. It does not call the Honcho API and does not require
an original source checkout.
"""

from __future__ import annotations

import argparse
import difflib
import json
import sys
from pathlib import Path
from typing import Any

try:
    import click
    import typer.main
    from honcho_cli.main import app
except Exception as exc:  # pragma: no cover - environment-specific import guard
    raise SystemExit(
        "Could not import honcho_cli. Run this script with a Python environment "
        "where honcho-cli is installed. Original import error: " + repr(exc)
    ) from exc

GLOBAL_OPTIONS: set[tuple[str | None, str]] = {
    ("--workspace", "Override workspace ID"),
    ("--peer", "Override peer ID"),
    ("--session", "Override session ID"),
    ("--json", "Force JSON output"),
}

HEADER = """{/*
  GENERATED from the installed honcho-cli Typer app — do not edit by hand.
  Regenerate with: python scripts/generate_cli_docs.py --format mdx --output <file>
*/}

"""


def _escape_mdx(text: str) -> str:
    """Escape MDX-sensitive characters in prose."""
    return (
        text.replace("\\", "\\\\")
        .replace("{", "\\{")
        .replace("}", "\\}")
        .replace("<", "\\<")
    )


def _attr(value: str) -> str:
    """Escape a string for a JSX double-quoted attribute."""
    return value.replace("\\", "\\\\").replace('"', "'")


def _long_opt(param: click.Option) -> str | None:
    return next((opt for opt in param.opts if opt.startswith("--")), None)


def _short_opt(param: click.Option) -> str | None:
    return next(
        (opt for opt in param.opts if opt.startswith("-") and not opt.startswith("--")),
        None,
    )


def _is_global(param: click.Parameter) -> bool:
    if not isinstance(param, click.Option) or not param.help:
        return False
    return (_long_opt(param), param.help) in GLOBAL_OPTIONS


def _param_type(param: click.Parameter) -> str:
    if isinstance(param, click.Option) and param.is_flag:
        return "boolean"
    if isinstance(param.type, click.Choice):
        return "string"
    type_name = getattr(param.type, "name", "")
    if type_name in {"integer", "int", "float", "decimal"}:
        return "number"
    if type_name == "boolean":
        return "boolean"
    return "string"


def _param_path(param: click.Parameter) -> str:
    if isinstance(param, click.Argument):
        return param.name or ""
    return _long_opt(param) or (param.opts[0] if param.opts else "")


def _param_required(param: click.Parameter) -> bool:
    if isinstance(param, click.Argument):
        return param.required
    if isinstance(param, click.Option):
        return bool(param.required)
    return False


def _default_value(param: click.Parameter) -> Any | None:
    default = param.default
    if default is None or default is False or callable(default):
        return None
    if isinstance(default, (list, tuple)) and not default:
        return None
    return default


def _ensure_period(text: str) -> str:
    return text if text.endswith((".", "?", "!", ":")) else text + "."


def _param_description(param: click.Parameter) -> str:
    parts: list[str] = []
    if isinstance(param, click.Option):
        if param.help:
            parts.append(_ensure_period(param.help.strip()))
        short = _short_opt(param)
        if short:
            parts.append(f"Short alias: `{short}`.")
        if param.secondary_opts:
            neg = " / ".join(f"`{opt}`" for opt in param.secondary_opts)
            parts.append(f"Negate with {neg}.")
        if isinstance(param.type, click.Choice):
            choices = ", ".join(f"`{choice}`" for choice in param.type.choices)
            parts.append(f"One of: {choices}.")
    return " ".join(parts)


def _params_of(cmd: click.Command, *, strip_globals: bool) -> list[click.Parameter]:
    args = [param for param in cmd.params if isinstance(param, click.Argument)]
    opts = [
        param
        for param in cmd.params
        if isinstance(param, click.Option)
        and not param.hidden
        and not (strip_globals and _is_global(param))
    ]
    return args + opts


def _invocation_line(path: list[str], cmd: click.Command) -> str:
    parts = [" ".join(path)]
    for arg in [param for param in cmd.params if isinstance(param, click.Argument)]:
        placeholder = f"<{arg.name}>"
        if not arg.required:
            placeholder = f"[{placeholder}]"
        parts.append(placeholder)
    return " ".join(parts)


def _param_record(param: click.Parameter) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": _param_path(param),
        "type": _param_type(param),
        "required": _param_required(param),
    }
    if isinstance(param, click.Option):
        record["opts"] = list(param.opts)
        record["secondary_opts"] = list(param.secondary_opts)
        record["help"] = param.help or ""
    default = _default_value(param)
    if default is not None:
        record["default"] = default
    if isinstance(param.type, click.Choice):
        record["choices"] = list(param.type.choices)
    return record


def _command_record(cmd: click.Command, path: list[str]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "path": path,
        "name": path[-1],
        "help": cmd.help or "",
        "invocation": _invocation_line(path, cmd),
        "params": [_param_record(p) for p in _params_of(cmd, strip_globals=True)],
    }
    if isinstance(cmd, click.Group):
        record["commands"] = [
            _command_record(cmd.commands[name], path + [name])
            for name in sorted(cmd.commands)
        ]
    return record


def build_inventory() -> dict[str, Any]:
    root: click.Command = typer.main.get_command(app)
    if not isinstance(root, click.Group):
        raise SystemExit("Expected honcho Typer app to compile to a Click group")
    return {
        "program": "honcho",
        "commands": [
            _command_record(root.commands[name], ["honcho", name])
            for name in sorted(root.commands)
        ],
    }


def _render_param(param: click.Parameter) -> list[str]:
    props = [f'path="{_attr(_param_path(param))}"', f'type="{_param_type(param)}"']
    if _param_required(param):
        props.append("required")
    default = _default_value(param)
    if default is not None:
        props.append(f'default="{_attr(str(default))}"')
    body = _escape_mdx(_param_description(param)).strip()
    open_tag = f"<ParamField {' '.join(props)}>"
    if body:
        return [open_tag, f"  {body}", "</ParamField>"]
    return [open_tag.replace(">", " />")]


def _render_leaf(cmd: click.Command, path: list[str]) -> list[str]:
    lines = ["```bash", _invocation_line(path, cmd), "```", ""]
    for param in _params_of(cmd, strip_globals=True):
        lines.extend(_render_param(param))
    return lines


def _render_accordion(cmd: click.Command, path: list[str]) -> list[str]:
    lines = [f'<Accordion title="{_attr(path[-1])}">']
    if cmd.help:
        lines.append(_escape_mdx(cmd.help.strip()))
        lines.append("")
    lines.extend(_render_leaf(cmd, path))
    lines.append("</Accordion>")
    return lines


def build_mdx() -> str:
    root: click.Command = typer.main.get_command(app)
    if not isinstance(root, click.Group):
        raise SystemExit("Expected honcho Typer app to compile to a Click group")

    body: list[str] = []
    for name in sorted(root.commands):
        cmd = root.commands[name]
        path = ["honcho", name]
        body.extend([f"## {' '.join(path)}", ""])
        if cmd.help:
            body.extend([_escape_mdx(cmd.help.strip()), ""])
        if isinstance(cmd, click.Group) and cmd.commands:
            body.append("<AccordionGroup>")
            for sub_name in sorted(cmd.commands):
                body.extend(_render_accordion(cmd.commands[sub_name], path + [sub_name]))
            body.extend(["</AccordionGroup>", ""])
        else:
            body.extend(_render_leaf(cmd, path))
            body.append("")
    return HEADER + "\n".join(body).rstrip() + "\n"


def _write_or_check(content: str, output: Path | None, check: Path | None) -> int:
    if check is not None:
        existing = check.read_text() if check.exists() else ""
        if existing != content:
            diff = "".join(
                difflib.unified_diff(
                    existing.splitlines(keepends=True),
                    content.splitlines(keepends=True),
                    fromfile=str(check),
                    tofile="generated",
                )
            )
            print(f"CLI docs are stale: {check}", file=sys.stderr)
            if diff:
                print(diff, file=sys.stderr)
            return 1
        return 0

    if output is not None:
        output.parent.mkdir(parents=True, exist_ok=True)
        output.write_text(content)
    else:
        sys.stdout.write(content)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--format",
        choices=("mdx", "json"),
        default="mdx",
        help="Output format. Default: mdx.",
    )
    parser.add_argument("--output", type=Path, help="Write generated output to this file.")
    parser.add_argument(
        "--check",
        type=Path,
        help="Exit non-zero if this file differs from generated output.",
    )
    args = parser.parse_args(argv)

    if args.format == "json":
        content = json.dumps(build_inventory(), indent=2) + "\n"
    else:
        content = build_mdx()

    return _write_or_check(content, args.output, args.check)


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
