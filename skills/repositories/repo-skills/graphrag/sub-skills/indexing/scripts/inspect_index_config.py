#!/usr/bin/env python3
"""Summarize GraphRAG indexing-related config without printing secret values."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from typing import Any

SECRET_PATTERN = re.compile(r"(api[_-]?key|token|secret|password|connection[_-]?string)", re.I)

INDEXING_SECTIONS = [
    "input",
    "input_storage",
    "chunking",
    "output_storage",
    "update_output_storage",
    "table_provider",
    "cache",
    "reporting",
    "vector_store",
    "workflows",
    "embed_text",
    "extract_graph",
    "summarize_descriptions",
    "extract_graph_nlp",
    "prune_graph",
    "cluster_graph",
    "extract_claims",
    "community_reports",
    "snapshots",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Load a GraphRAG project config and summarize indexing-related fields."
    )
    parser.add_argument(
        "--root",
        default=".",
        help="GraphRAG project root containing settings.yml/settings.yaml/settings.json.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a readable text summary.",
    )
    parser.add_argument(
        "--include-model-names",
        action="store_true",
        help="Include configured completion/embedding model keys and non-secret provider/model names.",
    )
    return parser.parse_args()


def to_plain(value: Any) -> Any:
    if hasattr(value, "model_dump"):
        return value.model_dump(mode="json")
    if isinstance(value, dict):
        return {str(k): to_plain(v) for k, v in value.items()}
    if isinstance(value, list | tuple):
        return [to_plain(v) for v in value]
    return value


def redact(value: Any, key: str = "") -> Any:
    if SECRET_PATTERN.search(key):
        return "<redacted>" if value not in (None, "") else value
    if isinstance(value, dict):
        return {str(k): redact(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [redact(v, key) for v in value]
    return value


def compact_storage(section: Any) -> dict[str, Any]:
    data = redact(to_plain(section))
    if not isinstance(data, dict):
        return {"value": data}
    keys = ["type", "base_dir", "container_name", "database_name", "db_uri", "url"]
    return {k: data.get(k) for k in keys if k in data and data.get(k) not in (None, "")}


def summarize_models(config: Any) -> dict[str, Any]:
    summary: dict[str, Any] = {}
    for section_name in ["completion_models", "embedding_models"]:
        models = to_plain(getattr(config, section_name, {}))
        section_summary = {}
        for name, model_config in models.items():
            if not isinstance(model_config, dict):
                section_summary[name] = "<configured>"
                continue
            section_summary[name] = {
                key: model_config.get(key)
                for key in ["type", "model_provider", "model", "auth_method"]
                if model_config.get(key) not in (None, "")
            }
        summary[section_name] = section_summary
    return summary


def summarize_config(root: Path, include_model_names: bool) -> dict[str, Any]:
    try:
        from graphrag.config.load_config import load_config
    except Exception as exc:  # pragma: no cover - depends on caller environment
        raise RuntimeError(
            "Could not import GraphRAG. Run this script in an environment where the "
            "graphrag package is installed."
        ) from exc

    config = load_config(root_dir=root)
    summary: dict[str, Any] = {"root": str(root), "sections": {}}

    for name in INDEXING_SECTIONS:
        if not hasattr(config, name):
            continue
        value = getattr(config, name)
        if name.endswith("storage") or name in {"cache", "reporting", "vector_store", "table_provider"}:
            summary["sections"][name] = compact_storage(value)
        else:
            summary["sections"][name] = redact(to_plain(value))

    if include_model_names:
        summary["models"] = redact(summarize_models(config))

    return summary


def print_text(summary: dict[str, Any]) -> None:
    print(f"GraphRAG indexing config summary for: {summary['root']}")
    for name, value in summary["sections"].items():
        print(f"\n[{name}]")
        rendered = json.dumps(value, indent=2, sort_keys=True, ensure_ascii=False)
        print(rendered)
    if "models" in summary:
        print("\n[models]")
        print(json.dumps(summary["models"], indent=2, sort_keys=True, ensure_ascii=False))


def main() -> int:
    args = parse_args()
    try:
        summary = summarize_config(Path(args.root).expanduser(), args.include_model_names)
    except Exception as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True, ensure_ascii=False))
    else:
        print_text(summary)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
