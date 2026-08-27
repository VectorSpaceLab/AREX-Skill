#!/usr/bin/env python3
"""Run a bounded, local Tokenizer vocab/stopword persistence smoke check.

The fixture is intentionally tiny and creates all state in a temporary directory.
It does not download a dataset or rely on a repository-relative file.
"""

from __future__ import annotations

import json
from pathlib import Path
from tempfile import TemporaryDirectory

from bm25s.tokenization import Tokenizer


def main() -> None:
    corpus = ["A cat is playful", "A dog is friendly"]
    query = ["cat is unknown"]
    splitter = lambda text: text.split()

    tokenizer = Tokenizer(
        lower=True,
        splitter=splitter,
        stopwords=["is"],
        stemmer=None,
    )
    corpus_ids = tokenizer.tokenize(
        corpus,
        update_vocab=True,
        return_as="ids",
        allow_empty=False,
        show_progress=False,
    )
    query_ids = tokenizer.tokenize(
        query,
        update_vocab=False,
        return_as="ids",
        allow_empty=False,
        show_progress=False,
    )

    with TemporaryDirectory(prefix="bm25s-tokenizer-") as temp_dir:
        state_dir = Path(temp_dir)
        tokenizer.save_vocab(state_dir)
        tokenizer.save_stopwords(state_dir)

        restored = Tokenizer(
            lower=True,
            splitter=splitter,
            stopwords=[],
            stemmer=None,
        )
        restored.load_vocab(state_dir)
        restored.load_stopwords(state_dir)
        restored_query_ids = restored.tokenize(
            query,
            update_vocab=False,
            return_as="ids",
            allow_empty=False,
            show_progress=False,
        )

        assert corpus_ids == [[0, 1, 2], [0, 3, 4]], corpus_ids
        assert query_ids == [[1]], query_ids
        assert restored_query_ids == query_ids, (restored_query_ids, query_ids)
        assert restored.get_vocab_dict() == tokenizer.get_vocab_dict()
        assert list(restored.stopwords) == ["is"]
        assert (state_dir / "vocab.tokenizer.json").is_file()
        assert (state_dir / "stopwords.tokenizer.json").is_file()
        assert not (state_dir / "vocab.index.json").exists()

        result = {
            "status": "ok",
            "corpus_documents": len(corpus_ids),
            "query_ids": query_ids,
            "vocab_size": len(tokenizer.get_vocab_dict()),
            "saved_files": [
                "vocab.tokenizer.json",
                "stopwords.tokenizer.json",
            ],
        }

    print(json.dumps(result, ensure_ascii=False, sort_keys=True))


if __name__ == "__main__":
    main()
