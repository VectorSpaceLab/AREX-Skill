#!/usr/bin/env python3
"""Offline validator for a DocsGPT per-source configuration object.

Accepts JSON or YAML. This mirrors the public configuration contract and makes
no API calls; server validation remains authoritative.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

TOP = {"kind", "chunking", "retrieval", "graph"}
CHUNK = {"strategy", "max_tokens", "min_tokens", "duplicate_headers"}
RETRIEVAL = {"retriever", "exposure", "chunks", "score_threshold", "rephrase_query", "reranker", "prescreen"}
GRAPH = {"extraction_model", "max_chunks", "gleanings"}
PRESCREEN = {"candidate_k", "model", "batch_size", "max_keep"}
STRATEGIES = {"classic_chunk", "recursive", "markdown", "parent_child", "semantic"}
RETRIEVERS = {"classic", "default", "hybrid", "graphrag"}
EXPOSURES = {"prefetch", "agentic_tool"}


def load(path: Path) -> Any:
    text = path.read_text(encoding="utf-8")
    if path.suffix.lower() == ".json":
        return json.loads(text)
    try:
        import yaml
    except ImportError:
        return json.loads(text)
    return yaml.safe_load(text)


def mapping(value: Any, name: str, errors: list[str]) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        errors.append(f"{name} must be an object")
        return {}
    return value


def no_extra(value: dict[str, Any], allowed: set[str], name: str, errors: list[str]) -> None:
    extra = set(value) - allowed
    if extra:
        errors.append(f"{name} has unknown fields: {sorted(extra)}")


def bounded_int(value: Any, name: str, minimum: int, maximum: int | None, errors: list[str]) -> None:
    if isinstance(value, bool) or not isinstance(value, int):
        errors.append(f"{name} must be an integer")
    elif value < minimum or (maximum is not None and value > maximum):
        upper = f" and <= {maximum}" if maximum is not None else ""
        errors.append(f"{name} must be >= {minimum}{upper}")


def validate(data: Any) -> list[str]:
    errors: list[str] = []
    root = mapping(data, "config", errors)
    no_extra(root, TOP, "config", errors)

    chunk = mapping(root.get("chunking"), "chunking", errors)
    no_extra(chunk, CHUNK, "chunking", errors)
    if "strategy" in chunk and chunk["strategy"] not in STRATEGIES:
        errors.append(f"chunking.strategy must be one of {sorted(STRATEGIES)}")
    for field in ("max_tokens", "min_tokens"):
        if field in chunk:
            bounded_int(chunk[field], f"chunking.{field}", 1, None, errors)
    if all(field in chunk and isinstance(chunk[field], int) for field in ("max_tokens", "min_tokens")):
        if chunk["min_tokens"] > chunk["max_tokens"]:
            errors.append("chunking.min_tokens must be <= chunking.max_tokens")
    if "duplicate_headers" in chunk and not isinstance(chunk["duplicate_headers"], bool):
        errors.append("chunking.duplicate_headers must be boolean")

    retrieval = mapping(root.get("retrieval"), "retrieval", errors)
    no_extra(retrieval, RETRIEVAL, "retrieval", errors)
    if "retriever" in retrieval and retrieval["retriever"] not in RETRIEVERS:
        errors.append(f"retrieval.retriever must be one of {sorted(RETRIEVERS)}")
    if "exposure" in retrieval and retrieval["exposure"] not in EXPOSURES:
        errors.append(f"retrieval.exposure must be one of {sorted(EXPOSURES)}")
    if "chunks" in retrieval:
        bounded_int(retrieval["chunks"], "retrieval.chunks", 1, 500, errors)
    if "rephrase_query" in retrieval and not isinstance(retrieval["rephrase_query"], bool):
        errors.append("retrieval.rephrase_query must be boolean")

    prescreen = mapping(retrieval.get("prescreen"), "retrieval.prescreen", errors)
    if prescreen:
        no_extra(prescreen, PRESCREEN, "retrieval.prescreen", errors)
        values = {"candidate_k": 40, "batch_size": 10, "max_keep": 8, **prescreen}
        for field in ("candidate_k", "batch_size", "max_keep"):
            bounded_int(values[field], f"retrieval.prescreen.{field}", 1, 500, errors)
        if all(isinstance(values[f], int) for f in ("candidate_k", "max_keep")) and values["max_keep"] > values["candidate_k"]:
            errors.append("retrieval.prescreen.max_keep must be <= candidate_k")
        chunks = retrieval.get("chunks", 2)
        if isinstance(values["candidate_k"], int) and isinstance(chunks, int) and values["candidate_k"] < chunks:
            errors.append("retrieval.prescreen.candidate_k must be >= retrieval.chunks")

    graph = mapping(root.get("graph"), "graph", errors)
    no_extra(graph, GRAPH, "graph", errors)
    if graph.get("max_chunks") is not None:
        bounded_int(graph["max_chunks"], "graph.max_chunks", 1, None, errors)
    if "gleanings" in graph:
        bounded_int(graph["gleanings"], "graph.gleanings", 0, None, errors)
    return errors


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("config", type=Path)
    args = parser.parse_args()
    try:
        data = load(args.config)
    except Exception as error:
        print(f"ERROR: cannot parse {args.config}: {error}", file=sys.stderr)
        return 2
    errors = validate(data)
    for error in errors:
        print(f"ERROR: {error}", file=sys.stderr)
    if errors:
        return 1
    print("Source configuration is structurally valid")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
