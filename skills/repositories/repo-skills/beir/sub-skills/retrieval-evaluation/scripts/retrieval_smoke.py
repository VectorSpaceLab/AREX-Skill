#!/usr/bin/env python3
"""Offline BEIR retrieval/evaluation smoke test.

This script uses a deterministic toy encoder and in-memory BEIR-shaped data. It
performs no downloads, reads no repository files, and is intended to verify that
BEIR dense retrieval, standard metrics, custom metrics, and result export work
in the current Python environment.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

import numpy as np

from beir import util
from beir.retrieval.evaluation import EvaluateRetrieval
from beir.retrieval.search.dense import DenseRetrievalExactSearch as DRES


VOCABULARY = [
    "albert",
    "einstein",
    "mass",
    "energy",
    "physics",
    "wheat",
    "beer",
    "brewed",
    "faiss",
    "vector",
    "index",
    "search",
]


class ToyKeywordEncoder:
    """Small custom encoder implementing BEIR's dense model protocol."""

    def __init__(self, vocabulary: Iterable[str] = VOCABULARY) -> None:
        self.vocabulary = list(vocabulary)

    def encode_queries(self, queries: list[str], batch_size: int = 16, **kwargs) -> np.ndarray:
        return self._encode_texts(queries, expected_rows=len(queries))

    def encode_corpus(self, corpus: list[dict[str, str]], batch_size: int = 16, **kwargs) -> np.ndarray:
        texts = [(doc.get("title", "") + " " + doc.get("text", "")).strip() for doc in corpus]
        return self._encode_texts(texts, expected_rows=len(corpus))

    def _encode_texts(self, texts: list[str], expected_rows: int) -> np.ndarray:
        embeddings = np.zeros((len(texts), len(self.vocabulary)), dtype=np.float32)
        for row_index, text in enumerate(texts):
            normalized = text.lower().replace("-", " ")
            for column_index, token in enumerate(self.vocabulary):
                embeddings[row_index, column_index] = normalized.count(token)

        if embeddings.ndim != 2 or embeddings.shape[0] != expected_rows:
            raise ValueError(f"expected ({expected_rows}, dim) embeddings, got {embeddings.shape}")
        if not np.isfinite(embeddings).all():
            raise ValueError("toy embeddings contain non-finite values")
        return embeddings


def build_toy_dataset() -> tuple[dict[str, dict[str, str]], dict[str, str], dict[str, dict[str, int]]]:
    corpus = {
        "doc-einstein": {
            "title": "Albert Einstein",
            "text": "Mass energy equivalence is a physics result associated with Albert Einstein.",
        },
        "doc-beer": {
            "title": "Wheat beer",
            "text": "Wheat beer is brewed with a large proportion of wheat.",
        },
        "doc-faiss": {
            "title": "FAISS index",
            "text": "FAISS provides vector index search for dense retrieval experiments.",
        },
        "doc-background": {
            "title": "Background",
            "text": "This unrelated document should not be ranked first for any toy query.",
        },
    }
    queries = {
        "q-einstein": "Who developed mass energy physics ideas?",
        "q-beer": "Which beer is brewed with wheat?",
        "q-faiss": "What library provides vector index search?",
    }
    qrels = {
        "q-einstein": {"doc-einstein": 1},
        "q-beer": {"doc-beer": 1},
        "q-faiss": {"doc-faiss": 1},
    }
    return corpus, queries, qrels


def assert_metric_key(metric_dict: dict[str, float], key: str) -> None:
    if key not in metric_dict:
        raise AssertionError(f"missing metric key {key!r}; found {sorted(metric_dict)}")


