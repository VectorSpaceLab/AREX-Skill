#!/usr/bin/env python3
"""Inventory BERTopic embedding backends without downloads.

Default behavior:
- report module availability for the embedding backend stack,
- report exported backend objects and `NotInstalled` placeholders when possible,
- run a deterministic local encoder smoke that needs only NumPy.

Use `--with-precomputed` to add a tiny BERTopic smoke that exercises the
precomputed-embedding path when the runtime import stack is healthy.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import json
from typing import Any

import numpy as np


OPTIONAL_MODULES = [
    "bertopic",
    "bertopic.backend",
    "bertopic.cluster",
    "bertopic.dimensionality",
    "joblib",
    "numpy",
    "pandas",
    "scipy",
    "sklearn",
    "torch",
    "sentence_transformers",
    "transformers",
    "model2vec",
    "fastembed",
    "openai",
    "cohere",
    "langchain_core",
    "spacy",
    "flair",
    "gensim",
    "tensorflow_hub",
    "PIL",
]

BACKEND_EXPORTS = [
    "BaseEmbedder",
    "WordDocEmbedder",
    "OpenAIBackend",
    "CohereBackend",
    "MultiModalBackend",
    "Model2VecBackend",
    "FastEmbedBackend",
    "LangChainBackend",
    "languages",
]

INTERNAL_BACKENDS = {
    "SentenceTransformerBackend": "bertopic.backend._sentencetransformers",
    "HFTransformerBackend": "bertopic.backend._hftransformers",
    "SklearnEmbedder": "bertopic.backend._sklearn",
    "SpacyBackend": "bertopic.backend._spacy",
    "GensimBackend": "bertopic.backend._gensim",
    "FlairBackend": "bertopic.backend._flair",
    "USEBackend": "bertopic.backend._use",
    "MultiModalBackend": "bertopic.backend._multimodal",
    "Model2VecBackend": "bertopic.backend._model2vec",
    "FastEmbedBackend": "bertopic.backend._fastembed",
    "OpenAIBackend": "bertopic.backend._openai",
    "CohereBackend": "bertopic.backend._cohere",
    "LangChainBackend": "bertopic.backend._langchain",
    "WordDocEmbedder": "bertopic.backend._word_doc",
}


try:
    from bertopic.backend import BaseEmbedder as RuntimeBaseEmbedder
except Exception:  # pragma: no cover - handled as report data
    RuntimeBaseEmbedder = object


class TinyDeterministicBackend(RuntimeBaseEmbedder):
    """A tiny offline encoder used to smoke-test backend contracts."""

    def __init__(self, dimensions: int = 6):
        super().__init__()
        self.dimensions = dimensions

    @staticmethod
    def _ensure_list(values: Any):
        if values is None:
            return None
        if isinstance(values, (str, bytes)):
            return [values]
        return list(values)

    def _vectorize(self, value: Any) -> np.ndarray:
        text = "" if value is None else str(value)
        lowered = text.lower()
        vowels = sum(ch in "aeiou" for ch in lowered)
        consonants = sum(ch.isalpha() and ch not in "aeiou" for ch in lowered)
        digits = sum(ch.isdigit() for ch in lowered)
        spaces = sum(ch.isspace() for ch in lowered)
        punctuation = sum(not ch.isalnum() and not ch.isspace() for ch in lowered)
        code = sum((index + 1) * ord(ch) for index, ch in enumerate(lowered)) % 997
        vector = np.array(
            [len(lowered), vowels, consonants, digits, spaces, punctuation + code / 997.0],
            dtype=float,
        )
        if self.dimensions == vector.shape[0]:
            return vector
        if self.dimensions < vector.shape[0]:
            return vector[: self.dimensions]
        padding = np.zeros(self.dimensions - vector.shape[0], dtype=float)
        return np.concatenate([vector, padding])

    def _stack(self, values: list[Any]) -> np.ndarray:
        return np.vstack([self._vectorize(value) for value in values])

    def embed(self, documents, images=None, verbose: bool = False):
        docs = self._ensure_list(documents)
        imgs = self._ensure_list(images)
        if docs is None and imgs is None:
            raise ValueError("Need documents, images, or both.")
        if docs is not None and imgs is not None and len(docs) != len(imgs):
            raise ValueError("documents and images must have the same length.")

        doc_embeddings = self._stack(docs) if docs is not None else None
        image_embeddings = self._stack([repr(image) for image in imgs]) if imgs is not None else None

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


def module_spec(module_name: str) -> dict[str, Any]:
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


def collect_module_specs() -> dict[str, dict[str, Any]]:
    return {module_name: module_spec(module_name) for module_name in OPTIONAL_MODULES}


def collect_backend_exports() -> dict[str, Any]:
    try:
        backend = importlib.import_module("bertopic.backend")
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {
            "ok": False,
            "error": f"{type(exc).__name__}: {exc}",
        }

    exports: dict[str, Any] = {}
    for name in BACKEND_EXPORTS:
        value = getattr(backend, name, None)
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

        exports[name] = {
            "present": True,
            "kind": "class" if isinstance(value, type) else type(value).__name__,
        }

    return {
        "ok": True,
        "exports": exports,
        "all": list(getattr(backend, "__all__", [])),
    }


def collect_internal_backend_status() -> dict[str, Any]:
    status: dict[str, Any] = {}
    for class_name, module_name in INTERNAL_BACKENDS.items():
        try:
            module = importlib.import_module(module_name)
            value = getattr(module, class_name)
            status[class_name] = {
                "present": True,
                "module": module_name,
                "kind": "class" if isinstance(value, type) else type(value).__name__,
            }
        except Exception as exc:  # pragma: no cover - diagnostic path
            status[class_name] = {
                "present": False,
                "module": module_name,
                "error": f"{type(exc).__name__}: {exc}",
            }
    return status


def run_local_smoke() -> dict[str, Any]:
    backend = TinyDeterministicBackend()
    docs = ["alpha beta", "gamma-1"]
    words = ["alpha", "gamma"]
    images = ["img://one", "img://two"]

    doc_embeddings = backend.embed_documents(docs)
    word_embeddings = backend.embed_words(words)
    image_embeddings = backend.embed_images(images)
    paired_embeddings = backend.embed(docs, images=images)
    repeated_embeddings = backend.embed_documents(docs)

    if doc_embeddings.shape != (2, backend.dimensions):
        raise AssertionError(f"doc embeddings have shape {doc_embeddings.shape}")
    if word_embeddings.shape != (2, backend.dimensions):
        raise AssertionError(f"word embeddings have shape {word_embeddings.shape}")
    if image_embeddings.shape != (2, backend.dimensions):
        raise AssertionError(f"image embeddings have shape {image_embeddings.shape}")
    if paired_embeddings.shape != (2, backend.dimensions):
        raise AssertionError(f"paired embeddings have shape {paired_embeddings.shape}")
    if not np.allclose(doc_embeddings, repeated_embeddings):
        raise AssertionError("local backend is not deterministic")
    if not np.allclose(paired_embeddings, np.mean([doc_embeddings, image_embeddings], axis=0)):
        raise AssertionError("paired embeddings are not the expected average")

    return {
        "backend": backend.__class__.__name__,
        "dimensions": backend.dimensions,
        "doc_shape": list(doc_embeddings.shape),
        "word_shape": list(word_embeddings.shape),
        "image_shape": list(image_embeddings.shape),
        "paired_shape": list(paired_embeddings.shape),
        "fingerprint": round(float(doc_embeddings.sum() + word_embeddings.sum() + image_embeddings.sum()), 6),
    }


def run_precomputed_smoke() -> dict[str, Any]:
    try:
        from bertopic import BERTopic
        from bertopic.cluster import BaseCluster
        from bertopic.dimensionality import BaseDimensionalityReduction
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"status": "skipped", "reason": f"{type(exc).__name__}: {exc}"}

    docs = [
        "rocket launch mission orbit",
        "rocket launch window orbit",
        "sourdough bread starter",
        "bread starter dough",
    ]
    embeddings = np.array(
        [
            [0.10, 1.00, 0.00],
            [0.20, 0.90, 0.10],
            [1.00, 0.10, 0.00],
            [0.90, 0.20, 0.10],
        ],
        dtype=float,
    )
    topics = [0, 0, 1, 1]

    model = BERTopic(
        embedding_model=None,
        umap_model=BaseDimensionalityReduction(),
        hdbscan_model=BaseCluster(),
        calculate_probabilities=False,
        verbose=False,
    )
    assigned_topics, probabilities = model.fit_transform(docs, embeddings=embeddings, y=topics)

    if list(assigned_topics) != topics:
        raise AssertionError(f"manual topics were not preserved: {assigned_topics}")
    if model.embedding_model is not None:
        raise AssertionError("embedding_model should remain None for the precomputed smoke")

    return {
        "status": "ok",
        "topic_count": len(set(assigned_topics)),
        "assigned_topics": list(assigned_topics),
        "probabilities": None if probabilities is None else list(np.asarray(probabilities).shape),
        "embedding_shape": list(embeddings.shape),
    }


def build_report(with_precomputed: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "module_specs": collect_module_specs(),
        "backend_exports": collect_backend_exports(),
        "internal_backend_status": collect_internal_backend_status(),
        "local_smoke": run_local_smoke(),
    }
    if with_precomputed:
        report["precomputed_smoke"] = run_precomputed_smoke()
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--with-precomputed",
        action="store_true",
        help="Also run the tiny BERTopic precomputed-embedding smoke when possible.",
    )
    args = parser.parse_args()

    report = build_report(with_precomputed=args.with_precomputed)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
