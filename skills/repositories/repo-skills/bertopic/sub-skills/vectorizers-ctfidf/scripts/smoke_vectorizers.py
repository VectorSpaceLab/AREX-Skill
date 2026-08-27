#!/usr/bin/env python3
"""Tiny smoke checks for BERTopic vectorizer and c-TF-IDF workflows.

This script avoids downloads and works on a synthetic corpus. It exercises:
- custom tokenization and CountVectorizer tuning,
- c-TF-IDF scoring,
- a BERTopic `update_topics(...)` refresh path, and
- OnlineCountVectorizer decay / delete_min_df cleanup.
"""

from __future__ import annotations

import argparse
import json
import re
import warnings
from collections import OrderedDict

import numpy as np
from sklearn.feature_extraction.text import CountVectorizer

from bertopic.vectorizers import ClassTfidfTransformer, OnlineCountVectorizer

warnings.filterwarnings("ignore", message="Your stop_words may be inconsistent*", category=UserWarning)
warnings.filterwarnings("ignore", category=FutureWarning)

TOPIC_DOCS = [
    "rocket launch mission orbit project c++",
    "rocket launch window orbit project",
    "deep space rocket launch project",
    "sourdough bread starter project",
    "bread starter dough project",
    "artisan bread dough project",
    "c++ parser tokenization project",
    "tokenization with c++ project",
    "fast parser in c++ project",
]
TOPIC_IDS = [0, 0, 0, 1, 1, 1, 2, 2, 2]

STREAM_BATCHES = [
    ["alpha alpha beta", "alpha gamma"],
    ["beta beta delta", "alpha delta delta"],
    ["epsilon epsilon delta", "epsilon delta delta"],
    ["beta beta beta", "epsilon beta beta"],
]

STOPWORDS = ["project", "with", "in", "the", "and", "for", "of"]
TOKEN_PATTERN = re.compile(r"[a-z][a-z0-9+#-]*")


def custom_tokenizer(text: str) -> list[str]:
    return TOKEN_PATTERN.findall(text.lower())


def get_feature_names(vectorizer: CountVectorizer) -> list[str]:
    if hasattr(vectorizer, "get_feature_names_out"):
        return vectorizer.get_feature_names_out().tolist()
    return list(vectorizer.get_feature_names())


def group_documents_by_topic(docs: list[str], topics: list[int]) -> tuple[list[int], list[str]]:
    grouped: OrderedDict[int, list[str]] = OrderedDict()
    for doc, topic in zip(docs, topics):
        grouped.setdefault(topic, []).append(doc)
    topic_ids = list(grouped.keys())
    topic_docs = [" ".join(grouped[topic]) for topic in topic_ids]
    return topic_ids, topic_docs


def top_terms(matrix, words: list[str], top_n: int) -> dict[str, list[dict[str, float]]]:
    dense = matrix.toarray()
    result: dict[str, list[dict[str, float]]] = {}
    for row_idx, row in enumerate(dense):
        order = np.argsort(row)[::-1]
        terms = []
        for col_idx in order[:top_n]:
            score = float(row[col_idx])
            if score <= 0:
                continue
            terms.append({"term": words[col_idx], "score": round(score, 8)})
        result[f"topic_{row_idx}"] = terms
    return result


def ctfidf_sweep(top_n: int) -> dict[str, dict[str, object]]:
    topic_ids, grouped_docs = group_documents_by_topic(TOPIC_DOCS, TOPIC_IDS)
    configs = [
        (
            "baseline",
            CountVectorizer(
                tokenizer=custom_tokenizer,
                token_pattern=None,
                lowercase=False,
                min_df=1,
            ),
            ClassTfidfTransformer(),
        ),
        (
            "phrases_with_stopwords",
            CountVectorizer(
                tokenizer=custom_tokenizer,
                token_pattern=None,
                lowercase=False,
                stop_words=STOPWORDS,
                ngram_range=(1, 2),
                min_df=1,
            ),
            ClassTfidfTransformer(bm25_weighting=True, reduce_frequent_words=True),
        ),
        (
            "bounded_vocab",
            CountVectorizer(
                tokenizer=custom_tokenizer,
                token_pattern=None,
                lowercase=False,
                stop_words=STOPWORDS,
                ngram_range=(1, 2),
                min_df=1,
                max_features=12,
            ),
            ClassTfidfTransformer(bm25_weighting=True, reduce_frequent_words=True),
        ),
    ]

    summary: dict[str, dict[str, object]] = {}
    for name, vectorizer, transformer in configs:
        X = vectorizer.fit_transform(grouped_docs)
        words = get_feature_names(vectorizer)
        ctfidf = transformer.fit(X).transform(X)
        terms = top_terms(ctfidf, words, top_n)

        if not words:
            raise AssertionError(f"{name}: empty vocabulary")
        if not terms:
            raise AssertionError(f"{name}: no topic terms extracted")

        if name == "baseline":
            if "c++" not in words:
                raise AssertionError("custom tokenizer did not preserve 'c++'")
        if name == "phrases_with_stopwords":
            if not any(" " in item["term"] for values in terms.values() for item in values):
                raise AssertionError("bigrams did not surface any phrases")
        if name == "bounded_vocab" and len(words) > 12:
            raise AssertionError("max_features was not respected")

        summary[name] = {
            "topic_ids": topic_ids,
            "vocabulary_size": len(words),
            "top_terms": terms,
        }

    return summary


