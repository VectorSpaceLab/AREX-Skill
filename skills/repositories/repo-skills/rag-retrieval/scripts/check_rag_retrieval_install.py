#!/usr/bin/env python3
"""No-download RAG-Retrieval package surface check."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
import sys


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> int:
    parse_args()
    report: dict[str, object] = {"ok": False, "checks": {}}
    checks = report["checks"]
    assert isinstance(checks, dict)

    try:
        dist = metadata.distribution("rag_retrieval")
        checks["distribution"] = {
            "ok": True,
            "name": dist.metadata.get("Name"),
            "version": dist.version,
            "summary": dist.metadata.get("Summary"),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        checks["distribution"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    try:
        package = importlib.import_module("rag_retrieval")
        reranker_module = importlib.import_module("rag_retrieval.reranker")
        result_module = importlib.import_module("rag_retrieval.infer.reranker_models.result")
        registry_module = importlib.import_module("rag_retrieval.infer.reranker_models")
        checks["imports"] = {"ok": True}
    except Exception as exc:  # pragma: no cover - diagnostic path
        checks["imports"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
        print(json.dumps(report, indent=2, sort_keys=True))
        return 1

    reranker = getattr(package, "Reranker", None)
    ranked_results = getattr(result_module, "RankedResults", None)
    result = getattr(result_module, "Result", None)
    available_rankers = getattr(registry_module, "AVAILABLE_RANKERS", {})

    checks["api"] = {
        "ok": callable(reranker) and ranked_results is not None and result is not None,
        "reranker_signature": str(inspect.signature(reranker)) if callable(reranker) else None,
        "available_rankers": sorted(available_rankers.keys()) if isinstance(available_rankers, dict) else str(available_rankers),
        "has_ranked_results_methods": all(
            hasattr(ranked_results, name) for name in ("results_count", "top_k", "get_score_by_docid")
        ) if ranked_results is not None else False,
    }

    try:
        sample = result(doc_id=0, text="doc", score=1.0, rank=1)
        ranked = ranked_results(results=[sample], query="query", has_scores=True)
        checks["result_model"] = {
            "ok": ranked.results_count() == 1 and ranked.top_k(1)[0].doc_id == 0,
            "score": ranked.get_score_by_docid(0),
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        checks["result_model"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    get_model_type = getattr(reranker_module, "_get_model_type", None)
    if callable(get_model_type):
        checks["model_type_mapping"] = {
            "ok": True,
            "cross_encoder": get_model_type("BAAI/bge-reranker-base"),
            "llm": get_model_type("BAAI/bge-reranker-v2-gemma"),
            "colbert": get_model_type("BAAI/bge-m3"),
        }
    else:
        checks["model_type_mapping"] = {"ok": False, "error": "missing _get_model_type"}

    failures = [name for name, value in checks.items() if isinstance(value, dict) and not value.get("ok")]
    report["ok"] = not failures
    report["failures"] = failures
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    sys.exit(main())
