#!/usr/bin/env python3
"""No-download smoke check for the rag_retrieval reranker API.

This script intentionally does not instantiate rag_retrieval.Reranker because doing so
loads a tokenizer/model and may download artifacts. It only imports modules, inspects
signatures/registrations, and constructs lightweight Result/RankedResults objects.
"""

from __future__ import annotations

import argparse
import inspect
import json
import sys
from importlib import metadata
from typing import Any


EXPECTED_RERANKER_PARAMS = ["model_name", "model_type", "verbose", "kwargs"]
EXPECTED_AVAILABLE = {"CorssEncoderRanker", "LLMRanker"}
EXPECTED_ABSENT = {"ColBERTRanker"}


def _version() -> str | None:
    for dist_name in ("rag_retrieval", "rag-retrieval"):
        try:
            return metadata.version(dist_name)
        except metadata.PackageNotFoundError:
            continue
    return None


def _signature_names(obj: Any) -> list[str]:
    return list(inspect.signature(obj).parameters)


def _require(condition: bool, message: str, failures: list[str]) -> None:
    if not condition:
        failures.append(message)


def _dump_model(obj: Any) -> dict[str, Any]:
    if hasattr(obj, "model_dump"):
        return obj.model_dump()
    return obj.dict()


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    return parser.parse_args()


def main() -> int:
    parse_args()
    failures: list[str] = []

    try:
        import rag_retrieval
        from rag_retrieval import Reranker
        from rag_retrieval.infer.reranker_models import AVAILABLE_RANKERS
        from rag_retrieval.infer.reranker_models.result import RankedResults, Result
    except Exception as exc:  # pragma: no cover - diagnostic script
        print(json.dumps({"ok": False, "stage": "import", "error": repr(exc)}, indent=2, sort_keys=True))
        return 1

    reranker_signature = _signature_names(Reranker)
    available_rankers = sorted(AVAILABLE_RANKERS)

    _require(
        getattr(rag_retrieval, "Reranker", None) is Reranker,
        "rag_retrieval.Reranker is not the public Reranker export",
        failures,
    )
    _require(
        reranker_signature == EXPECTED_RERANKER_PARAMS,
        f"Reranker signature changed: expected {EXPECTED_RERANKER_PARAMS}, got {reranker_signature}",
        failures,
    )
    _require(
        EXPECTED_AVAILABLE.issubset(AVAILABLE_RANKERS),
        f"Missing registered rankers: {sorted(EXPECTED_AVAILABLE - set(AVAILABLE_RANKERS))}",
        failures,
    )
    _require(
        EXPECTED_ABSENT.isdisjoint(AVAILABLE_RANKERS),
        "ColBERTRanker is now registered; update ColBERT limitation guidance",
        failures,
    )

    method_signatures: dict[str, dict[str, list[str]]] = {}
    for ranker_name in sorted(EXPECTED_AVAILABLE & set(AVAILABLE_RANKERS)):
        ranker_cls = AVAILABLE_RANKERS[ranker_name]
        method_signatures[ranker_name] = {
            "init": _signature_names(ranker_cls.__init__),
            "compute_score": _signature_names(ranker_cls.compute_score),
            "rerank": _signature_names(ranker_cls.rerank),
        }

    cross_score = method_signatures.get("CorssEncoderRanker", {}).get("compute_score", [])
    cross_rerank = method_signatures.get("CorssEncoderRanker", {}).get("rerank", [])
    llm_score = method_signatures.get("LLMRanker", {}).get("compute_score", [])
    llm_rerank = method_signatures.get("LLMRanker", {}).get("rerank", [])

    _require("normalize" in cross_score, "Cross compute_score lacks normalize", failures)
    _require("enable_tqdm" in cross_score, "Cross compute_score lacks enable_tqdm", failures)
    _require("long_doc_process_strategy" in cross_rerank, "Cross rerank lacks long_doc_process_strategy", failures)
    _require("prompt" in llm_score, "LLM compute_score lacks prompt", failures)
    _require("cutoff_layers" in llm_score, "LLM compute_score lacks cutoff_layers", failures)
    _require("prompt" in llm_rerank, "LLM rerank lacks prompt", failures)
    _require("cutoff_layers" in llm_rerank, "LLM rerank lacks cutoff_layers", failures)
    _require("long_doc_process_strategy" in llm_rerank, "LLM rerank lacks long_doc_process_strategy", failures)

    result = Result(doc_id=0, text="first", score=0.25, rank=2)
    better = Result(doc_id="b", text="second", score=0.75, rank=1)
    ranked = RankedResults(results=[result, better], query="check", has_scores=True)

    _require(ranked.results_count() == 2, "RankedResults.results_count returned unexpected value", failures)
    _require(ranked.top_k(1)[0].doc_id == "b", "RankedResults.top_k did not sort by score", failures)
    _require(ranked.get_score_by_docid(0) == 0.25, "RankedResults.get_score_by_docid failed", failures)
    _require(ranked.get_score_by_docid("missing") is None, "Missing doc id should return None", failures)

    readable_signatures = {}
    for ranker_name in sorted(EXPECTED_AVAILABLE & set(AVAILABLE_RANKERS)):
        ranker_cls = AVAILABLE_RANKERS[ranker_name]
        readable_signatures[ranker_name] = {
            "init": str(inspect.signature(ranker_cls.__init__)),
            "compute_score": str(inspect.signature(ranker_cls.compute_score)),
            "rerank": str(inspect.signature(ranker_cls.rerank)),
        }

    report = {
        "ok": not failures,
        "distribution_version": _version(),
        "public_export": "Reranker",
        "reranker_signature": str(inspect.signature(Reranker)),
        "available_rankers": available_rankers,
        "colbert_registered": "ColBERTRanker" in AVAILABLE_RANKERS,
        "method_signatures": readable_signatures,
        "method_parameters": method_signatures,
        "ranked_results_probe": {
            "count": ranked.results_count(),
            "top_1": _dump_model(ranked.top_k(1)[0]),
            "score_doc_0": ranked.get_score_by_docid(0),
            "missing_score": ranked.get_score_by_docid("missing"),
        },
        "failures": failures,
    }

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if not failures else 1


if __name__ == "__main__":
    raise SystemExit(main())
