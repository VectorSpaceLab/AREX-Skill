#!/usr/bin/env python3
"""Inspect PaperQA parser imports and signatures without requiring optional readers.

This script is intentionally safe: it imports modules if present and reports
missing optional parser packages instead of failing the whole run. It does not
parse PDFs, call LLMs, contact network services, or require any project checkout.
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import json
import sys
from importlib import metadata
from typing import Any

MODULES: dict[str, dict[str, Any]] = {
    "paperqa.readers": {
        "distribution": "paper-qa",
        "required": True,
        "symbols": [
            "read_doc",
            "parse_text",
            "parse_image",
            "parse_office_doc",
            "chunk_text",
            "chunk_pdf",
            "chunk_code_text",
            "resolve_page_range",
        ],
    },
    "paperqa.settings": {
        "distribution": "paper-qa",
        "required": True,
        "symbols": ["ParsingSettings", "MultimodalOptions", "get_default_pdf_parser"],
    },
    "paperqa_pypdf": {
        "distribution": "paper-qa-pypdf",
        "required": False,
        "symbols": ["parse_pdf_to_pages"],
    },
    "paperqa_pymupdf": {
        "distribution": "paper-qa-pymupdf",
        "required": False,
        "symbols": ["parse_pdf_to_pages", "setup_pymupdf_python_logging"],
    },
    "paperqa_docling": {
        "distribution": "paper-qa-docling",
        "required": False,
        "symbols": ["parse_pdf_to_pages"],
    },
    "paperqa_nemotron": {
        "distribution": "paper-qa-nemotron",
        "required": False,
        "symbols": ["parse_pdf_to_pages"],
    },
}

EXTRA_MODULES = {
    "pypdf": "pypdf text extraction",
    "pypdfium2": "pypdf/Nemotron rasterization and full-page media",
    "PIL": "Pillow image conversion",
    "pdfplumber": "pypdf enhanced table and figure clustering",
    "pymupdf": "PyMuPDF reader backend",
    "docling": "Docling reader backend",
    "unstructured": "Office document parsing",
    "litellm": "Nemotron NVIDIA API calls and enrichment models",
    "aiobotocore": "Nemotron SageMaker extra",
}


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def signature_of(obj: Any) -> str | None:
    try:
        signature = str(inspect.signature(obj))
    except (TypeError, ValueError):
        return None
    max_len = 600
    if len(signature) > max_len:
        return signature[:max_len] + "...<truncated>"
    return signature


def inspect_module(module_name: str, spec: dict[str, Any]) -> dict[str, Any]:
    record: dict[str, Any] = {
        "module": module_name,
        "required": bool(spec["required"]),
        "distribution": spec["distribution"],
        "distribution_version": dist_version(spec["distribution"]),
        "available": False,
        "symbols": {},
    }
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001 - report import failures, do not hide them
        record["error"] = f"{type(exc).__name__}: {exc}"
        return record

    record["available"] = True
    for symbol in spec["symbols"]:
        symbol_record: dict[str, Any] = {"available": hasattr(module, symbol)}
        if hasattr(module, symbol):
            obj = getattr(module, symbol)
            symbol_record["signature"] = signature_of(obj)
            symbol_record["kind"] = type(obj).__name__
        record["symbols"][symbol] = symbol_record
    return record


def inspect_extra(module_name: str, purpose: str) -> dict[str, Any]:
    record = {"module": module_name, "purpose": purpose, "available": False}
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:  # noqa: BLE001
        record["error"] = f"{type(exc).__name__}: {exc}"
        return record
    record["available"] = True
    for attr in ("__version__", "PYPDFIUM_INFO"):
        if hasattr(module, attr):
            record[attr] = str(getattr(module, attr))
    return record


def inspect_default_parser() -> dict[str, Any]:
    try:
        from paperqa.settings import ParsingSettings, get_default_pdf_parser
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    try:
        parser = get_default_pdf_parser()
        settings = ParsingSettings()
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "available": True,
        "default_parser": f"{getattr(parser, '__module__', type(parser).__module__)}.{getattr(parser, '__name__', type(parser).__name__)}",
        "default_parser_signature": signature_of(parser),
        "reader_config": settings.reader_config,
        "page_size_limit": settings.page_size_limit,
        "multimodal": str(settings.multimodal),
        "should_parse_and_enrich_media": settings.should_parse_and_enrich_media,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--json-only",
        action="store_true",
        help="Print compact JSON only, without a human summary.",
    )
    args = parser.parse_args()

    result = {
        "python": sys.version.split()[0],
        "modules": {name: inspect_module(name, spec) for name, spec in MODULES.items()},
        "extras": {name: inspect_extra(name, purpose) for name, purpose in EXTRA_MODULES.items()},
        "default_pdf_parser": inspect_default_parser(),
    }

    if not args.json_only:
        print("PaperQA parser inventory")
        for name, record in result["modules"].items():
            status = "ok" if record["available"] else "missing"
            req = "required" if record["required"] else "optional"
            version = record.get("distribution_version") or "not installed"
            print(f"- {name}: {status} ({req}, {record['distribution']} {version})")
            if record.get("error"):
                print(f"  error: {record['error']}")
            for sym, sym_record in record.get("symbols", {}).items():
                if sym_record.get("available"):
                    sig = sym_record.get("signature") or "<no signature>"
                    print(f"  {sym}{sig}")
        print("- default parser:", result["default_pdf_parser"])
        print()

    print(json.dumps(result, indent=None if args.json_only else 2, sort_keys=True))

    required_missing = [
        name
        for name, record in result["modules"].items()
        if record["required"] and not record["available"]
    ]
    return 2 if required_missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
