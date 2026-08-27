#!/usr/bin/env python3
"""Tiny no-download smoke for BERTopic representation and labeling workflows.

The script uses a deterministic local embedder plus synthetic documents so it
can exercise keyword reranking, custom representations, multi-aspect topic
views, and label helpers without remote model downloads.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
import json
from typing import Any, Iterable

import numpy as np
from sklearn.cluster import KMeans
from sklearn.decomposition import PCA

from bertopic import BERTopic
from bertopic.backend import BaseEmbedder
from bertopic.representation import BaseRepresentation, KeyBERTInspired, MaximalMarginalRelevance

DOCS = [
    "rocket launch mission orbit",
    "rocket mission launch window",
    "sourdough bread starter",
    "artisan bread dough",
    "space rocket orbit",
    "bread starter oven",
]


def module_status(module_name: str) -> dict[str, Any]:
    try:
        spec = importlib.util.find_spec(module_name)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"present": False, "error": f"{type(exc).__name__}: {exc}"}
    if spec is None:
        return {"present": False}
    info = {"present": True}
    if getattr(spec, "origin", None):
        info["origin"] = spec.origin
    if getattr(spec, "loader", None):
        info["loader"] = type(spec.loader).__name__
    return info


class TinyEmbedder(BaseEmbedder):
    """Deterministic local embedder for no-download representation smoke tests."""

    def __init__(self, dimensions: int = 4):
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
        for index, token in enumerate(("rocket", "bread", "space", "starter")):
            if token in text:
                vector[index] = 1.0
        if not vector.any():
            vector[:] = 0.25
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


class EchoRepresentation(BaseRepresentation):
    """Custom representation that prefixes each topic with a deterministic echo token."""

    def extract_topics(self, topic_model, documents, c_tf_idf, topics):
        updated_topics = {}
        for topic_id, values in topics.items():
            updated_topics[topic_id] = [(f"echo-{topic_id}", 1.0)] + list(values[:4])
        return updated_topics


def collect_representation_status() -> dict[str, Any]:
    try:
        module = importlib.import_module("bertopic.representation")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    export_names = [
        "BaseRepresentation",
        "Cohere",
        "KeyBERTInspired",
        "LangChain",
        "LiteLLM",
        "LlamaCPP",
        "MaximalMarginalRelevance",
        "OpenAI",
        "PartOfSpeech",
        "TextGeneration",
        "VisualRepresentation",
        "ZeroShotClassification",
    ]

    exports: dict[str, Any] = {}
    for name in export_names:
        value = getattr(module, name, None)
        if value is None:
            exports[name] = {"present": False}
            continue
        if type(value).__name__ == "NotInstalled":
            exports[name] = {
                "present": False,
                "placeholder": True,
                "tool": getattr(value, "tool", None),
                "dep": getattr(value, "dep", None),
                "message": getattr(value, "msg", None),
            }
            continue
        exports[name] = {"present": True, "kind": "class" if isinstance(value, type) else type(value).__name__}

    return {"ok": True, "exports": exports, "all": list(getattr(module, "__all__", []))}


def fit_model() -> tuple[BERTopic, list[int]]:
    model = BERTopic(
        embedding_model=TinyEmbedder(),
        umap_model=PCA(n_components=2),
        hdbscan_model=KMeans(n_clusters=2, random_state=0, n_init=10),
        representation_model={
            "Main": MaximalMarginalRelevance(diversity=0.2),
            "KeyBERT": KeyBERTInspired(top_n_words=5),
            "Custom": EchoRepresentation(),
        },
        calculate_probabilities=False,
        verbose=False,
    )
    topics, probabilities = model.fit_transform(DOCS)
    if probabilities is not None:
        raise AssertionError("expected probabilities=None for the smoke model")
    if len(set(topics)) != 2:
        raise AssertionError(f"expected two topics, got {sorted(set(topics))}")
    return model, list(topics)


def summarize_model(model: BERTopic) -> dict[str, Any]:
    topic_info = model.get_topic_info()
    full_topics = model.get_topics(full=True)
    first_topic_id = int(topic_info.loc[topic_info.Topic != -1, "Topic"].iloc[0])
    first_topic_full = model.get_topic(first_topic_id, full=True)

    main_labels = model.generate_topic_labels(topic_prefix=False)
    aspect_labels = model.generate_topic_labels(topic_prefix=False, aspect="KeyBERT")

    model.set_topic_labels(main_labels)
    after_list = list(model.custom_labels_)
    model.set_topic_labels({first_topic_id: "Renamed topic"})
    after_dict = list(model.custom_labels_)

    if "KeyBERT" not in model.topic_aspects_:
        raise AssertionError("expected a KeyBERT aspect to be written")
    if "Custom" not in model.topic_aspects_:
        raise AssertionError("expected a Custom aspect to be written")
    if "Main" not in full_topics:
        raise AssertionError("expected get_topics(full=True) to include Main")
    if "KeyBERT" not in full_topics:
        raise AssertionError("expected get_topics(full=True) to include KeyBERT")
    if "Custom" not in full_topics:
        raise AssertionError("expected get_topics(full=True) to include Custom")
    if not first_topic_full:
        raise AssertionError("expected get_topic(..., full=True) to return aspect data")
    if len(main_labels) != len(set(model.topics_)):
        raise AssertionError("generate_topic_labels did not match the topic count")
    if len(aspect_labels) != len(set(model.topics_)):
        raise AssertionError("aspect-based label generation did not match the topic count")

    return {
        "topic_info_rows": len(topic_info),
        "topic_ids": sorted(int(topic) for topic in set(model.topics_)),
        "aspect_names": sorted(model.topic_aspects_.keys()),
        "main_labels": main_labels,
        "keybert_labels": aspect_labels,
        "labels_after_list": after_list,
        "labels_after_dict": after_dict,
        "first_topic_full_keys": sorted(first_topic_full.keys()) if isinstance(first_topic_full, dict) else [],
    }


def build_report() -> dict[str, Any]:
    model, topics = fit_model()
    return {
        "representation_exports": collect_representation_status(),
        "topic_summary": summarize_model(model),
        "smoke_topics": topics,
        "signatures": {
            "BaseRepresentation.extract_topics": str(
                inspect.signature(BaseRepresentation.extract_topics)
            ),
            "KeyBERTInspired.__init__": str(inspect.signature(KeyBERTInspired.__init__)),
            "MaximalMarginalRelevance.__init__": str(
                inspect.signature(MaximalMarginalRelevance.__init__)
            ),
        },
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.parse_args()
    print(json.dumps(build_report(), indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
