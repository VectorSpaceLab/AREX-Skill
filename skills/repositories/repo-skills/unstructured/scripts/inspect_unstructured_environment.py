#!/usr/bin/env python3
"""Print a safe Unstructured environment and capability summary."""

from __future__ import annotations

import argparse
import importlib.metadata as metadata
import importlib.util
import json
import platform
import shutil
import sys
from typing import Any


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def package_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def tool_path(name: str) -> bool:
    return shutil.which(name) is not None


def build_report() -> dict[str, Any]:
    optional_modules = {
        "magic": "MIME detection",
        "pypandoc": "Pandoc-backed formats",
        "pdf2image": "PDF page rendering",
        "pdfminer": "PDF text extraction",
        "unstructured_inference": "hi_res PDF/image layout inference",
        "unstructured_pytesseract": "OCR wrapper",
        "whisper": "audio transcription",
        "torch": "Hugging Face and object detection metrics",
        "pandas": "CSV/XLSX and metrics utilities",
        "openpyxl": "XLSX parsing",
        "docx": "DOCX parsing",
        "pptx": "PPTX parsing",
    }
    tools = {
        "tesseract": "OCR",
        "pdftoppm": "Poppler PDF rendering",
        "soffice": "LibreOffice legacy Office conversion",
        "pandoc": "Pandoc formats",
        "ffmpeg": "Audio decoding",
    }
    return {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "unstructured_version": package_version("unstructured"),
        "modules": {
            name: {"available": module_available(name), "purpose": purpose}
            for name, purpose in optional_modules.items()
        },
        "tools": {name: {"available": tool_path(name), "purpose": purpose} for name, purpose in tools.items()},
    }


def print_text(report: dict[str, Any]) -> None:
    print(f"Python: {report['python']}")
    print(f"Platform: {report['platform']}")
    print(f"unstructured: {report['unstructured_version'] or 'not installed'}")
    print("\nOptional Python modules:")
    for name, row in report["modules"].items():
        status = "ok" if row["available"] else "missing"
        print(f"  {name:26} {status:8} {row['purpose']}")
    print("\nSystem tools:")
    for name, row in report["tools"].items():
        status = "ok" if row["available"] else "missing"
        print(f"  {name:26} {status:8} {row['purpose']}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    args = parser.parse_args()
    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
