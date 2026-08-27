#!/usr/bin/env python3
"""Safe LightRAG core API import and signature check.

This script imports installed package symbols and inspects signatures only. It
never initializes storages, calls LLMs, calls embeddings, contacts services,
reads credentials, or writes persistent data.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib import metadata
from typing import Any


EXPECTED_QUERY_MODES = {"local", "global", "hybrid", "naive", "mix", "bypass"}


def _distribution_version() -> str | None:
    for dist_name in ("lightrag-hku", "lightrag"):
        try:
            return metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            continue
    return None


def _signature_text(obj: Any) -> str:
    try:
        return str(inspect.signature(obj))
    except (TypeError, ValueError) as exc:
        return f"<unavailable: {exc}>"


def _query_modes_from_annotation(QueryParam: Any) -> list[str]:
    field = getattr(QueryParam, "__dataclass_fields__", {}).get("mode")
    annotation = getattr(field, "type", None)
    modes: set[str] = set()

    if hasattr(annotation, "__args__"):
        for item in annotation.__args__:
            if isinstance(item, str):
                modes.add(item)

    if not modes:
        text = str(annotation)
        for mode in EXPECTED_QUERY_MODES:
            if mode in text:
                modes.add(mode)

    return sorted(modes)


def collect() -> dict[str, Any]:
    import lightrag
    from lightrag import LightRAG, QueryParam
    from lightrag.utils import EmbeddingFunc, wrap_embedding_func_with_attrs

    query_default = QueryParam()
    light_rag_sig = _signature_text(LightRAG)
    query_param_sig = _signature_text(QueryParam)
    embedding_func_sig = _signature_text(EmbeddingFunc)
    wrap_sig = _signature_text(wrap_embedding_func_with_attrs)

    required_light_rag_params = {"working_dir", "llm_model_func", "embedding_func"}
    required_query_params = {"mode", "top_k", "chunk_top_k", "enable_rerank"}
    light_rag_params = set(inspect.signature(LightRAG).parameters)
    query_params = set(inspect.signature(QueryParam).parameters)

    query_modes = _query_modes_from_annotation(QueryParam)

    checks = {
        "import_lightrag": True,
        "has_LightRAG": callable(LightRAG),
        "has_QueryParam": callable(QueryParam),
        "has_EmbeddingFunc": callable(EmbeddingFunc),
        "has_wrap_embedding_func_with_attrs": callable(wrap_embedding_func_with_attrs),
        "LightRAG_required_params": required_light_rag_params <= light_rag_params,
        "QueryParam_required_params": required_query_params <= query_params,
        "QueryParam_default_mode_mix": query_default.mode == "mix",
        "QueryParam_enable_rerank_bool": isinstance(query_default.enable_rerank, bool),
        "QueryParam_modes_include_expected": EXPECTED_QUERY_MODES <= set(query_modes),
    }

    return {
        "ok": all(checks.values()),
        "module_file": getattr(lightrag, "__file__", None),
        "distribution_version": _distribution_version(),
        "signatures": {
            "LightRAG": light_rag_sig,
            "QueryParam": query_param_sig,
            "EmbeddingFunc": embedding_func_sig,
            "wrap_embedding_func_with_attrs": wrap_sig,
        },
        "query_defaults": {
            "mode": query_default.mode,
            "top_k": query_default.top_k,
            "chunk_top_k": query_default.chunk_top_k,
            "max_entity_tokens": query_default.max_entity_tokens,
            "max_relation_tokens": query_default.max_relation_tokens,
            "max_total_tokens": query_default.max_total_tokens,
            "enable_rerank": query_default.enable_rerank,
            "include_references": query_default.include_references,
        },
        "query_modes": query_modes,
        "checks": checks,
    }


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check installed LightRAG core imports and API signatures without running models or storages."
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print the full check result as JSON.",
    )
    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Only print PASS or FAIL.",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)

    try:
        result = collect()
    except Exception as exc:  # pragma: no cover - diagnostic path
        failure = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        if args.json:
            print(json.dumps(failure, indent=2, sort_keys=True))
        else:
            print(f"FAIL LightRAG core API import/signature check failed: {failure['error']}")
        return 1

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
    elif args.quiet:
        print("PASS" if result["ok"] else "FAIL")
    else:
        status = "PASS" if result["ok"] else "FAIL"
        print(f"{status} LightRAG core API check")
        print(f"distribution_version: {result['distribution_version']}")
        print(f"query_default_mode: {result['query_defaults']['mode']}")
        print(f"query_enable_rerank_default: {result['query_defaults']['enable_rerank']}")
        print(f"query_modes: {', '.join(result['query_modes'])}")
        failed = [name for name, passed in result["checks"].items() if not passed]
        if failed:
            print("failed_checks: " + ", ".join(failed))
            print("Run with --json for details.")

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
