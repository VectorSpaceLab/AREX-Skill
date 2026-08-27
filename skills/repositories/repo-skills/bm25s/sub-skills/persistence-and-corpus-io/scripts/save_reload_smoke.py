#!/usr/bin/env python3
"""Bounded local save/load smoke test for bm25s persistence."""

from __future__ import annotations

import argparse
import shutil
import tempfile
from pathlib import Path

import bm25s


NAMES = {
    "data_name": "scores.npy",
    "indices_name": "indices.npy",
    "indptr_name": "indptr.npy",
    "vocab_name": "model-vocab.json",
    "params_name": "model-params.json",
    "nnoc_name": "nonoccurrence.npy",
    "corpus_name": "documents.jsonl",
}


def run(index_dir: Path) -> None:
    documents = [
        {"id": "red", "text": "red fox in a quiet forest"},
        {"id": "blue", "text": "blue whale in a deep ocean"},
    ]
    tokenized = bm25s.tokenize(
        [document["text"] for document in documents],
        stopwords=[],
        show_progress=False,
    )

    retriever = bm25s.BM25(method="bm25+")
    retriever.index(tokenized, show_progress=False)
    retriever.save(
        index_dir,
        corpus=documents,
        show_progress=False,
        **NAMES,
    )

    loaded = bm25s.BM25.load(
        index_dir,
        load_corpus=True,
        mmap=True,
        show_progress=False,
        **NAMES,
    )
    try:
        assert loaded.scores["num_docs"] == len(documents)
        assert len(loaded.corpus) == len(documents)
        assert isinstance(loaded.corpus, bm25s.utils.corpus.JsonlCorpus)

        fox_id = loaded.vocab_dict["fox"]
        result = loaded.retrieve([[fox_id]], k=1, show_progress=False)
        assert result.documents[0, 0]["id"] == "red"
        assert result.scores.shape == (1, 1)

        # load_scores is intentionally a partial, array-only operation.
        scores_only = bm25s.BM25()
        scores_only.load_scores(
            index_dir,
            num_docs=len(documents),
            mmap=True,
            data_name=NAMES["data_name"],
            indices_name=NAMES["indices_name"],
            indptr_name=NAMES["indptr_name"],
        )
        assert scores_only.scores["num_docs"] == len(documents)
        assert scores_only.scores["data"].shape == retriever.scores["data"].shape
    finally:
        loaded.corpus.close()


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run a tiny local bm25s save/load/mmap smoke test."
    )
    parser.add_argument(
        "--keep",
        action="store_true",
        help="Keep the temporary index directory and print its path.",
    )
    args = parser.parse_args()

    index_dir = Path(tempfile.mkdtemp(prefix="bm25s-persistence-smoke-"))
    try:
        run(index_dir)
        print(f"save/load smoke passed: {index_dir}")
        if args.keep:
            print("temporary index retained (--keep)")
            return 0
        return 0
    finally:
        if not args.keep:
            shutil.rmtree(index_dir, ignore_errors=True)


if __name__ == "__main__":
    raise SystemExit(main())
