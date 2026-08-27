#!/usr/bin/env python3
"""Classify an input for OWL DocumentProcessingToolkit without opening it."""
from __future__ import annotations

import argparse
import json
from pathlib import Path
from urllib.parse import urlparse

HANDLERS = {
    ".jpg": ("image-analysis", "vision-capable configured model"),
    ".jpeg": ("image-analysis", "vision-capable configured model"),
    ".png": ("image-analysis", "vision-capable configured model"),
    ".xls": ("excel-toolkit", "CAMEL ExcelToolkit dependencies"),
    ".xlsx": ("excel-toolkit", "CAMEL ExcelToolkit dependencies"),
    ".zip": ("archive-extraction", "isolated cache directory and unzip executable"),
    ".json": ("json-load", "one valid JSON document; not arbitrary JSONL records"),
    ".jsonl": ("json-load", "one valid JSON document; test multi-record JSONL separately"),
    ".jsonld": ("json-load", "one valid JSON document"),
    ".py": ("utf8-source-read", "read only; never execute extracted source"),
    ".xml": ("xmltodict-then-raw-text", "valid UTF-8 recommended"),
}


def classify(value: str) -> dict:
    parsed = urlparse(value)
    if parsed.scheme and parsed.netloc:
        return {
            "input": value,
            "kind": "url",
            "likely_handler": "webpage-detection then Firecrawl or Crawl4AI, otherwise UnstructuredIO",
            "prerequisites": ["network access", "public/authorized URL", "FIRECRAWL_API_KEY or Crawl4AI/browser setup"],
            "opens_input": False,
        }
    path = Path(value)
    suffix = path.suffix.lower()
    handler, prerequisite = HANDLERS.get(suffix, ("UnstructuredIO.parse_file_or_url", "supported parser dependencies"))
    return {
        "input": value,
        "kind": "local-file",
        "exists": path.is_file(),
        "suffix": suffix or None,
        "likely_handler": handler,
        "prerequisites": [prerequisite],
        "opens_input": False,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", required=True, help="local path or URL to classify")
    parser.add_argument("--json", action="store_true", help="emit JSON")
    args = parser.parse_args()
    result = classify(args.input)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        for key, value in result.items():
            print(f"{key}: {value}")
    return 0 if result.get("kind") == "url" or result.get("exists") else 1


if __name__ == "__main__":
    raise SystemExit(main())
