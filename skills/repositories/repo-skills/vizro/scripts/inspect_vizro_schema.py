#!/usr/bin/env python3
"""Summarize public Vizro model fields from the installed package.

Useful when writing or debugging dashboards without opening the source tree.
"""

from __future__ import annotations

import argparse
import inspect
from typing import Any

import vizro.models as vm

DEFAULT_MODELS = [
    "Dashboard",
    "Page",
    "Card",
    "Graph",
    "Table",
    "AgGrid",
    "Button",
    "Filter",
    "Parameter",
    "Slider",
    "RangeSlider",
    "Checklist",
    "Dropdown",
    "Tabs",
    "Container",
    "Tooltip",
]


def annotation_to_str(value: Any) -> str:
    try:
        return value.__name__
    except AttributeError:
        return str(value).replace("typing.", "")


def summarize_model(name: str) -> str:
    cls = getattr(vm, name, None)
    if cls is None:
        return f"## {name}\n\nMISSING from vizro.models\n"

    lines = [f"## {name}", ""]
    doc = inspect.getdoc(cls)
    if doc:
        first = doc.strip().splitlines()[0]
        lines.append(first)
        lines.append("")

    fields = getattr(cls, "model_fields", None)
    if not fields:
        sig = inspect.signature(cls)
        lines.append(f"Signature: `{sig}`")
        return "\n".join(lines) + "\n"

    lines.append("| Field | Type | Required | Default |")
    lines.append("| --- | --- | --- | --- |")
    for field_name, field in fields.items():
        required = "yes" if field.is_required() else "no"
        default = "<required>" if field.is_required() else repr(field.default)
        if len(default) > 80:
            default = default[:77] + "..."
        lines.append(f"| `{field_name}` | `{annotation_to_str(field.annotation)}` | {required} | `{default}` |")
    return "\n".join(lines) + "\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--models", nargs="*", default=DEFAULT_MODELS, help="Model class names from vizro.models")
    args = parser.parse_args()

    print("# Vizro model field summary\n")
    for model_name in args.models:
        print(summarize_model(model_name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
