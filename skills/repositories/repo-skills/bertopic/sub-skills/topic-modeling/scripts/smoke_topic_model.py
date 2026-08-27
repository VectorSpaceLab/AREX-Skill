#!/usr/bin/env python3
"""Offline BERTopic smoke checks for the topic-modeling sub-skill.

The script uses tiny synthetic documents and precomputed embeddings so it can
run without any model downloads. It exercises the core lifecycle, model
mutation, online partial_fit, and merge_models when the optional backend is
available.
"""

from __future__ import annotations

import copy
import sys
from typing import Iterable

import numpy as np
from sklearn.cluster import KMeans, MiniBatchKMeans
from sklearn.decomposition import IncrementalPCA, PCA

from bertopic import BERTopic
from bertopic.backend import BaseEmbedder
from bertopic.vectorizers import OnlineCountVectorizer


class ToyEmbedder(BaseEmbedder):
    """Deterministic local embedder for topic search smoke checks."""

    def embed(self, documents: Iterable[str], verbose: bool = False) -> np.ndarray:
        if isinstance(documents, str):
            documents = [documents]

        vectors = []
        for document in documents:
            text = "" if document is None else str(document).lower()
            vector = np.zeros(3, dtype=float)
            matched = False

            for index, token in enumerate(("alpha", "gamma", "omega")):
                if token in text:
                    vector[index] += 1.0
                    matched = True

            if not matched:
                vector[:] = 1.0 / 3.0

            vectors.append(vector)

        return np.vstack(vectors)


def build_primary_corpus() -> tuple[list[str], np.ndarray]:
    docs: list[str] = []
    embeddings: list[np.ndarray] = []
    themes = [("alpha", 0), ("gamma", 1), ("omega", 2)]

    base_vectors = {
        "alpha": np.array([0.95, 0.03, 0.02], dtype=float),
        "gamma": np.array([0.02, 0.95, 0.03], dtype=float),
        "omega": np.array([0.03, 0.02, 0.95], dtype=float),
    }

    for index in range(4):
        for theme, _ in themes:
            docs.append(f"{theme} signal {index}")
            embeddings.append(base_vectors[theme].copy())

    return docs, np.vstack(embeddings)


def build_transform_corpus() -> tuple[list[str], np.ndarray]:
    docs = ["alpha fresh", "gamma fresh", "omega fresh"]
    embeddings = np.array(
        [
            [0.95, 0.03, 0.02],
            [0.02, 0.95, 0.03],
            [0.03, 0.02, 0.95],
        ],
        dtype=float,
    )
    return docs, embeddings


def build_merge_corpus() -> tuple[list[str], np.ndarray, list[str], np.ndarray]:
    docs, embeddings = build_primary_corpus()
    left_indices = [i for i, doc in enumerate(docs) if "omega" not in doc]
    left_docs = [docs[i] for i in left_indices]
    left_embeddings = embeddings[left_indices]
    return left_docs, left_embeddings, docs, embeddings


def make_topic_model(n_clusters: int = 3, n_components: int = 2) -> BERTopic:
    return BERTopic(
        embedding_model=ToyEmbedder(),
        umap_model=PCA(n_components=n_components),
        hdbscan_model=KMeans(n_clusters=n_clusters, random_state=0, n_init=10),
        calculate_probabilities=False,
        min_topic_size=2,
        verbose=False,
    )


def make_online_model() -> BERTopic:
    return BERTopic(
        embedding_model=ToyEmbedder(),
        umap_model=IncrementalPCA(n_components=2),
        hdbscan_model=MiniBatchKMeans(n_clusters=3, random_state=0, batch_size=4, n_init=10),
        vectorizer_model=OnlineCountVectorizer(decay=0.01),
        calculate_probabilities=False,
        min_topic_size=2,
        verbose=False,
    )


def has_merge_backend() -> bool:
    for module_name in ("torch", "safetensors"):
        try:
            __import__(module_name)
            return True
        except ImportError:
            continue
    return False


