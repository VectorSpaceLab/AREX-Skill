#!/usr/bin/env python3
"""Offline builder and validator for R2R document-ingestion payloads."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Any

REQUIRED_ONE_OF = ("file_path", "raw_text", "chunks", "s3_url")


def _load_json(value: str | None) -> Any:
    if value is None:
        return None
    if value.startswith("@"):
        return json.loads(Path(value[1:]).read_text())
    return json.loads(value)


def _validate(payload: dict[str, Any]) -> list[str]:
    errors: list[str] = []
    if not any(payload.get(key) not in (None, "", [], {}) for key in REQUIRED_ONE_OF):
        errors.append("one of file_path/raw_text/chunks/s3_url is required")
    if payload.get("chunks") is not None and not isinstance(payload["chunks"], list):
        errors.append("chunks must be a list of strings")
    if payload.get("metadata") is not None and not isinstance(payload["metadata"], dict):
        errors.append("metadata must be a dictionary")
    if payload.get("collection_ids") is not None and not isinstance(payload["collection_ids"], list):
        errors.append("collection_ids must be a list")
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Build and validate R2R documents.create payloads without contacting a server.",
    )
    parser.add_argument(
        "--payload-json",
        help="JSON string or @path to a JSON file containing documents.create fields.",
    )
    parser.add_argument(
        "--curl",
        action="store_true",
        help="Print an example curl command after validation.",
    )
    args = parser.parse_args()

    if not args.payload_json:
        parser.error("--payload-json is required")

    payload = _load_json(args.payload_json)
    if not isinstance(payload, dict):
        raise SystemExit("payload must decode to a JSON object")

    errors = _validate(payload)
    if errors:
        for error in errors:
            print(f"ERROR: {error}")
        return 1

    print(json.dumps(payload, indent=2, sort_keys=True))
    if args.curl:
        print()
        print("curl -X POST http://localhost:7272/v3/documents \\")
        print("  -H 'Content-Type: application/json' \\")
        print("  -d @payload.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