def online_vectorizer_smoke(decay: float, delete_min_df: int) -> dict[str, object]:
    vectorizer = OnlineCountVectorizer(
        tokenizer=custom_tokenizer,
        token_pattern=None,
        lowercase=False,
        decay=decay,
        delete_min_df=delete_min_df,
    )

    history: list[dict[str, object]] = []
    for batch in STREAM_BATCHES:
        vectorizer.partial_fit(batch)
        bow = vectorizer.update_bow(batch)
        vocabulary = sorted(vectorizer.vocabulary_.keys())
        totals = np.asarray(bow.sum(axis=0)).ravel().tolist()
        totals_by_term = {
            term: round(float(totals[index]), 6)
            for term, index in sorted(vectorizer.vocabulary_.items(), key=lambda item: item[1])
        }
        history.append(
            {
                "rows": int(bow.shape[0]),
                "cols": int(bow.shape[1]),
                "vocabulary": vocabulary,
                "column_totals": totals_by_term,
            }
        )

    if "beta" in history[0]["vocabulary"]:
        raise AssertionError("delete_min_df cleanup did not remove the first low-frequency terms")
    if "beta" in history[2]["vocabulary"]:
        raise AssertionError("beta should have been removed after decay and cleanup")
    if "beta" not in history[-1]["vocabulary"]:
        raise AssertionError("beta should reappear once it becomes frequent again")
    if any(item["rows"] != len(STREAM_BATCHES[0]) for item in history):
        raise AssertionError("online bow row counts changed unexpectedly")

    return {"history": history, "final_vocabulary_size": len(history[-1]["vocabulary"])}


def bertopic_update_smoke(top_n: int) -> dict[str, object]:
    from bertopic import BERTopic
    from bertopic.cluster import BaseCluster
    from bertopic.dimensionality import BaseDimensionalityReduction

    docs = [
        "rocket launch mission orbit project c++",
        "rocket launch window orbit project",
        "sourdough bread starter project",
        "bread starter dough project",
        "c++ parser tokenization project",
        "fast parser in c++ project",
    ]
    topics = [0, 0, 1, 1, 2, 2]
    embeddings = np.eye(len(docs), 4, dtype=float)

    base_vectorizer = CountVectorizer(
        tokenizer=custom_tokenizer,
        token_pattern=None,
        lowercase=False,
        min_df=1,
    )
    model = BERTopic(
        embedding_model=None,
        umap_model=BaseDimensionalityReduction(),
        hdbscan_model=BaseCluster(),
        vectorizer_model=base_vectorizer,
        ctfidf_model=ClassTfidfTransformer(),
        top_n_words=top_n,
        calculate_probabilities=False,
        verbose=False,
    )
    assigned_topics, _ = model.fit_transform(docs, embeddings=embeddings, y=topics)

    before = {
        str(topic): [word for word, _ in model.get_topic(topic)[:top_n]]
        for topic in sorted(set(topics))
    }

    refreshed_vectorizer = CountVectorizer(
        tokenizer=custom_tokenizer,
        token_pattern=None,
        lowercase=False,
        stop_words=STOPWORDS,
        ngram_range=(1, 2),
        min_df=1,
    )
    refreshed_ctfidf = ClassTfidfTransformer(bm25_weighting=True, reduce_frequent_words=True)
    model.update_topics(
        docs,
        topics=topics,
        vectorizer_model=refreshed_vectorizer,
        ctfidf_model=refreshed_ctfidf,
        top_n_words=top_n,
    )

    after = {
        str(topic): [word for word, _ in model.get_topic(topic)[:top_n]]
        for topic in sorted(set(topics))
    }

    if list(assigned_topics) != topics:
        raise AssertionError("fit_transform did not preserve the provided synthetic topics")
    if before == after:
        raise AssertionError("update_topics did not change the topic words")
    if not any(" " in term for words in after.values() for term in words):
        raise AssertionError("update_topics did not surface any phrase terms")

    return {"before": before, "after": after}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--top-n", type=int, default=5)
    parser.add_argument("--decay", type=float, default=0.25)
    parser.add_argument("--delete-min-df", type=int, default=2)
    parser.add_argument("--skip-bertopic-update", action="store_true")
    args = parser.parse_args()

    summary = {
        "ctfidf_sweep": ctfidf_sweep(args.top_n),
        "online_vectorizer": online_vectorizer_smoke(args.decay, args.delete_min_df),
    }

    if not args.skip_bertopic_update:
        summary["bertopic_update"] = bertopic_update_smoke(args.top_n)

    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
