#!/usr/bin/env python3
"""Tiny no-download smoke for BERTopic inspection and plotting workflows.

The script fits a deterministic synthetic model, then exercises topic tables,
hierarchy helpers, distribution helpers, and the main plot families. It keeps
plots small and uses precomputed 2D layouts where practical.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
from typing import Any, Iterable

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from bertopic import BERTopic
from bertopic.backend import BaseEmbedder

DOCS = [
    "rocket launch mission orbit",
    "rocket launch window",
    "rocket mission control",
    "sourdough bread starter",
    "artisan bread dough",
    "bread starter oven",
    "space telescope galaxy",
    "space shuttle mission",
    "space orbit station",
]
TIMESTAMPS = [0, 0, 1, 1, 2, 2, 3, 3, 3]
CLASSES = ["news", "news", "news", "food", "food", "food", "science", "science", "science"]


class TinyEmbedder(BaseEmbedder):
    """Deterministic local embedder for smoke tests."""

    def __init__(self, dimensions: int = 3):
        super().__init__()
        self.dimensions = dimensions

    @staticmethod
    def _as_list(values: Any) -> list[Any] | None:
        if values is None:
            return None
        if isinstance(values, (str, bytes)):
            return [values]
        return list(values)

    def _vectorize(self, value: Any) -> np.ndarray:
        text = "" if value is None else str(value).lower()
        vector = np.zeros(self.dimensions, dtype=float)
        for index, token in enumerate(("rocket", "bread", "space")):
            if token in text:
                vector[index] = 1.0
        if not vector.any():
            vector[:] = 1.0 / self.dimensions
        return vector

    def embed(self, documents, images=None, verbose: bool = False):
        docs = self._as_list(documents)
        imgs = self._as_list(images)
        if docs is None and imgs is None:
            raise ValueError("documents or images must be provided")
        if docs is not None and imgs is not None and len(docs) != len(imgs):
            raise ValueError("documents and images must have the same length")

        doc_embeddings = None if docs is None else np.vstack([self._vectorize(doc) for doc in docs])
        image_embeddings = None if imgs is None else np.vstack([self._vectorize(repr(image)) for image in imgs])

        if doc_embeddings is not None and image_embeddings is not None:
            return np.mean([doc_embeddings, image_embeddings], axis=0)
        if doc_embeddings is not None:
            return doc_embeddings
        return image_embeddings

    def embed_documents(self, documents, verbose: bool = False):
        return self.embed(documents, verbose=verbose)

    def embed_words(self, words, verbose: bool = False):
        return self.embed(words, verbose=verbose)

    def embed_images(self, images, verbose: bool = False):
        return self.embed(None, images=images, verbose=verbose)


def maybe_spec(module_name: str) -> bool:
    try:
        return importlib.util.find_spec(module_name) is not None
    except Exception:  # pragma: no cover - defensive
        return False


def fit_model() -> tuple[BERTopic, np.ndarray, list[int]]:
    embeddings = TinyEmbedder().embed_documents(DOCS)
    model = BERTopic(
        embedding_model=TinyEmbedder(),
        umap_model=PCA(n_components=2),
        hdbscan_model=KMeans(n_clusters=3, random_state=0, n_init=10),
        calculate_probabilities=False,
        verbose=False,
    )
    topics, probabilities = model.fit_transform(DOCS)
    if probabilities is not None:
        raise AssertionError("expected probabilities=None for the smoke model")
    if len(set(topics)) != 3:
        raise AssertionError(f"expected three topics, got {sorted(set(topics))}")
    return model, embeddings, [int(topic) for topic in topics]


def figure_summary(fig: Any) -> dict[str, Any]:
    if fig is None:
        raise AssertionError("expected a figure, got None")
    payload = fig.to_dict() if hasattr(fig, "to_dict") else {}
    summary = {"type": type(fig).__name__}
    if isinstance(payload, dict):
        summary["trace_count"] = len(payload.get("data", []))
        layout = payload.get("layout", {})
        if isinstance(layout, dict):
            summary["annotation_count"] = len(layout.get("annotations", []))
            summary["slider_count"] = len(layout.get("sliders", []))
    return summary


def summarize_core_tables(model: BERTopic, docs: list[str]) -> dict[str, Any]:
    topic_info = model.get_topic_info()
    topic_freq = model.get_topic_freq()
    representatives = model.get_representative_docs()

    first_topic = int(topic_info.loc[topic_info.Topic != -1, "Topic"].iloc[0])
    first_topic_words = model.get_topic(first_topic)
    if not first_topic_words:
        raise AssertionError("expected a non-empty topic representation")

    return {
        "topic_info_rows": len(topic_info),
        "topic_freq_rows": len(topic_freq),
        "representative_topic_count": len(representatives),
        "first_topic": first_topic,
        "first_topic_word_count": len(first_topic_words),
        "topic_ids": sorted(int(topic) for topic in set(model.topics_)),
    }


def summarize_analysis(model: BERTopic, docs: list[str]) -> dict[str, Any]:
    hier_topics = model.hierarchical_topics(docs)
    tree = model.get_topic_tree(hier_topics)
    topic_distr, token_distr = model.approximate_distribution(docs[:3], calculate_tokens=True, min_similarity=0.0)
    topics_over_time = model.topics_over_time(docs, TIMESTAMPS)
    topics_per_class = model.topics_per_class(docs, CLASSES)

    if topic_distr.shape[0] != 3:
        raise AssertionError("approximate_distribution returned the wrong number of rows")
    if token_distr is None or len(token_distr) != 3:
        raise AssertionError("token-level approximate distribution was not returned")
    if len(topics_over_time) == 0 or len(topics_per_class) == 0:
        raise AssertionError("expected non-empty comparison tables")
    if len(tree) < 10:
        raise AssertionError("topic tree output looks too small")

    return {
        "hierarchical_topics_rows": len(hier_topics),
        "tree_length": len(tree),
        "topics_over_time_rows": len(topics_over_time),
        "topics_per_class_rows": len(topics_per_class),
        "topic_distribution_shape": list(topic_distr.shape),
        "token_distribution_length": len(token_distr),
    }


def summarize_plots(model: BERTopic, docs: list[str], embeddings: np.ndarray) -> dict[str, Any]:
    reduced_embeddings = PCA(n_components=2).fit_transform(embeddings)
    hier_topics = model.hierarchical_topics(docs)
    topic_distr, token_distr = model.approximate_distribution(docs[:3], calculate_tokens=True, min_similarity=0.0)
    topics_over_time = model.topics_over_time(docs, TIMESTAMPS)
    topics_per_class = model.topics_per_class(docs, CLASSES)

    plots = {
        "visualize_topics": figure_summary(model.visualize_topics(top_n_topics=3)),
        "visualize_barchart": figure_summary(model.visualize_barchart(top_n_topics=3)),
        "visualize_heatmap": figure_summary(model.visualize_heatmap(top_n_topics=3)),
        "visualize_term_rank": figure_summary(model.visualize_term_rank()),
        "visualize_documents": figure_summary(
            model.visualize_documents(docs, reduced_embeddings=reduced_embeddings, hide_document_hover=True)
        ),
        "visualize_distribution": figure_summary(model.visualize_distribution(topic_distr[0], min_probability=0.0)),
        "visualize_approximate_distribution": None,
        "visualize_hierarchy": figure_summary(model.visualize_hierarchy(hierarchical_topics=hier_topics)),
        "visualize_topics_over_time": figure_summary(model.visualize_topics_over_time(topics_over_time, top_n_topics=3)),
        "visualize_topics_per_class": figure_summary(model.visualize_topics_per_class(topics_per_class, top_n_topics=3)),
        "visualize_hierarchical_documents": None,
    }

    try:
        plots["visualize_hierarchical_documents"] = figure_summary(
            model.visualize_hierarchical_documents(
                docs,
                hier_topics,
                reduced_embeddings=reduced_embeddings,
                hide_document_hover=True,
            )
        )
    except Exception as exc:
        plots["visualize_hierarchical_documents"] = {
            "status": "skipped",
            "reason": f"{type(exc).__name__}: {exc}",
        }

    try:
        plots["visualize_approximate_distribution"] = {
            "type": type(model.visualize_approximate_distribution(docs[0], token_distr[0])).__name__,
        }
    except Exception as exc:
        plots["visualize_approximate_distribution"] = {
            "status": "skipped",
            "reason": f"{type(exc).__name__}: {exc}",
        }

    if maybe_spec("datamapplot"):
        plots["visualize_document_datamap"] = figure_summary(
            model.visualize_document_datamap(docs, reduced_embeddings=reduced_embeddings, interactive=False)
        )
    else:
        plots["visualize_document_datamap"] = {"status": "skipped", "reason": "datamapplot not installed"}

    if not plots["visualize_topics"]["trace_count"]:
        raise AssertionError("visualize_topics did not create any traces")
    if not plots["visualize_barchart"].get("annotation_count", 0):
        raise AssertionError("visualize_barchart did not create annotations")
    if not plots["visualize_heatmap"]["trace_count"]:
        raise AssertionError("visualize_heatmap did not create any traces")
    if not plots["visualize_documents"]["trace_count"]:
        raise AssertionError("visualize_documents did not create any traces")
    if not plots["visualize_distribution"]["trace_count"]:
        raise AssertionError("visualize_distribution did not create any traces")
    if not plots["visualize_hierarchy"]["trace_count"]:
        raise AssertionError("visualize_hierarchy did not create any traces")
    if not plots["visualize_topics_over_time"]["trace_count"]:
        raise AssertionError("visualize_topics_over_time did not create any traces")
    if not plots["visualize_topics_per_class"]["trace_count"]:
        raise AssertionError("visualize_topics_per_class did not create any traces")

    hierarchical_documents_plot = plots["visualize_hierarchical_documents"]
    if not (isinstance(hierarchical_documents_plot, dict) and hierarchical_documents_plot.get("status") == "skipped"):
        if not hierarchical_documents_plot["trace_count"]:
            raise AssertionError("visualize_hierarchical_documents did not create any traces")

    return plots


def build_report() -> dict[str, Any]:
    model, embeddings, topics = fit_model()
    core = summarize_core_tables(model, DOCS)
    analysis = summarize_analysis(model, DOCS)
    plots = summarize_plots(model, DOCS, embeddings)
    return {
        "topic_ids": topics,
        "core": core,
        "analysis": analysis,
        "plots": plots,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(build_report(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
