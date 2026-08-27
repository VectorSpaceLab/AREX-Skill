#!/usr/bin/env python3
"""Extract Stable Diffusion WebUI CLI flags from modules/cmd_args.py safely.

The script uses only Python's standard-library AST parser. It does not import the
WebUI checkout, does not evaluate defaults, and does not execute launcher code.
"""

from __future__ import annotations

import argparse
import ast
import json
import sys
from pathlib import Path
from typing import Any


OUTPUT_FORMATS = ("json", "markdown")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Statically extract argparse flags from a Stable Diffusion WebUI modules/cmd_args.py file."
    )
    parser.add_argument(
        "--source",
        required=True,
        help="Path to the cmd_args.py source file to inspect.",
    )
    parser.add_argument(
        "--format",
        choices=OUTPUT_FORMATS,
        default="json",
        help="Output format.",
    )
    return parser.parse_args()


def expression_to_source(node: ast.AST | None) -> str | None:
    if node is None:
        return None
    unparse = getattr(ast, "unparse", None)
    if unparse is not None:
        try:
            return unparse(node)
        except Exception:
            pass
    return ast.dump(node, annotate_fields=False)


def literal_or_source(node: ast.AST | None) -> Any:
    if node is None:
        return None
    try:
        return ast.literal_eval(node)
    except Exception:
        return expression_to_source(node)


def keyword_map(call_node: ast.Call) -> dict[str, ast.AST | None]:
    result: dict[str, ast.AST | None] = {}
    for keyword in call_node.keywords:
        if keyword.arg is not None:
            result[keyword.arg] = keyword.value
    return result


def is_add_argument_call(node: ast.AST) -> bool:
    if not isinstance(node, ast.Call):
        return False
    function = node.func
    return isinstance(function, ast.Attribute) and function.attr == "add_argument"


def option_strings_from_call(call_node: ast.Call) -> list[str]:
    option_strings: list[str] = []
    for argument in call_node.args:
        try:
            value = ast.literal_eval(argument)
        except Exception:
            break
        if not isinstance(value, str):
            break
        option_strings.append(value)
    return option_strings


def derive_dest(option_strings: list[str], keywords: dict[str, ast.AST | None]) -> str | None:
    explicit_dest = literal_or_source(keywords.get("dest"))
    if isinstance(explicit_dest, str):
        return explicit_dest
    long_options = [option for option in option_strings if option.startswith("--")]
    if long_options:
        return long_options[0].lstrip("-").replace("-", "_")
    if option_strings:
        return option_strings[0].lstrip("-").replace("-", "_")
    return None


def extract_flag(call_node: ast.Call, source_path: Path) -> dict[str, Any] | None:
    option_strings = option_strings_from_call(call_node)
    if not option_strings:
        return None

    keywords = keyword_map(call_node)
    help_value = literal_or_source(keywords.get("help"))
    suppressed = help_value == "argparse.SUPPRESS"

    action_value = literal_or_source(keywords.get("action"))
    type_value = literal_or_source(keywords.get("type"))
    nargs_value = literal_or_source(keywords.get("nargs"))
    default_value = literal_or_source(keywords.get("default"))
    choices_value = literal_or_source(keywords.get("choices"))

    return {
        "option_strings": option_strings,
        "dest": derive_dest(option_strings, keywords),
        "action": action_value,
        "type": type_value,
        "nargs": nargs_value,
        "default": default_value,
        "choices": choices_value,
        "help": None if suppressed else help_value,
        "help_suppressed": suppressed,
        "line": getattr(call_node, "lineno", None),
        "source": str(source_path),
    }


def extract_flags(source_path: Path) -> list[dict[str, Any]]:
    source_text = source_path.read_text(encoding="utf-8")
    tree = ast.parse(source_text, filename=str(source_path))
    flags: list[dict[str, Any]] = []

    for node in ast.walk(tree):
        if not isinstance(node, ast.Call) or not is_add_argument_call(node):
            continue
        flag = extract_flag(node, source_path)
        if flag is not None:
            flags.append(flag)

    flags.sort(key=lambda item: (item.get("line") or 0, item.get("option_strings") or []))
    return flags


def markdown_escape(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (list, tuple)):
        text = ", ".join(str(item) for item in value)
    else:
        text = str(value)
    return text.replace("\n", " ").replace("|", "\\|")


def format_markdown(flags: list[dict[str, Any]], source_path: Path) -> str:
    lines = [
        f"# CLI Flags from `{source_path}`",
        "",
        f"Extracted {len(flags)} `parser.add_argument(...)` calls without importing WebUI.",
        "",
        "| Flags | Dest | Action / Type | Default | Choices | Help |",
        "| --- | --- | --- | --- | --- | --- |",
    ]
    for flag in flags:
        action_or_type = flag.get("action") or flag.get("type") or "value"
        if flag.get("nargs") is not None:
            action_or_type = f"{action_or_type}; nargs={flag['nargs']}"
        if flag.get("help_suppressed"):
            help_text = "argparse.SUPPRESS"
        else:
            help_text = flag.get("help")
        lines.append(
            "| {flags} | {dest} | {action} | {default} | {choices} | {help} |".format(
                flags=markdown_escape(", ".join(flag["option_strings"])),
                dest=markdown_escape(flag.get("dest")),
                action=markdown_escape(action_or_type),
                default=markdown_escape(flag.get("default")),
                choices=markdown_escape(flag.get("choices")),
                help=markdown_escape(help_text),
            )
        )
    return "\n".join(lines) + "\n"


def main() -> int:
    args = parse_args()
    source_path = Path(args.source)
    if not source_path.is_file():
        print(f"error: source file not found: {source_path}", file=sys.stderr)
        return 2

    try:
        flags = extract_flags(source_path)
    except SyntaxError as error:
        print(f"error: could not parse {source_path}: {error}", file=sys.stderr)
        return 2

    if args.format == "json":
        payload = {
            "source": str(source_path),
            "flag_count": len(flags),
            "flags": flags,
        }
        print(json.dumps(payload, indent=2, sort_keys=True))
    else:
        print(format_markdown(flags, source_path), end="")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
