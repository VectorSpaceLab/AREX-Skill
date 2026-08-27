#!/usr/bin/env python3
"""Print Docling pipeline option fields and defaults for the installed package.

This helper is intentionally read-only. It imports selected Docling option
classes, prints Pydantic fields/defaults when available, and exits cleanly when
optional classes or dependencies are unavailable.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from enum import Enum
from typing import Any

CLASS_LOCATIONS = {
    "AcceleratorOptions": "docling.datamodel.accelerator_options",
    "PdfPipelineOptions": "docling.datamodel.pipeline_options",
    "ThreadedPdfPipelineOptions": "docling.datamodel.pipeline_options",
    "TableStructureOptions": "docling.datamodel.pipeline_options",
    "TableStructureV2Options": "docling.datamodel.pipeline_options",
    "EasyOcrOptions": "docling.datamodel.pipeline_options",
    "RapidOcrOptions": "docling.datamodel.pipeline_options",
    "TesseractCliOcrOptions": "docling.datamodel.pipeline_options",
    "TesseractOcrOptions": "docling.datamodel.pipeline_options",
    "OcrMacOptions": "docling.datamodel.pipeline_options",
    "KserveV2OcrOptions": "docling.datamodel.pipeline_options",
}

DEFAULT_CLASSES = [
    "PdfPipelineOptions",
    "ThreadedPdfPipelineOptions",
    "TableStructureOptions",
    "EasyOcrOptions",
    "RapidOcrOptions",
    "TesseractCliOcrOptions",
    "TesseractOcrOptions",
    "OcrMacOptions",
    "AcceleratorOptions",
]


def safe_repr(value: Any) -> str:
    if value is None or isinstance(value, (str, int, float, bool)):
        return repr(value)
    if isinstance(value, Enum):
        return f"{value.__class__.__name__}.{value.name}"
    if isinstance(value, (list, tuple, set)):
        return repr(list(value))
    if isinstance(value, dict):
        try:
            return json.dumps(value, sort_keys=True)
        except TypeError:
            return repr(value)
    return repr(value)


def field_default(field: Any) -> str:
    default = getattr(field, "default", None)
    default_factory = getattr(field, "default_factory", None)
    if default_factory is not None:
        return f"<factory {getattr(default_factory, '__name__', default_factory)}>"
    if str(default) == "PydanticUndefined":
        return "<required>"
    return safe_repr(default)


def field_annotation(field: Any) -> str:
    annotation = getattr(field, "annotation", None)
    if annotation is None:
        return "<unknown>"
    text = getattr(annotation, "__name__", None)
    return text or str(annotation).replace("typing.", "")


def load_class(class_name: str) -> tuple[type[Any] | None, str | None]:
    module_name = CLASS_LOCATIONS.get(class_name)
    if module_name is None:
        return None, f"unknown class {class_name!r}; known: {', '.join(sorted(CLASS_LOCATIONS))}"
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report optional import failures cleanly.
        return None, f"could not import {module_name}: {exc.__class__.__name__}: {exc}"
    try:
        return getattr(module, class_name), None
    except AttributeError:
        return None, f"{module_name} has no class {class_name}"


def inspect_class(class_name: str) -> int:
    option_class, error = load_class(class_name)
    print(f"\n## {class_name}")
    if error is not None or option_class is None:
        print(f"ERROR: {error}")
        return 1

    fields = getattr(option_class, "model_fields", None)
    if not fields:
        print("No Pydantic model_fields found.")
        return 0

    for field_name, field in fields.items():
        print(f"- {field_name}")
        print(f"  annotation: {field_annotation(field)}")
        print(f"  default: {field_default(field)}")
        description = getattr(field, "description", None)
        if description:
            print(f"  description: {description}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--classes",
        nargs="+",
        default=DEFAULT_CLASSES,
        help="Option class names to inspect.",
    )
    args = parser.parse_args()

    failures = 0
    for class_name in args.classes:
        failures += inspect_class(class_name)
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
