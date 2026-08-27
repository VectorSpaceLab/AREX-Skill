#!/usr/bin/env python3
"""Run a tiny, local BM25S metadata retrieval example.

The script deliberately uses only an installed bm25s package and an in-memory
fixture, so it is safe to run from any current working directory.
"""

from __future__ import annotations

import argparse
import json

import bm25s


DOCUMENTS = [
    {
        "id": "cat-doc",
        "title": "About cats",
        "text": "Cats are feline animals that purr and like warm places.",
        "metadata": {"source": "fixture"},
    },
    {
        "id": "dog-doc",
        "title": "About dogs",
        "text": "Dogs are friendly animals that play and help people.",
        "metadata": {"source": "fixture"},
    },
    {
        "id": "fish-doc",
        "title": "About fish",
        "text": "Fish swim in water and use fins to move.",
        "metadata": {"source": "fixture"},
    },
]


def retrieve_metadata(query: str, k: int) -> dict[str, object]:
    """Index the fixture and return JSON-compatible metadata and scores."""
    if k < 1 or k > len(DOCUMENTS):
        raise ValueError(f"k must be between 1 and {len(DOCUMENTS)}")

    texts = [document["text"] for document in DOCUMENTS]
    corpus_tokens = bm25s.tokenize(
        texts, stopwords=None, show_progress=False, return_ids=True
    )
    if len(corpus_tokens.ids) != len(DOCUMENTS):
        raise ValueError("fixture metadata and tokenized corpus are misaligned")

    retriever = bm25s.BM25(corpus=DOCUMENTS, backend="numpy", csc_backend="numpy")
    retriever.index(corpus_tokens, show_progress=False)
    result = retriever.retrieve(
        bm25s.tokenize([query], stopwords=None, show_progress=False, return_ids=False),
        k=k,
        sorted=True,
        return_as="tuple",
        show_progress=False,
        backend_selection="numpy",
    )
    return {
        "query": query,
        "documents": result.documents[0].tolist(),
        "scores": [float(score) for score in result.scores[0]],
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", default="cat purr", help="plain-text query")
    parser.add_argument("--k", type=int, default=2, help="number of records to return")
    args = parser.parse_args()
    try:
        payload = retrieve_metadata(args.query, args.k)
    except ValueError as exc:
        parser.error(str(exc))
    print(json.dumps(payload, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
