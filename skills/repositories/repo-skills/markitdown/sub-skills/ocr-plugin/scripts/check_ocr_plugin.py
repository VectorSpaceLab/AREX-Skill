#!/usr/bin/env python3
"""Safely inspect markitdown-ocr import, entry point, and converter wiring.

This script does not convert user files and never calls an LLM. Real OCR
requires MarkItDown with plugins enabled plus an OpenAI-compatible vision client
and model supplied by the user.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import sys
from dataclasses import dataclass
from io import BytesIO
from typing import Any


PLUGIN_GROUP = "markitdown.plugin"
PLUGIN_NAME = "ocr"
PLUGIN_MODULE = "markitdown_ocr"
FORMAT_TO_CONVERTER = {
    "pdf": "PdfConverterWithOCR",
    "docx": "DocxConverterWithOCR",
    "pptx": "PptxConverterWithOCR",
    "xlsx": "XlsxConverterWithOCR",
}
FORMAT_TO_EXTENSION = {
    "pdf": ".pdf",
    "docx": ".docx",
    "pptx": ".pptx",
    "xlsx": ".xlsx",
}


@dataclass
class CheckResult:
    ok: bool
    message: str


def _print_result(result: CheckResult) -> None:
    prefix = "OK" if result.ok else "ERROR"
    print(f"[{prefix}] {result.message}")


def _find_ocr_entry_point() -> metadata.EntryPoint | None:
    entry_points = metadata.entry_points()
    if hasattr(entry_points, "select"):
        matches = entry_points.select(group=PLUGIN_GROUP, name=PLUGIN_NAME)
    else:  # pragma: no cover - compatibility with old importlib.metadata
        matches = [
            ep
            for ep in entry_points.get(PLUGIN_GROUP, [])
            if ep.name == PLUGIN_NAME
        ]
    for entry_point in matches:
        return entry_point
    return None


def _check_distribution() -> CheckResult:
    try:
        version = metadata.version("markitdown-ocr")
    except metadata.PackageNotFoundError:
        return CheckResult(False, "distribution 'markitdown-ocr' is not installed")
    return CheckResult(True, f"distribution 'markitdown-ocr' version {version} is installed")


def _check_import() -> tuple[CheckResult, Any | None]:
    try:
        module = importlib.import_module(PLUGIN_MODULE)
    except Exception as exc:
        return CheckResult(False, f"could not import {PLUGIN_MODULE}: {exc}"), None

    required_names = [
        "register_converters",
        "LLMVisionOCRService",
        "PdfConverterWithOCR",
        "DocxConverterWithOCR",
        "PptxConverterWithOCR",
        "XlsxConverterWithOCR",
    ]
    missing = [name for name in required_names if not hasattr(module, name)]
    if missing:
        return CheckResult(False, f"{PLUGIN_MODULE} is missing exports: {', '.join(missing)}"), module

    interface_version = getattr(module, "__plugin_interface_version__", None)
    version = getattr(module, "__version__", "unknown")
    return (
        CheckResult(
            True,
            f"imported {PLUGIN_MODULE} version {version}; plugin interface {interface_version}",
        ),
        module,
    )


def _check_entry_point(require_entry_point: bool) -> CheckResult:
    entry_point = _find_ocr_entry_point()
    if entry_point is None:
        message = f"entry point {PLUGIN_GROUP}:{PLUGIN_NAME} was not found"
        if require_entry_point:
            return CheckResult(False, message)
        return CheckResult(True, f"{message}; continuing because it was not required")

    value = entry_point.value
    if value != PLUGIN_MODULE:
        return CheckResult(False, f"entry point {PLUGIN_NAME} points to {value!r}, expected {PLUGIN_MODULE!r}")

    return CheckResult(True, f"entry point discovered: {PLUGIN_NAME} = {value}")


def _check_client_module(client_module: str | None) -> CheckResult:
    if not client_module:
        return CheckResult(True, "no client module requested; no LLM client import attempted")
    try:
        importlib.import_module(client_module)
    except Exception as exc:
        return CheckResult(False, f"could not import client module {client_module!r}: {exc}")
    return CheckResult(True, f"client module {client_module!r} imports; no client was instantiated")


def _check_converter(module: Any, selected_format: str) -> CheckResult:
    try:
        from markitdown import StreamInfo
    except Exception as exc:
        return CheckResult(False, f"could not import markitdown.StreamInfo: {exc}")

    converter_name = FORMAT_TO_CONVERTER[selected_format]
    extension = FORMAT_TO_EXTENSION[selected_format]
    try:
        converter_class = getattr(module, converter_name)
        converter = converter_class(ocr_service=None)
        accepted = converter.accepts(BytesIO(b""), StreamInfo(extension=extension))
    except Exception as exc:
        return CheckResult(False, f"{converter_name} safe instantiation/acceptance failed: {exc}")

    if not accepted:
        return CheckResult(False, f"{converter_name} did not accept extension {extension}")

    return CheckResult(
        True,
        f"{converter_name} accepts {extension} without an OCR service; no conversion or LLM call was made",
    )


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Safely check markitdown-ocr import, plugin entry point, and converter "
            "wiring. This script never calls an LLM; real OCR requires an "
            "OpenAI-compatible vision client passed to MarkItDown."
        )
    )
    parser.add_argument(
        "--require-entry-point",
        action="store_true",
        help="fail if the markitdown.plugin entry point 'ocr' is not installed",
    )
    parser.add_argument(
        "--model",
        help="model name to report as intended real-OCR configuration; no API call is made",
    )
    parser.add_argument(
        "--client-module",
        help="optional client package/module to import-check, such as 'openai'; no client is instantiated",
    )
    parser.add_argument(
        "--format",
        choices=sorted(FORMAT_TO_CONVERTER),
        default="pdf",
        help="converter format to instantiate safely without OCR service",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    print("markitdown-ocr safe diagnostic")
    print("No document conversion or LLM/API call will be attempted.")
    if args.model:
        print(f"Requested model label for future real OCR: {args.model}")
    else:
        print("No model label supplied; real OCR would still require llm_model.")

    results: list[CheckResult] = []

    dist_result = _check_distribution()
    results.append(dist_result)

    import_result, module = _check_import()
    results.append(import_result)

    results.append(_check_entry_point(args.require_entry_point))
    results.append(_check_client_module(args.client_module))

    if module is not None:
        results.append(_check_converter(module, args.format))

    for result in results:
        _print_result(result)

    if all(result.ok for result in results):
        print(
            "Real conversion requires MarkItDown(enable_plugins=True, "
            "llm_client=<OpenAI-compatible vision client>, llm_model=<vision model>)."
        )
        return 0

    return 1


if __name__ == "__main__":
    raise SystemExit(main())
