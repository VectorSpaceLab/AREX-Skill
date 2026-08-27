#!/usr/bin/env python3
"""Tiny TF-IDF/LSI/LDA/CoherenceModel smoke test for Gensim.

No network or external corpora are used. This validates API wiring, not topic
quality.
"""

from __future__ import annotations

import argparse
import json


def run_smoke() -> dict:
    from gensim import corpora, models
    from gensim.models import CoherenceModel

    texts = [
        ["human", "computer", "interface"],
        ["user", "computer", "system"],
        ["graph", "trees", "minors"],
        ["graph", "system", "trees"],
    ]
    dictionary = corpora.Dictionary(texts)
    corpus = [dictionary.doc2bow(text) for text in texts]

    tfidf = models.TfidfModel(corpus)
    corpus_tfidf = list(tfidf[corpus])
    lsi = models.LsiModel(corpus_tfidf, id2word=dictionary, num_topics=2, random_seed=0)
    lsi_topics = lsi.print_topics(num_topics=2)

    lda = models.LdaModel(
        corpus=corpus,
        id2word=dictionary,
        num_topics=2,
        passes=5,
        iterations=30,
        eval_every=None,
        random_state=0,
    )
    lda_topics = lda.show_topics(num_topics=2, formatted=False)
    cm = CoherenceModel(model=lda, corpus=corpus, dictionary=dictionary, coherence="u_mass", topn=3)
    coherence = float(cm.get_coherence())

    assert len(dictionary) >= 8
    assert len(corpus_tfidf) == len(corpus)
    assert len(lsi_topics) == 2
    assert len(lda_topics) == 2
    assert coherence == coherence  # not NaN

    return {
        "dictionary_size": len(dictionary),
        "lsi_topics": lsi_topics,
        "lda_topic_count": len(lda_topics),
        "u_mass_coherence": coherence,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    result = run_smoke()
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print("topic transform smoke passed", result)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
