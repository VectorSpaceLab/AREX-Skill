#!/usr/bin/env python3
"""Summarize CCDS-style option and help JSON files.

This stdlib-only utility adapts the CCDS documentation option-table logic. It
reads a schema JSON such as ccds.json plus a help JSON such as ccds-help.json
and prints either Markdown or structured JSON. It does not import ccds,
cookiecutter, mkdocs, or project checkout code.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any


DEFAULT_SCHEMA = Path("ccds.json")
DEFAULT_HELP = Path("ccds-help.json")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize CCDS-compatible option schema/help JSON as Markdown or JSON. "
            "By default, reads ./ccds.json and ./ccds-help.json when present."
        )
    )
    parser.add_argument(
        "--schema",
        type=Path,
        default=None,
        help="Path to option schema JSON, for example ccds.json. Defaults to ./ccds.json.",
    )
    parser.add_argument(
        "--help-file",
        type=Path,
        default=None,
        help="Path to option help JSON, for example ccds-help.json. Defaults to ./ccds-help.json.",
    )
    parser.add_argument(
        "--format",
        choices=("markdown", "json"),
        default="markdown",
        help="Output format. Default: markdown.",
    )
    parser.add_argument(
        "--output",
        type=Path,
        default=None,
        help="Optional output path. Defaults to stdout.",
    )
    return parser.parse_args(argv)


def fail(message: str) -> None:
    print(f"error: {message}", file=sys.stderr)
    raise SystemExit(2)


def resolve_input_path(path: Path | None, default: Path, label: str) -> Path:
    chosen = path or default
    if not chosen.exists():
        if path is None:
            flag = "--help-file" if label == "help_file" else f"--{label.replace('_', '-')}"
            fail(f"{label} not found at default path {default!s}; pass {flag} explicitly")
        fail(f"{label} path does not exist: {chosen!s}")
    if not chosen.is_file():
        fail(f"{label} path is not a file: {chosen!s}")
    return chosen


def load_json(path: Path, expected_type: type, label: str) -> Any:
    try:
        with path.open("r", encoding="utf-8") as f:
            data = json.load(f)
    except json.JSONDecodeError as exc:
        fail(f"{label} is not valid JSON at {path!s}: line {exc.lineno}, column {exc.colno}: {exc.msg}")
    except OSError as exc:
        fail(f"could not read {label} at {path!s}: {exc}")
    if not isinstance(data, expected_type):
        fail(f"{label} must be a {expected_type.__name__}, got {type(data).__name__}")
    return data


def help_to_lookup(
    items: list[Any], prefix: str = "", out: dict[str, dict[str, str]] | None = None
) -> dict[str, dict[str, str]]:
    if out is None:
        out = {}
    for item in items:
        if not isinstance(item, dict):
            continue
        name = item.get("field", item.get("choice"))
        if not isinstance(name, str):
            continue
        key = name if not prefix else f"{prefix}.{name}"
        help_obj = item.get("help", {})
        out[key] = {
            "description": str(help_obj.get("description", "")) if isinstance(help_obj, dict) else "",
            "more_information": str(help_obj.get("more_information", "")) if isinstance(help_obj, dict) else "",
        }
        choices = item.get("choices")
        if isinstance(choices, list):
            help_to_lookup(choices, key, out)
        subfields = item.get("subfields")
        if isinstance(subfields, list):
            help_to_lookup(subfields, key, out)
    return out


def simplify_template_default(value: str) -> str:
    """Make a pure cookiecutter reference easier to scan while preserving value."""
    match = re.fullmatch(r"\{\{\s*cookiecutter\.([^{}]+?)\s*\}\}", value)
    if match:
        return match.group(1)
    return value


def choice_name_and_payload(choice: Any) -> tuple[str, Any]:
    if isinstance(choice, str):
        return choice, None
    if isinstance(choice, dict) and len(choice) == 1:
        name = next(iter(choice.keys()))
        return str(name), choice[name]
    return str(choice), None


def normalize_schema(schema: dict[str, Any], help_lookup: dict[str, dict[str, str]]) -> list[dict[str, Any]]:
    options: list[dict[str, Any]] = []
    for name, value in schema.items():
        base_help = help_lookup.get(name, {"description": "", "more_information": ""})
        option: dict[str, Any] = {
            "name": name,
            "description": base_help.get("description", ""),
            "more_information": base_help.get("more_information", ""),
        }
        if isinstance(value, str):
            option.update(
                {
                    "type": "string",
                    "default": value,
                    "default_display": simplify_template_default(value),
                    "choices": [],
                }
            )
        elif isinstance(value, list):
            default = "" if not value else choice_name_and_payload(value[0])[0]
            option.update({"type": "choice", "default": default, "choices": []})
            for choice in value:
                choice_name, payload = choice_name_and_payload(choice)
                choice_help = help_lookup.get(
                    f"{name}.{choice_name}", {"description": "", "more_information": ""}
                )
                choice_record: dict[str, Any] = {
                    "choice": choice_name,
                    "description": choice_help.get("description", ""),
                    "more_information": choice_help.get("more_information", ""),
                    "subfields": [],
                }
                if isinstance(payload, dict):
                    for sub_name, sub_default in payload.items():
                        sub_help = help_lookup.get(
                            f"{name}.{choice_name}.{sub_name}",
                            {"description": "", "more_information": ""},
                        )
                        choice_record["subfields"].append(
                            {
                                "name": str(sub_name),
                                "default": sub_default,
                                "description": sub_help.get("description", ""),
                                "more_information": sub_help.get("more_information", ""),
                            }
                        )
                elif isinstance(payload, list):
                    choice_record["nested_choices"] = [choice_name_and_payload(item)[0] for item in payload]
                elif payload is not None:
                    choice_record["value"] = payload
                option["choices"].append(choice_record)
        elif isinstance(value, dict):
            option.update({"type": "object", "default": value, "choices": []})
        else:
            option.update({"type": type(value).__name__, "default": value, "choices": []})
        options.append(option)
    return options


def escape_md(value: Any) -> str:
    text = "" if value is None else str(value)
    return text.replace("|", "\\|").replace("\n", " ")


def render_markdown(schema_path: Path, help_path: Path, options: list[dict[str, Any]]) -> str:
    lines = [
        "# CCDS Option Summary",
        "",
        f"Schema: `{escape_md(schema_path)}`",
        f"Help file: `{escape_md(help_path)}`",
        "",
    ]
    for option in options:
        lines.extend(
            [
                f"## {option['name'].replace('_', ' ').title()}",
                "",
                f"**Name:** `{option['name']}`",
                "",
                f"**Type:** `{option['type']}`",
                "",
            ]
        )
        if option["type"] == "string":
            default_value = option.get("default_display", option.get("default", ""))
        else:
            default_value = option.get("default", "")
        lines.extend([f"**Default:** `{escape_md(default_value)}`", ""])
        if option.get("description"):
            lines.extend([escape_md(option["description"]), ""])
        if option.get("more_information"):
            lines.extend([f"More information: {escape_md(option['more_information'])}", ""])
        if option.get("choices"):
            lines.extend(
                [
                    "| Choice | Sub-field | Default/value | Description | More information |",
                    "| --- | --- | --- | --- | --- |",
                ]
            )
            for choice in option["choices"]:
                lines.append(
                    "| {choice} |  | {value} | {description} | {more} |".format(
                        choice=escape_md(choice.get("choice", "")),
                        value=escape_md(choice.get("value", "")),
                        description=escape_md(choice.get("description", "")),
                        more=escape_md(choice.get("more_information", "")),
                    )
                )
                for subfield in choice.get("subfields", []):
                    lines.append(
                        "| {choice} | {sub} | {default} | {description} | {more} |".format(
                            choice=escape_md(choice.get("choice", "")),
                            sub=escape_md(subfield.get("name", "")),
                            default=escape_md(subfield.get("default", "")),
                            description=escape_md(subfield.get("description", "")),
                            more=escape_md(subfield.get("more_information", "")),
                        )
                    )
            lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def render_json(schema_path: Path, help_path: Path, options: list[dict[str, Any]]) -> str:
    payload = {
        "schema_path": str(schema_path),
        "help_file": str(help_path),
        "options": options,
    }
    return json.dumps(payload, indent=2, ensure_ascii=False) + "\n"


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    schema_path = resolve_input_path(args.schema, DEFAULT_SCHEMA, "schema")
    help_path = resolve_input_path(args.help_file, DEFAULT_HELP, "help_file")
    schema = load_json(schema_path, dict, "schema")
    help_data = load_json(help_path, list, "help_file")
    help_lookup = help_to_lookup(help_data)
    options = normalize_schema(schema, help_lookup)

    if args.format == "markdown":
        output = render_markdown(schema_path, help_path, options)
    else:
        output = render_json(schema_path, help_path, options)

    if args.output:
        try:
            args.output.parent.mkdir(parents=True, exist_ok=True)
            args.output.write_text(output, encoding="utf-8")
        except OSError as exc:
            fail(f"could not write output to {args.output!s}: {exc}")
    else:
        sys.stdout.write(output)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
