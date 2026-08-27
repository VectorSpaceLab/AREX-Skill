#!/usr/bin/env python3
"""Tiny Gensim similarity-index smoke test."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def run_smoke() -> dict:
    from gensim import corpora, models, similarities

    docs = [
        "human computer interface",
        "user computer system",
        "graph trees minors",
        "trees graph survey",
    ]
    texts = [doc.split() for doc in docs]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]
    tfidf = models.TfidfModel(corpus)
    lsi = models.LsiModel(tfidf[corpus], id2word=dictionary, num_topics=2, random_seed=0)
    transformed = list(lsi[tfidf[corpus]])

    matrix_index = similarities.MatrixSimilarity(transformed, num_features=2)
    query = lsi[tfidf[dictionary.doc2bow("human system".split())]]
    matrix_scores = list(matrix_index[query])

    with tempfile.TemporaryDirectory() as tmp:
        prefix = str(Path(tmp) / "tiny-index")
        sharded_index = similarities.Similarity(prefix, transformed, num_features=2, shardsize=2)
        sharded_scores = list(sharded_index[query])

    assert len(matrix_scores) == len(docs)
    assert len(sharded_scores) == len(docs)
    assert max(matrix_scores) >= min(matrix_scores)
    assert max(sharded_scores) >= min(sharded_scores)
    top = max(enumerate(matrix_scores), key=lambda pair: pair[1])

    return {"documents": len(docs), "dictionary_size": len(dictionary), "top_matrix_match": [int(top[0]), float(top[1])]}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("similarity query smoke passed", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