def assert_fit_and_queries() -> BERTopic:
    docs, embeddings = build_primary_corpus()
    model = make_topic_model()
    topics, probabilities = model.fit_transform(docs, embeddings)

    assert len(topics) == len(docs)
    assert probabilities is None

    topic_info = model.get_topic_info()
    assert len(topic_info) == 3
    assert topic_info.Count.sum() == len(docs)
    assert len(set(topics)) == 3

    doc_info = model.get_document_info(docs)
    assert len(doc_info) == len(docs)

    new_docs, new_embeddings = build_transform_corpus()
    transformed_topics, transformed_probs = model.transform(new_docs, new_embeddings)
    assert len(transformed_topics) == len(new_docs)
    assert transformed_probs is None

    similar_topics, similarities = model.find_topics("alpha", top_n=2)
    assert len(similar_topics) == 2
    assert len(similarities) == 2
    assert similar_topics[0] in set(topic_info.Topic.tolist())
    assert model.get_topic(similar_topics[0])

    return model


def assert_mutations(base_model: BERTopic) -> None:
    docs, embeddings = build_primary_corpus()
    topic_ids = sorted(topic for topic in base_model.get_topic_info().Topic.tolist() if topic != -1)

    reduce_model = copy.deepcopy(base_model)
    reduce_model.reduce_topics(docs, nr_topics=2)
    reduce_info = reduce_model.get_topic_info()
    assert len(reduce_info) == 2
    assert reduce_info.Count.sum() == len(docs)

    merge_model = copy.deepcopy(base_model)
    merge_model.merge_topics(docs, topic_ids[:2])
    merge_info = merge_model.get_topic_info()
    assert len(merge_info) == 2
    assert merge_info.Count.sum() == len(docs)
    assert merge_model.topic_mapper_.get_mappings()

    delete_model = copy.deepcopy(base_model)
    deleted_topic = topic_ids[0]
    delete_model.delete_topics([deleted_topic])
    delete_info = delete_model.get_topic_info()
    assert -1 in set(delete_info.Topic.tolist())
    assert delete_model.topic_mapper_.get_mappings()[deleted_topic] == -1
    assert delete_info.Count.sum() == len(docs)

    before_outliers = sum(topic == -1 for topic in delete_model.topics_)
    reduced_topics = delete_model.reduce_outliers(
        docs,
        delete_model.topics_,
        strategy="embeddings",
        embeddings=embeddings,
        threshold=0.0,
    )
    after_outliers = sum(topic == -1 for topic in reduced_topics)
    assert len(reduced_topics) == len(docs)
    assert after_outliers < before_outliers


def assert_online_updates() -> None:
    docs, embeddings = build_primary_corpus()
    batches = [docs[i : i + 4] for i in range(0, len(docs), 4)]
    batch_embeddings = [embeddings[i : i + 4] for i in range(0, len(embeddings), 4)]

    model = make_online_model()
    cumulative_topics: list[int] = []
    seen = 0

    for batch_docs, batch_embeddings_chunk in zip(batches, batch_embeddings):
        model.partial_fit(batch_docs, batch_embeddings_chunk)
        seen += len(batch_docs)
        cumulative_topics.extend(model.topics_)

        assert len(model.topics_) == len(batch_docs)
        assert sum(model.topic_sizes_.values()) == seen
        assert model.topic_mapper_.get_mappings()

    assert len(cumulative_topics) == len(docs)
    assert len(model.get_topic_info()) >= 1


def assert_merge_models() -> None:
    if not has_merge_backend():
        print("[smoke] merge_models skipped: torch/safetensors not installed")
        return

    left_docs, left_embeddings, all_docs, all_embeddings = build_merge_corpus()
    right_docs = all_docs
    right_embeddings = all_embeddings

    left_model = make_topic_model(n_clusters=2)
    left_model.fit(left_docs, left_embeddings)

    right_model = make_topic_model(n_clusters=3)
    right_model.fit(right_docs, right_embeddings)

    merged_model = BERTopic.merge_models([left_model, right_model], embedding_model=ToyEmbedder())
    assert len(merged_model.get_topic_info()) >= len(left_model.get_topic_info())
    assert merged_model.get_topic_info().Topic.notna().all()


def main() -> int:
    base_model = assert_fit_and_queries()
    assert_mutations(base_model)
    assert_online_updates()
    assert_merge_models()
    print("[smoke] topic-modeling checks passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