def run_smoke(output_dir: Path | None = None) -> dict[str, object]:
    corpus, queries, qrels = build_toy_dataset()
    searcher = DRES(ToyKeywordEncoder(), batch_size=2, corpus_chunk_size=2, show_progress_bar=False)
    retriever = EvaluateRetrieval(searcher, k_values=[1, 2, 3], score_function="cos_sim")

    results = retriever.retrieve(corpus, queries)
    ndcg, metric_map, recall, precision = retriever.evaluate(qrels, results, retriever.k_values)
    mrr = retriever.evaluate_custom(qrels, results, retriever.k_values, metric="mrr")
    recall_cap = retriever.evaluate_custom(qrels, results, retriever.k_values, metric="recall_cap")
    hole = retriever.evaluate_custom(qrels, results, retriever.k_values, metric="hole")
    accuracy = retriever.evaluate_custom(qrels, results, retriever.k_values, metric="top_k_accuracy")

    for metric_dict, key in [
        (ndcg, "NDCG@1"),
        (metric_map, "MAP@1"),
        (recall, "Recall@1"),
        (precision, "P@1"),
        (mrr, "MRR@1"),
        (recall_cap, "R_cap@1"),
        (hole, "Hole@1"),
        (accuracy, "Accuracy@1"),
    ]:
        assert_metric_key(metric_dict, key)

    expected_top_docs = {
        "q-einstein": "doc-einstein",
        "q-beer": "doc-beer",
        "q-faiss": "doc-faiss",
    }
    for query_id, expected_doc_id in expected_top_docs.items():
        ranked_doc_ids = sorted(results[query_id], key=results[query_id].get, reverse=True)
        if ranked_doc_ids[0] != expected_doc_id:
            raise AssertionError(f"{query_id} top doc {ranked_doc_ids[0]!r} != {expected_doc_id!r}")

    expected_perfect = {
        "NDCG@1": ndcg["NDCG@1"],
        "MAP@1": metric_map["MAP@1"],
        "Recall@1": recall["Recall@1"],
        "P@1": precision["P@1"],
        "MRR@1": mrr["MRR@1"],
        "R_cap@1": recall_cap["R_cap@1"],
        "Accuracy@1": accuracy["Accuracy@1"],
    }
    for metric_name, value in expected_perfect.items():
        if value != 1.0:
            raise AssertionError(f"expected {metric_name}=1.0, got {value}")
    if hole["Hole@1"] != 0.0:
        raise AssertionError(f"expected Hole@1=0.0, got {hole['Hole@1']}")

    try:
        bad_retriever = EvaluateRetrieval(searcher, k_values=[1], score_function="cosine")
        bad_retriever.retrieve(corpus, queries)
    except ValueError as exc:
        invalid_score_error = str(exc)
    else:
        raise AssertionError("invalid score_function did not raise ValueError")

    summary = {
        "ok": True,
        "queries": len(queries),
        "corpus_documents": len(corpus),
        "top_docs": {qid: sorted(scores, key=scores.get, reverse=True)[0] for qid, scores in results.items()},
        "metrics": {
            "ndcg": ndcg,
            "map": metric_map,
            "recall": recall,
            "precision": precision,
            "mrr": mrr,
            "recall_cap": recall_cap,
            "hole": hole,
            "accuracy": accuracy,
        },
        "invalid_score_error": invalid_score_error,
    }

    if output_dir is not None:
        output_dir.mkdir(parents=True, exist_ok=True)
        util.save_runfile(str(output_dir / "toy.run.trec"), results, run_name="toy", top_k=3)
        util.save_results(
            str(output_dir / "toy.metrics.json"),
            ndcg,
            metric_map,
            recall,
            precision,
            mrr=mrr,
            recall_cap=recall_cap,
            hole=hole,
        )
        (output_dir / "toy.summary.json").write_text(json.dumps(summary, indent=2, sort_keys=True) + "\n")
        summary["output_dir"] = str(output_dir)

    return summary


def main() -> None:
    parser = argparse.ArgumentParser(description="Run an offline BEIR retrieval/evaluation smoke test.")
    parser.add_argument("--output-dir", type=Path, help="Optional directory for runfile and metric JSON outputs.")
    parser.add_argument("--json", action="store_true", help="Print the full summary as JSON.")
    args = parser.parse_args()

    summary = run_smoke(args.output_dir)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("BEIR retrieval smoke test passed")
        print("top_docs=" + json.dumps(summary["top_docs"], sort_keys=True))
        if args.output_dir:
            print(f"outputs={args.output_dir}")


if __name__ == "__main__":
    main()
