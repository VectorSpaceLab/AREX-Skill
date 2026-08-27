#!/usr/bin/env python3
"""Tiny Word2Vec/FastText/Doc2Vec/Phrases smoke test for Gensim."""

from __future__ import annotations

import argparse
import json
import tempfile
from pathlib import Path


def run_smoke() -> dict:
    from gensim.models import FastText, Phrases, Word2Vec
    from gensim.models.doc2vec import Doc2Vec, TaggedDocument
    from gensim.models import KeyedVectors

    sentences = [
        ["human", "computer", "interface"],
        ["human", "computer", "system"],
        ["graph", "trees", "minors"],
        ["graph", "trees", "system"],
    ]
    w2v = Word2Vec(sentences, vector_size=10, min_count=1, workers=1, epochs=5, seed=0)
    fasttext = FastText(sentences, vector_size=10, min_count=1, workers=1, epochs=5, seed=0)
    tagged = [TaggedDocument(words=s, tags=[i]) for i, s in enumerate(sentences)]
    doc2vec = Doc2Vec(tagged, vector_size=10, min_count=1, workers=1, epochs=5, seed=0)

    phrases = Phrases(sentences, min_count=1, threshold=1.0)
    phrased = [list(phrases[s]) for s in sentences]
    inferred = doc2vec.infer_vector(["human", "computer"])

    with tempfile.TemporaryDirectory() as tmp:
        vector_path = Path(tmp) / "vectors.txt"
        w2v.wv.save_word2vec_format(str(vector_path), binary=False)
        loaded = KeyedVectors.load_word2vec_format(str(vector_path), binary=False)
        assert loaded.vector_size == w2v.wv.vector_size
        assert loaded.index_to_key == w2v.wv.index_to_key

    assert len(w2v.wv) == len(fasttext.wv) >= 6
    assert len(doc2vec.dv) == len(sentences)
    assert inferred.shape == (10,)
    assert len(phrased) == len(sentences)
    assert "unseenword" in fasttext.wv  # subword lookup on this tiny model

    return {
        "word2vec_vocab": len(w2v.wv),
        "fasttext_vocab": len(fasttext.wv),
        "doc2vec_documents": len(doc2vec.dv),
        "inferred_shape": list(inferred.shape),
        "phrased_documents": len(phrased),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("embedding smoke passed", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
