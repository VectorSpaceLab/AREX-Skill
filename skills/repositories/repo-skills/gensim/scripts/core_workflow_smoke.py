#!/usr/bin/env python3
"""Run a tiny end-to-end Gensim corpus -> model -> similarity smoke test.

The fixture is embedded and no network/data downloads are used. The script is
safe to run from any working directory.
"""

from __future__ import annotations

import argparse
import json


def run_smoke() -> dict:
    from gensim import corpora, models, similarities

    documents = [
        "human machine interface",
        "survey user computer system",
        "graph trees minors",
        "human computer interaction",
    ]
    texts = [doc.lower().split() for doc in documents]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]

    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = list(tfidf[corpus])
    lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=2, random_seed=0)
    corpus_lsi = list(lsi[corpus_tfidf])

    index = similarities.MatrixSimilarity(corpus_lsi, num_features=2)
    query = dictionary.doc2bow("human computer".split())
    sims = list(enumerate(index[lsi[tfidf[query]]]))
    sims_sorted = sorted(sims, key=lambda pair: -pair[1])

    assert len(dictionary) >= 8, f"unexpected dictionary size {len(dictionary)}"
    assert len(corpus) == len(documents)
    assert len(corpus_lsi) == len(documents)
    assert len(sims_sorted) == len(documents)
    assert sims_sorted[0][1] >= sims_sorted[-1][1]

    return {
        "dictionary_size": len(dictionary),
        "documents": len(documents),
        "top_match": {"index": int(sims_sorted[0][0]), "score": float(sims_sorted[0][1])},
        "topics": lsi.print_topics(num_topics=2),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a short text summary")
    args = parser.parse_args()
    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("Gensim core workflow smoke passed")
        print(f"dictionary_size={result['dictionary_size']} documents={result['documents']} top_match={result['top_match']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
