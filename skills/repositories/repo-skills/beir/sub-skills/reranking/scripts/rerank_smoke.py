#!/usr/bin/env python3
"""No-download smoke test for BEIR Rerank mechanics.

This script uses a fake cross-encoder-compatible object to prove that BEIR
constructs query/document pairs, slices candidates by top_k, and returns
reranker scores instead of original retrieval scores.
"""

from __future__ import annotations

import sys
from pathlib import Path


def _allow_source_checkout_import() -> None:
    """Let the script run from a BEIR source checkout as well as an installed package."""

    for parent in Path(__file__).resolve().parents:
        if (parent / "pyproject.toml").exists() and (parent / "beir" / "reranking").is_dir():
            sys.path.insert(0, str(parent))
            return


try:
    from beir.reranking import Rerank
except ModuleNotFoundError:
    _allow_source_checkout_import()
    from beir.reranking import Rerank


class FakeCrossEncoder:
    """Deterministic scorer with the same protocol BEIR Rerank expects."""

    def __init__(self) -> None:
        self.calls: list[tuple[list[list[str]], int]] = []

    def predict(self, sentence_pairs, batch_size):
        self.calls.append((list(sentence_pairs), batch_size))
        scores = []
        for query, document in sentence_pairs:
            score = 0.0
            if "best answer" in document:
                score += 10.0
            if "second answer" in document:
                score += 5.0
            if "noise" in document:
                score -= 2.0
            if "important" in query:
                score += 1.0
            scores.append(score)
        return scores


def main() -> None:
    corpus = {
        "d1": {"title": "Low retrieval", "text": "best answer with exact evidence"},
        "d2": {"title": "High retrieval", "text": "noise document"},
        "d3": {"title": "Middle retrieval", "text": "second answer"},
    }
    queries = {"q1": "important query"}
    results = {"q1": {"d2": 9.0, "d3": 8.0, "d1": 1.0}}

    fake_model = FakeCrossEncoder()
    reranker = Rerank(fake_model, batch_size=2)
    reranked = reranker.rerank(corpus, queries, results, top_k=2)

    assert set(reranked) == {"q1"}
    assert set(reranked["q1"]) == {"d2", "d3"}, reranked
    assert "d1" not in reranked["q1"], "top_k=2 should exclude the lowest retrieval candidate"
    assert reranked["q1"]["d3"] > reranked["q1"]["d2"], reranked

    assert len(fake_model.calls) == 1
    sentence_pairs, batch_size = fake_model.calls[0]
    assert batch_size == 2
    assert sentence_pairs == [
        ["important query", "High retrieval noise document"],
        ["important query", "Middle retrieval second answer"],
    ]

    print("BEIR rerank smoke passed: top_k slicing and deterministic score replacement verified.")


if __name__ == "__main__":
    main()
