#!/usr/bin/env python3
"""Offline validation for RAGatouille persisted-index inputs.

This script intentionally does not import ragatouille, load models, download
checkpoints, or write index files. It mirrors the consistency checks that
RAGPretrainedModel applies before indexing documents with optional IDs and
metadata.
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from pathlib import Path
from typing import Any


MISSING = object()


def _load_json_arg(value: str | None, label: str, *, default: Any = MISSING) -> Any:
    if value is None:
        if default is MISSING:
            raise ValueError(f"{label} is required")
        return default

    candidate = Path(value)
    if candidate.exists():
        text = candidate.read_text(encoding="utf-8")
    else:
        text = value

    try:
        return json.loads(text)
    except json.JSONDecodeError as exc:
        raise ValueError(f"{label} must be valid JSON or a path to a JSON file: {exc}") from exc


def _type_name(value: Any) -> str:
    return type(value).__name__


def _find_duplicates(values: list[Any]) -> list[Any]:
    try:
        counts = Counter(values)
        return [value for value, count in counts.items() if count > 1]
    except TypeError:
        seen_serialized: dict[str, int] = {}
        values_by_key: dict[str, Any] = {}
        for value in values:
            key = json.dumps(value, sort_keys=True, default=repr)
            seen_serialized[key] = seen_serialized.get(key, 0) + 1
            values_by_key[key] = value
        return [values_by_key[key] for key, count in seen_serialized.items() if count > 1]


def validate_inputs(
    collection: Any,
    document_ids: Any = None,
    document_metadatas: Any = None,
    *,
    require_string_ids: bool = True,
) -> dict[str, Any]:
    errors: list[str] = []
    warnings: list[str] = []

    if not isinstance(collection, list):
        errors.append("collection must be a JSON list of document strings")
        collection_len = 0
    else:
        collection_len = len(collection)
        non_strings = [index for index, item in enumerate(collection) if not isinstance(item, str)]
        if non_strings:
            errors.append(
                "collection entries must be strings; non-string indexes: "
                + ", ".join(map(str, non_strings[:20]))
            )
        empty_docs = [index for index, item in enumerate(collection) if isinstance(item, str) and not item.strip()]
        if empty_docs:
            warnings.append(
                "collection contains empty or whitespace-only documents at indexes: "
                + ", ".join(map(str, empty_docs[:20]))
            )

    generated_ids = document_ids is None
    normalized_ids: list[Any] | None = None

    if document_ids is None:
        warnings.append("document_ids omitted; RAGatouille will generate UUID string ids")
    elif not isinstance(document_ids, list):
        errors.append("document_ids must be a JSON list when provided")
    else:
        normalized_ids = document_ids
        if len(document_ids) != collection_len:
            errors.append(
                f"document_ids length ({len(document_ids)}) must match collection length ({collection_len})"
            )

        duplicate_ids = _find_duplicates(document_ids)
        if duplicate_ids:
            preview = ", ".join(repr(value) for value in duplicate_ids[:10])
            errors.append(f"document_ids must be unique; duplicate values: {preview}")

        if document_ids:
            first_type = type(document_ids[0])
            mixed_indexes = [
                index
                for index, value in enumerate(document_ids)
                if not isinstance(value, first_type)
            ]
            if mixed_indexes:
                errors.append(
                    "all document_ids must share the same Python type; mixed-type indexes: "
                    + ", ".join(map(str, mixed_indexes[:20]))
                )

            if require_string_ids:
                non_string_indexes = [
                    index for index, value in enumerate(document_ids) if not isinstance(value, str)
                ]
                if non_string_indexes:
                    errors.append(
                        "document_ids should be strings for RAGatouille compatibility; non-string indexes: "
                        + ", ".join(map(str, non_string_indexes[:20]))
                    )

            empty_id_indexes: list[int] = []
            strip_incompatible_indexes: list[int] = []
            for index, value in enumerate(document_ids):
                if hasattr(value, "strip"):
                    if not value.strip():
                        empty_id_indexes.append(index)
                else:
                    strip_incompatible_indexes.append(index)
            if empty_id_indexes:
                errors.append(
                    "document_ids must not contain empty or whitespace-only strings; bad indexes: "
                    + ", ".join(map(str, empty_id_indexes[:20]))
                )
            if strip_incompatible_indexes and not require_string_ids:
                warnings.append(
                    "RAGatouille calls .strip() on ids; non-string ids may fail at runtime at indexes: "
                    + ", ".join(map(str, strip_incompatible_indexes[:20]))
                )

    if document_metadatas is None:
        metadata_keys: list[str] = []
    elif not isinstance(document_metadatas, list):
        errors.append("document_metadatas must be a JSON list of objects when provided")
        metadata_keys = []
    else:
        if len(document_metadatas) != collection_len:
            errors.append(
                f"document_metadatas length ({len(document_metadatas)}) must match collection length ({collection_len})"
            )
        non_dict_indexes = [
            index for index, metadata in enumerate(document_metadatas) if not isinstance(metadata, dict)
        ]
        if non_dict_indexes:
            errors.append(
                "document_metadatas entries must be objects/dicts; non-object indexes: "
                + ", ".join(map(str, non_dict_indexes[:20]))
            )
        metadata_keys = sorted(
            {
                str(key)
                for metadata in document_metadatas
                if isinstance(metadata, dict)
                for key in metadata.keys()
            }
        )

    id_type = None
    if normalized_ids:
        id_type = _type_name(normalized_ids[0])

    return {
        "ok": not errors,
        "errors": errors,
        "warnings": warnings,
        "summary": {
            "collection_length": collection_len,
            "document_ids_provided": not generated_ids,
            "document_id_type": id_type,
            "document_metadatas_provided": document_metadatas is not None,
            "metadata_keys": metadata_keys,
        },
    }


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate RAGatouille RAGPretrainedModel.index/add_to_index collection, "
            "document_ids, and document_metadatas consistency without importing RAGatouille."
        )
    )
    parser.add_argument(
        "--collection-json",
        required=True,
        help="JSON list of document strings, or a path to a JSON file containing that list.",
    )
    parser.add_argument(
        "--document-ids-json",
        help="Optional JSON list of document ids, or a path to a JSON file containing that list.",
    )
    parser.add_argument(
        "--document-metadatas-json",
        help="Optional JSON list of metadata objects, or a path to a JSON file containing that list.",
    )
    parser.add_argument(
        "--allow-non-string-ids",
        action="store_true",
        help=(
            "Downgrade the string-id compatibility check. RAGatouille 0.0.9post2 still calls "
            ".strip() on ids, so string ids are recommended."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON validation report instead of human-readable text.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        collection = _load_json_arg(args.collection_json, "collection")
        document_ids = _load_json_arg(args.document_ids_json, "document_ids", default=None)
        document_metadatas = _load_json_arg(
            args.document_metadatas_json,
            "document_metadatas",
            default=None,
        )
    except ValueError as exc:
        report = {"ok": False, "errors": [str(exc)], "warnings": [], "summary": {}}
        if args.json:
            print(json.dumps(report, indent=2, sort_keys=True))
        else:
            print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    report = validate_inputs(
        collection,
        document_ids,
        document_metadatas,
        require_string_ids=not args.allow_non_string_ids,
    )

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        status = "OK" if report["ok"] else "INVALID"
        print(f"RAGatouille index input validation: {status}")
        print(json.dumps(report["summary"], indent=2, sort_keys=True))
        for warning in report["warnings"]:
            print(f"WARNING: {warning}")
        for error in report["errors"]:
            print(f"ERROR: {error}")

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
