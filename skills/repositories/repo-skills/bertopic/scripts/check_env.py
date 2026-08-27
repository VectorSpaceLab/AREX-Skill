#!/usr/bin/env python3
"""Inspect a BERTopic installation and run a tiny no-download smoke.

This helper stays offline by default. It reports package and optional-backend
availability, verified public imports, and key BERTopic signatures. Pass
`--smoke` to run a tiny synthetic fit with precomputed embeddings.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import inspect
import json
from typing import Any

OPTIONAL_MODULES = [
    "plotly",
    "umap",
    "hdbscan",
    "torch",
    "sentence_transformers",
    "transformers",
    "safetensors",
    "spacy",
    "openai",
    "cohere",
    "litellm",
    "langchain_core",
    "fastembed",
    "model2vec",
    "gensim",
    "flair",
    "tensorflow_hub",
    "PIL",
]

PUBLIC_IMPORTS = [
    ("bertopic", "BERTopic"),
    ("bertopic.backend", "BaseEmbedder"),
    ("bertopic.dimensionality", "BaseDimensionalityReduction"),
    ("bertopic.vectorizers", "ClassTfidfTransformer"),
    ("bertopic.vectorizers", "OnlineCountVectorizer"),
    ("bertopic.representation", "KeyBERTInspired"),
    ("bertopic.representation", "MaximalMarginalRelevance"),
]

SIGNATURE_TARGETS = [
    ("bertopic", "BERTopic", "__init__"),
    ("bertopic", "BERTopic", "fit_transform"),
    ("bertopic", "BERTopic", "transform"),
    ("bertopic", "BERTopic", "save"),
    ("bertopic", "BERTopic", "load"),
    ("bertopic.vectorizers", "ClassTfidfTransformer", "__init__"),
    ("bertopic.vectorizers", "OnlineCountVectorizer", "__init__"),
    ("bertopic.dimensionality", "BaseDimensionalityReduction", "transform"),
    ("bertopic.cluster", "BaseCluster", "transform"),
]


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


def collect_public_imports() -> list[dict[str, Any]]:
    entries: list[dict[str, Any]] = []
    for module_name, attr_name in PUBLIC_IMPORTS:
        try:
            module = importlib.import_module(module_name)
            value = getattr(module, attr_name)
        except Exception as exc:  # pragma: no cover - diagnostic path
            entries.append(
                {
                    "module": module_name,
                    "attr": attr_name,
                    "present": False,
                    "error": f"{type(exc).__name__}: {exc}",
                }
            )
            continue

        entry: dict[str, Any] = {"module": module_name, "attr": attr_name, "present": True}
        if isinstance(value, type):
            entry["kind"] = "class"
            entry["object"] = f"{value.__module__}.{value.__qualname__}"
        else:
            entry["kind"] = type(value).__name__
        if type(value).__name__ == "NotInstalled":
            entry.update(
                {
                    "present": False,
                    "placeholder": True,
                    "tool": getattr(value, "tool", None),
                    "dep": getattr(value, "dep", None),
                    "message": getattr(value, "msg", None),
                }
            )
        entries.append(entry)
    return entries


def collect_signatures() -> dict[str, str]:
    signatures: dict[str, str] = {}
    for module_name, attr_name, target_name in SIGNATURE_TARGETS:
        module = importlib.import_module(module_name)
        target = getattr(module, attr_name)
        signatures[f"{module_name}.{attr_name}.{target_name}"] = str(
            inspect.signature(getattr(target, target_name))
        )
    return signatures


def run_smoke() -> dict[str, Any]:
    import numpy as np
    from bertopic import BERTopic
    from bertopic.cluster import BaseCluster
    from bertopic.dimensionality import BaseDimensionalityReduction

    docs = ["rocket signal", "rocket launch", "bread signal", "bread starter"]
    embeddings = np.array(
        [
            [0.95, 0.05, 0.0],
            [0.90, 0.10, 0.0],
            [0.05, 0.95, 0.0],
            [0.10, 0.90, 0.0],
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
        raise AssertionError(f"expected synthetic topics {topics}, got {list(assigned_topics)}")
    if probabilities is not None:
        raise AssertionError("expected probabilities=None for the smoke model")
    topic_info = model.get_topic_info()
    if int(topic_info.Count.sum()) != len(docs):
        raise AssertionError("topic counts do not cover all documents")

    return {
        "assigned_topics": [int(topic) for topic in assigned_topics],
        "topic_count": len(set(int(topic) for topic in assigned_topics)),
        "count_sum": int(topic_info.Count.sum()),
        "embedding_shape": list(embeddings.shape),
    }


def build_report(include_smoke: bool) -> dict[str, Any]:
    try:
        import bertopic
        from bertopic import BERTopic
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"status": "failed", "error": f"{type(exc).__name__}: {exc}"}

    report: dict[str, Any] = {
        "status": "ok",
        "package": {
            "version": getattr(bertopic, "__version__", None),
            "module": bertopic.__name__,
            "file": getattr(bertopic, "__file__", None),
            "class": BERTopic.__name__,
        },
        "module_specs": collect_module_specs(),
        "public_imports": collect_public_imports(),
        "signatures": collect_signatures(),
    }

    if include_smoke:
        report["smoke"] = run_smoke()

    return report


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--smoke",
        action="store_true",
        help="Run a tiny synthetic no-download BERTopic fit using precomputed embeddings.",
    )
    args = parser.parse_args()

    report = build_report(include_smoke=args.smoke)
    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report.get("status") == "ok" else 1


if __name__ == "__main__":
    raise SystemExit(main())
