#!/usr/bin/env python3
"""Offline RAGFlow parser routing/config smoke check.

This helper validates file-extension routing, output-format compatibility,
PDF backend names, backend-specific parser_config keys, and optional parser
imports. It does not open documents, start services, call networks, download
models, or mutate data.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import sys
from pathlib import Path
from typing import Any

FAMILIES: dict[str, dict[str, Any]] = {
    "pdf": {
        "suffixes": ["pdf"],
        "outputs": ["json", "markdown"],
        "default_output": "json",
        "default_parse_method": "deepdoc",
    },
    "spreadsheet": {
        "suffixes": ["xls", "xlsx", "csv"],
        "outputs": ["json", "markdown", "html"],
        "default_output": "html",
        "default_parse_method": "deepdoc",
    },
    "doc": {
        "suffixes": ["doc"],
        "outputs": ["json", "markdown"],
        "default_output": "json",
    },
    "docx": {
        "suffixes": ["docx"],
        "outputs": ["json", "markdown"],
        "default_output": "json",
    },
    "slides": {
        "suffixes": ["ppt", "pptx"],
        "outputs": ["json"],
        "default_output": "json",
        "default_parse_method": "deepdoc",
    },
    "image": {
        "suffixes": ["jpg", "jpeg", "png", "gif"],
        "outputs": ["json"],
        "default_output": "json",
        "default_parse_method": "ocr",
    },
    "markdown": {
        "suffixes": ["md", "markdown", "mdx"],
        "outputs": ["text", "json"],
        "default_output": "json",
    },
    "text&code": {
        "suffixes": ["txt", "py", "js", "java", "c", "cpp", "h", "php", "go", "ts", "sh", "cs", "kt", "sql"],
        "outputs": ["text", "json"],
        "default_output": "json",
    },
    "html": {
        "suffixes": ["htm", "html"],
        "outputs": ["text", "json"],
        "default_output": "json",
    },
    "email": {
        "suffixes": ["eml", "msg"],
        "outputs": ["text", "json"],
        "default_output": "json",
    },
    "audio": {
        "suffixes": ["da", "wave", "wav", "mp3", "aac", "flac", "ogg", "aiff", "au", "midi", "wma", "realaudio", "vqf", "oggvorbis", "ape"],
        "outputs": ["text", "json"],
        "default_output": "text",
    },
    "video": {
        "suffixes": ["mp4", "avi", "mkv"],
        "outputs": ["text"],
        "default_output": "text",
    },
    "epub": {
        "suffixes": ["epub"],
        "outputs": ["text", "json"],
        "default_output": "json",
    },
}

PDF_BACKENDS = {
    "deepdoc",
    "plain_text",
    "mineru",
    "docling",
    "opendataloader",
    "tcadp parser",
    "paddleocr",
}

KNOWN_FAMILY_KEYS: dict[str, set[str]] = {
    "pdf": {
        "parse_method",
        "lang",
        "flatten_media_to_text",
        "remove_toc",
        "remove_header_footer",
        "enable_multi_column",
        "output_format",
        "mineru_llm_name",
        "mineru_lang",
        "mineru_parse_method",
        "mineru_formula_enable",
        "mineru_table_enable",
        "opendataloader_llm_name",
        "paddleocr_llm_name",
        "table_result_type",
        "markdown_image_response_type",
        "vlm",
    },
    "spreadsheet": {
        "parse_method",
        "flatten_media_to_text",
        "output_format",
        "table_result_type",
        "markdown_image_response_type",
    },
    "doc": {"remove_toc", "remove_header_footer", "output_format"},
    "docx": {"flatten_media_to_text", "remove_toc", "remove_header_footer", "output_format", "vlm"},
    "slides": {"parse_method", "output_format", "table_result_type", "markdown_image_response_type"},
    "image": {"parse_method", "llm_id", "lang", "system_prompt", "output_format"},
    "markdown": {"flatten_media_to_text", "delimiter", "remove_toc", "output_format", "vlm"},
    "text&code": {"chunk_token_num", "delimiter", "output_format"},
    "html": {"remove_toc", "remove_header_footer", "chunk_token_num", "output_format"},
    "email": {"fields", "output_format"},
    "audio": {"vlm", "output_format"},
    "video": {"vlm", "prompt", "output_format"},
    "epub": {"output_format"},
}

OPTIONAL_IMPORTS = {
    "beartype": "beartype",
    "pdfplumber": "pdfplumber",
    "pypdf": "pypdf",
    "PIL": "Pillow",
    "numpy": "numpy",
    "xgboost": "xgboost",
    "docx": "python-docx",
    "openpyxl": "openpyxl",
    "pandas": "pandas",
    "bs4": "beautifulsoup4",
    "markdown": "markdown",
    "ebooklib": "ebooklib",
    "pptx": "python-pptx",
    "tika": "tika",
    "requests": "requests",
    "tencentcloud": "tencentcloud-sdk-python",
    "docling": "docling",
}

PUBLIC_KEY_HINTS = {
    "layout_recognize": "This is commonly a dataset/chunking key. Convert it to the PDF setup parse_method before expecting flow parser behavior.",
    "html4excel": "This is commonly a dataset/chunking key. It should drive spreadsheet HTML behavior in ingestion config, not every parser branch directly.",
    "chunk_method": "This is a dataset/document public API key. Parser routing uses file suffix plus internal parser setup.",
    "parser_id": "This is an internal dataset/document chunk method key. Parser routing still depends on file suffix and parser setup.",
}


def load_config(raw: str | None) -> dict[str, Any]:
    if not raw:
        return {}

    candidate = Path(raw)
    if candidate.exists():
        try:
            return json.loads(candidate.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            raise SystemExit(f"Invalid JSON in {candidate}: {exc}") from exc

    try:
        loaded = json.loads(raw)
    except json.JSONDecodeError as exc:
        raise SystemExit(f"--config must be JSON text or an existing JSON file: {exc}") from exc
    if not isinstance(loaded, dict):
        raise SystemExit("--config must decode to a JSON object")
    return loaded


def normalize_extension(value: str) -> str:
    ext = value.strip().lower()
    if not ext:
        raise SystemExit("extension cannot be empty")
    if "." in ext:
        ext = Path(ext).suffix.lower().lstrip(".") or ext.lstrip(".")
    return ext.lstrip(".")


def family_for_extension(ext: str) -> str | None:
    for family, spec in FAMILIES.items():
        if ext in spec["suffixes"]:
            return family
    return None


def selected_family_config(config: dict[str, Any], family: str) -> dict[str, Any]:
    family_config = config.get(family)
    if isinstance(family_config, dict):
        return family_config
    return config


def selected_output_format(family_config: dict[str, Any], family: str) -> str:
    value = family_config.get("output_format", FAMILIES[family]["default_output"])
    return str(value).lower()


def selected_parse_method(family_config: dict[str, Any], family: str) -> str | None:
    default = FAMILIES[family].get("default_parse_method")
    value = family_config.get("parse_method", default)
    if value is None:
        return None
    value = str(value)
    lowered = value.lower()
    if lowered.endswith("@mineru"):
        return "mineru"
    if lowered.endswith("@paddleocr"):
        return "paddleocr"
    return lowered


def warn_unknown_keys(config: dict[str, Any], family: str, family_config: dict[str, Any]) -> list[str]:
    warnings: list[str] = []
    nested = isinstance(config.get(family), dict)
    keys_to_check = set(family_config)
    known = KNOWN_FAMILY_KEYS.get(family, set())

    if nested:
        unknown = sorted(keys_to_check - known)
        for key in unknown:
            warnings.append(f"Unknown key for {family} setup: {key}")
    else:
        family_names = set(FAMILIES)
        for key in sorted(keys_to_check):
            if key in family_names:
                continue
            if key in PUBLIC_KEY_HINTS:
                warnings.append(f"Public/config-boundary key {key}: {PUBLIC_KEY_HINTS[key]}")
            elif key not in known:
                warnings.append(f"Unknown key for {family} setup: {key}")
    return warnings


def check_imports() -> dict[str, str]:
    results: dict[str, str] = {}
    for module, package_hint in OPTIONAL_IMPORTS.items():
        spec = importlib.util.find_spec(module)
        results[module] = "available" if spec else f"missing ({package_hint})"
    return results


def print_kv(label: str, value: Any) -> None:
    print(f"{label}: {value}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Offline parser extension/config smoke check for RAGFlow skills.")
    parser.add_argument("--extension", "-e", required=True, help="File extension or filename to route, such as pdf, sample.xlsx, or .md")
    parser.add_argument("--config", "-c", help="Parser setup JSON object or path to JSON file")
    parser.add_argument("--check-imports", action="store_true", help="Also report optional parser dependency import availability")
    parser.add_argument("--strict", action="store_true", help="Exit non-zero on warnings as well as errors")
    args = parser.parse_args(argv)

    ext = normalize_extension(args.extension)
    config = load_config(args.config)
    family = family_for_extension(ext)

    errors: list[str] = []
    warnings: list[str] = []

    print_kv("extension", ext)
    if not family:
        errors.append(f"No parser family is configured for extension .{ext}")
    else:
        family_config = selected_family_config(config, family)
        output_format = selected_output_format(family_config, family)
        parse_method = selected_parse_method(family_config, family)

        print_kv("family", family)
        print_kv("output_format", output_format)
        if parse_method:
            print_kv("parse_method", parse_method)

        allowed_outputs = FAMILIES[family]["outputs"]
        if output_format not in allowed_outputs:
            errors.append(f"output_format '{output_format}' is not allowed for {family}; allowed: {', '.join(allowed_outputs)}")

        if family == "pdf" and parse_method:
            if parse_method not in PDF_BACKENDS:
                warnings.append(
                    "PDF parse_method is not one of the built-in backends; it may be a configured VLM/provider model id. "
                    f"Built-ins: {', '.join(sorted(PDF_BACKENDS))}"
                )
            if parse_method == "mineru":
                method = str(family_config.get("mineru_parse_method", "auto"))
                if method not in {"auto", "txt", "ocr"}:
                    errors.append("mineru_parse_method must be one of: auto, txt, ocr")
            if parse_method == "paddleocr":
                algorithm = family_config.get("algorithm") or family_config.get("paddleocr_algorithm")
                if algorithm and algorithm not in {"PaddleOCR-VL", "PaddleOCR-VL-1.6", "PaddleOCR-VL-1.5", "PP-OCRv5", "PP-OCRv6", "PP-StructureV3"}:
                    warnings.append(f"PaddleOCR algorithm '{algorithm}' is not in the known supported set")

        if family in {"spreadsheet", "slides"} and parse_method and parse_method not in {"deepdoc", "tcadp parser"}:
            warnings.append(f"{family} parse_method '{parse_method}' is unusual; common values are deepdoc and tcadp parser")

        warnings.extend(warn_unknown_keys(config, family, family_config))

    if args.check_imports:
        print("optional_imports:")
        for module, status in check_imports().items():
            print(f"  {module}: {status}")

    if warnings:
        print("warnings:")
        for item in warnings:
            print(f"  - {item}")

    if errors:
        print("errors:")
        for item in errors:
            print(f"  - {item}")
        return 2

    if args.strict and warnings:
        return 1

    print("status: ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
