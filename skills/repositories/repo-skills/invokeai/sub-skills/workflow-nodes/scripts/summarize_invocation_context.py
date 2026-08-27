#!/usr/bin/env python3
"""Summarize InvokeAI InvocationContext JSON.

By default this reads the bundled distilled context summary next to the skill.
It can also summarize a generated invocation-context.json file supplied by the
user. The script has no InvokeAI import dependency.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

DEFAULT_CONTEXT_JSON = Path(__file__).resolve().parents[1] / "references" / "invocation-context-summary.json"


def load_context(path: Path) -> dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        data = json.load(handle)
    if not isinstance(data, dict):
        raise ValueError("context JSON root must be an object")
    if not isinstance(data.get("interfaces"), list):
        raise ValueError("context JSON must include an interfaces list")
    return data


def method_signature(method: dict[str, Any]) -> str:
    signature = method.get("signature")
    if isinstance(signature, str) and signature:
        return signature

    params = []
    for param in method.get("parameters", []) or []:
        if not isinstance(param, dict):
            continue
        name = param.get("name", "?")
        type_ = param.get("type", "Any")
        default = param.get("default")
        if default in (None, ""):
            params.append(f"{name}: {type_}")
        else:
            params.append(f"{name}: {type_} = {default}")
    return_type = method.get("return_type") or "Any"
    return f"({', '.join(params)}) -> {return_type}"


def normalize_interfaces(data: dict[str, Any]) -> list[dict[str, Any]]:
    interfaces = []
    for interface in data.get("interfaces", []):
        if not isinstance(interface, dict):
            continue
        methods = [method for method in interface.get("methods", []) if isinstance(method, dict)]
        interfaces.append(
            {
                "name": interface.get("name", "UnnamedInterface"),
                "description": interface.get("description", "") or "",
                "methods": sorted(
                    [
                        {
                            "name": method.get("name", "unnamed"),
                            "signature": method_signature(method),
                            "description": method.get("description", "") or method.get("returns", "") or "",
                        }
                        for method in methods
                    ],
                    key=lambda item: item["name"],
                ),
            }
        )
    return sorted(interfaces, key=lambda item: item["name"])


def filter_interfaces(interfaces: list[dict[str, Any]], interface_name: str | None) -> list[dict[str, Any]]:
    if not interface_name:
        return interfaces
    needle = interface_name.lower()
    return [interface for interface in interfaces if needle in interface["name"].lower()]


def render_text(data: dict[str, Any], interfaces: list[dict[str, Any]], show_descriptions: bool) -> str:
    lines: list[str] = []
    title = data.get("name") or "InvocationContext"
    lines.append(str(title))
    description = data.get("description")
    if description:
        lines.append(str(description).strip())
    lines.append("")

    if not interfaces:
        lines.append("No matching interfaces.")
        return "\n".join(lines)

    for interface in interfaces:
        methods = interface["methods"]
        lines.append(f"## {interface['name']} ({len(methods)} method{'s' if len(methods) != 1 else ''})")
        if show_descriptions and interface.get("description"):
            lines.append(str(interface["description"]).strip())
        for method in methods:
            lines.append(f"- {method['name']} {method['signature']}")
            if show_descriptions and method.get("description"):
                lines.append(f"  {str(method['description']).strip()}")
        lines.append("")

    return "\n".join(lines).rstrip()


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize InvokeAI InvocationContext interfaces from JSON.")
    parser.add_argument(
        "json_file",
        nargs="?",
        type=Path,
        default=DEFAULT_CONTEXT_JSON,
        help="Path to invocation-context JSON. Defaults to bundled distilled summary.",
    )
    parser.add_argument("--interface", help="Filter interfaces by case-insensitive name substring")
    parser.add_argument("--descriptions", action="store_true", help="Include interface and method descriptions")
    parser.add_argument("--json", action="store_true", help="Emit normalized summary as JSON")
    args = parser.parse_args(argv)

    try:
        data = load_context(args.json_file)
        interfaces = filter_interfaces(normalize_interfaces(data), args.interface)
    except Exception as exc:  # noqa: BLE001 - CLI should report all parse failures plainly.
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(
            json.dumps(
                {
                    "name": data.get("name", "InvocationContext"),
                    "description": data.get("description", ""),
                    "interfaces": interfaces,
                },
                indent=2,
            )
        )
    else:
        print(render_text(data, interfaces, args.descriptions))

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
