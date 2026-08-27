#!/usr/bin/env python3
"""Inspect a GraphRAG config and print a redacted JSON summary."""

from __future__ import annotations

import argparse
import json
import sys
from collections.abc import Mapping
from pathlib import Path
from typing import Any

SECRET_HINTS = (
    "api_key",
    "key",
    "secret",
    "token",
    "credential",
    "connection_string",
    "password",
)


def is_secret_key(key: str) -> bool:
    lowered = key.lower()
    return any(hint in lowered for hint in SECRET_HINTS)


def redact(value: Any, key: str = "") -> Any:
    if is_secret_key(key) and value not in (None, ""):
        return "<redacted>"
    if isinstance(value, Mapping):
        return {str(k): redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(item, key) for item in value]
    return value


def enum_value(value: Any) -> Any:
    return getattr(value, "value", value)


def model_to_dict(model: Any) -> dict[str, Any]:
    if model is None:
        return {}
    if hasattr(model, "model_dump"):
        return model.model_dump(mode="json")
    if isinstance(model, Mapping):
        return dict(model)
    return {}


def summarize_model(model: Any) -> dict[str, Any]:
    data = model_to_dict(model)
    keys = [
        "type",
        "model_provider",
        "model",
        "auth_method",
        "api_base",
        "api_version",
        "azure_deployment_name",
        "organization",
        "audience",
    ]
    summary = {key: data.get(key) for key in keys if key in data and data.get(key) is not None}
    if "api_key" in data:
        summary["api_key_set"] = bool(data.get("api_key"))
    return redact(summary)


def summarize_config(config: Any, root: Path) -> dict[str, Any]:
    vector_store = model_to_dict(getattr(config, "vector_store", None))
    cache = model_to_dict(getattr(config, "cache", None))
    table_provider = model_to_dict(getattr(config, "table_provider", None))

    return {
        "root": str(root),
        "completion_models": {
            model_id: summarize_model(model)
            for model_id, model in getattr(config, "completion_models", {}).items()
        },
        "embedding_models": {
            model_id: summarize_model(model)
            for model_id, model in getattr(config, "embedding_models", {}).items()
        },
        "input": redact(model_to_dict(getattr(config, "input", None))),
        "input_storage": redact(model_to_dict(getattr(config, "input_storage", None))),
        "output_storage": redact(model_to_dict(getattr(config, "output_storage", None))),
        "update_output_storage": redact(
            model_to_dict(getattr(config, "update_output_storage", None))
        ),
        "cache": redact(cache),
        "reporting": redact(model_to_dict(getattr(config, "reporting", None))),
        "table_provider": redact(table_provider),
        "vector_store": redact(vector_store),
        "workflows": [enum_value(item) for item in (getattr(config, "workflows", None) or [])],
        "indexing_model_ids": {
            "embed_text": model_to_dict(getattr(config, "embed_text", None)).get(
                "embedding_model_id"
            ),
            "extract_graph": model_to_dict(getattr(config, "extract_graph", None)).get(
                "completion_model_id"
            ),
            "summarize_descriptions": model_to_dict(
                getattr(config, "summarize_descriptions", None)
            ).get("completion_model_id"),
            "community_reports": model_to_dict(
                getattr(config, "community_reports", None)
            ).get("completion_model_id"),
        },
        "query_model_ids": {
            "local_search": model_to_dict(getattr(config, "local_search", None)).get(
                "completion_model_id"
            ),
            "global_search": model_to_dict(getattr(config, "global_search", None)).get(
                "completion_model_id"
            ),
            "drift_search": model_to_dict(getattr(config, "drift_search", None)).get(
                "completion_model_id"
            ),
            "basic_search": model_to_dict(getattr(config, "basic_search", None)).get(
                "completion_model_id"
            ),
        },
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load a GraphRAG project config and print a secret-redacted JSON summary."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="Project root or settings file path containing settings.yaml/yml/json.",
    )
    parser.add_argument(
        "--indent",
        type=int,
        default=2,
        help="JSON indentation level. Use 0 for compact output.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    root = Path(args.root).expanduser().resolve()

    try:
        from graphrag.config.load_config import load_config
    except Exception as exc:  # pragma: no cover - depends on caller environment
        print(f"Failed to import GraphRAG config loader: {exc}", file=sys.stderr)
        return 2

    try:
        config = load_config(root)
    except Exception as exc:
        print(f"Failed to load GraphRAG config: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    indent = None if args.indent == 0 else args.indent
    print(json.dumps(summarize_config(config, root), indent=indent, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
