#!/usr/bin/env python3
"""Tiny local-only BERTopic serialization smoke check.

The script avoids external datasets, model downloads, and Hugging Face network calls.
It checks:
- pickle save/load from a local file,
- one lightweight local save/load format (`safetensors` by default, then `pytorch`),
- `save_ctfidf=True` file layout,
- load with and without an explicit embedding backend, and
- the local-versus-Hub boundary that requires credentials only for Hub actions.
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any


@dataclass(frozen=True)
class Runtime:
    BERTopic: Any
    BaseEmbedder: Any
    KMeans: Any
    PCA: Any
    np: Any


@dataclass(frozen=True)
class SmokeData:
    docs: list[str]
    embeddings: Any


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def require_runtime() -> Runtime:
    """Import the minimal runtime and fail with a concise repair hint."""

    expected_modules = ["bertopic", "numpy", "sklearn", "joblib"]
    missing = [module for module in expected_modules if not module_available(module)]

    try:
        import numpy as np
        from bertopic import BERTopic
        from bertopic.backend import BaseEmbedder
        from sklearn.cluster import KMeans
        from sklearn.decomposition import PCA
    except Exception as exc:  # noqa: BLE001 - convert import stack into user-facing smoke failure
        hint = (
            "Cannot run smoke_serialization.py because the BERTopic runtime imports failed. "
            "Install BERTopic with its base dependencies before running this smoke."
        )
        if missing:
            hint += f" Missing modules detected before import: {', '.join(missing)}."
        hint += f" Original error: {type(exc).__name__}: {exc}"
        raise SystemExit(hint) from exc

    logging.getLogger("BERTopic").setLevel(logging.ERROR)
    return Runtime(BERTopic=BERTopic, BaseEmbedder=BaseEmbedder, KMeans=KMeans, PCA=PCA, np=np)


def make_synthetic_data(np: Any, repeats: int = 5) -> SmokeData:
    """Create a deterministic three-theme corpus and matching embeddings."""

    groups: list[tuple[str, list[str], Any]] = [
        (
            "space",
            [
                "rocket launch orbit mission",
                "planet telescope galaxy orbit",
                "astronaut lunar launch vehicle",
            ],
            np.array([5.0, 0.0, 0.0, 0.0, 0.0]),
        ),
        (
            "bread",
            [
                "sourdough starter flour crust",
                "bakery loaf dough yeast",
                "artisan bread oven crumb",
            ],
            np.array([0.0, 5.0, 0.0, 0.0, 0.0]),
        ),
        (
            "finance",
            [
                "equity market portfolio risk",
                "bank credit rate loan",
                "bond yield trading desk",
            ],
            np.array([0.0, 0.0, 5.0, 0.0, 0.0]),
        ),
    ]

    docs: list[str] = []
    embeddings: list[Any] = []
    for i in range(repeats):
        for label, templates, center in groups:
            docs.append(f"{templates[i % len(templates)]} {label} topic {i}")
            noise = np.array([0.02 * i, 0.01 * (i % 2), 0.015 * (i % 3), 0.01, 0.0])
            embeddings.append(center + noise)

    return SmokeData(docs=docs, embeddings=np.vstack(embeddings).astype("float64"))


def fit_tiny_model(rt: Runtime, data: SmokeData) -> tuple[Any, dict[str, Any]]:
    """Fit a small no-download model with precomputed embeddings."""

    topic_model = rt.BERTopic(
        embedding_model=None,
        umap_model=rt.PCA(n_components=2),
        hdbscan_model=rt.KMeans(n_clusters=3, random_state=42, n_init=10),
        top_n_words=5,
        verbose=False,
    )
    topics, probabilities = topic_model.fit_transform(data.docs, embeddings=data.embeddings)
    assert len(topics) == len(data.docs), "fit_transform returned one topic per document"
    assert len(set(int(topic) for topic in topics)) == 3, "expected three synthetic topics"
    assert int(topic_model.get_topic_info().Count.sum()) == len(data.docs), "topic counts do not cover all docs"

    return topic_model, {
        "docs": len(data.docs),
        "embedding_shape": list(data.embeddings.shape),
        "topics": sorted(set(int(topic) for topic in topics)),
        "probabilities_is_none": probabilities is None,
        "fitted_clusterer": type(topic_model.hdbscan_model).__name__,
        "fitted_reducer": type(topic_model.umap_model).__name__,
    }


def check_topic_count(model: Any, expected: int, context: str) -> int:
    count_sum = int(model.get_topic_info().Count.sum())
    assert count_sum == expected, f"{context}: expected Count.sum={expected}, got {count_sum}"
    return count_sum


def run_pickle_roundtrip(rt: Runtime, model: Any, data: SmokeData, root: Path) -> dict[str, Any]:
    path = root / "model.pkl"
    model.save(str(path), serialization="pickle", save_embedding_model=False)
    loaded = rt.BERTopic.load(str(path))
    check_topic_count(loaded, len(data.docs), "pickle load")

    predicted, probabilities = loaded.transform(data.docs[:3], embeddings=data.embeddings[:3])
    assert len(predicted) == 3, "pickle-loaded transform returned the wrong number of predictions"

    return {
        "path_kind": "local_file",
        "exists": path.is_file(),
        "count_sum": int(loaded.get_topic_info().Count.sum()),
        "loaded_clusterer": type(loaded.hdbscan_model).__name__,
        "loaded_reducer": type(loaded.umap_model).__name__,
        "transform_predictions": [int(topic) for topic in predicted],
        "transform_probabilities_is_none": probabilities is None,
    }


def choose_light_format(requested: str) -> str | None:
    if requested == "none":
        return None
    if requested == "auto":
        if module_available("safetensors"):
            return "safetensors"
        if module_available("torch"):
            return "pytorch"
        return None
    if requested == "safetensors" and not module_available("safetensors"):
        raise SystemExit("Requested --light-format safetensors, but safetensors is not importable.")
    if requested == "pytorch" and not module_available("torch"):
        raise SystemExit("Requested --light-format pytorch, but torch is not importable.")
    return requested


def expected_light_files(fmt: str) -> list[str]:
    if fmt == "safetensors":
        return ["config.json", "topics.json", "topic_embeddings.safetensors", "ctfidf.safetensors", "ctfidf_config.json"]
    if fmt == "pytorch":
        return ["config.json", "topics.json", "topic_embeddings.bin", "ctfidf.bin", "ctfidf_config.json"]
    raise ValueError(f"Unknown light format: {fmt}")


def run_light_roundtrip(rt: Runtime, model: Any, data: SmokeData, root: Path, fmt: str) -> dict[str, Any]:
    directory = root / f"model_{fmt}"
    model.save(str(directory), serialization=fmt, save_ctfidf=True, save_embedding_model=False)

    expected = expected_light_files(fmt)
    missing = [name for name in expected if not (directory / name).is_file()]
    assert not missing, f"{fmt} save is missing expected files: {missing}"

    loaded_without_backend = rt.BERTopic.load(str(directory))
    check_topic_count(loaded_without_backend, len(data.docs), f"{fmt} load without backend")

    loaded_with_backend = rt.BERTopic.load(str(directory), embedding_model=rt.BaseEmbedder())
    check_topic_count(loaded_with_backend, len(data.docs), f"{fmt} load with explicit backend")
    assert loaded_with_backend.c_tf_idf_ is not None, "save_ctfidf=True did not restore c_tf_idf_"

    predicted, probabilities = loaded_with_backend.transform(data.docs[:3], embeddings=data.embeddings[:3])
    assert len(predicted) == 3, f"{fmt}-loaded transform returned the wrong number of predictions"

    return {
        "path_kind": "local_directory",
        "format": fmt,
        "files": sorted(path.name for path in directory.iterdir()),
        "expected_files_present": expected,
        "count_sum_without_backend": int(loaded_without_backend.get_topic_info().Count.sum()),
        "count_sum_with_backend": int(loaded_with_backend.get_topic_info().Count.sum()),
        "loaded_clusterer": type(loaded_with_backend.hdbscan_model).__name__,
        "loaded_reducer": type(loaded_with_backend.umap_model).__name__,
        "ctfidf_restored": loaded_with_backend.c_tf_idf_ is not None,
        "transform_predictions": [int(topic) for topic in predicted],
        "transform_probabilities_is_none": probabilities is None,
    }


def hub_guidance_summary() -> dict[str, Any]:
    return {
        "network_calls_performed": False,
        "local_save_load_requires_credentials": False,
        "push_to_hf_hub_requires": ["huggingface_hub", "network", "write token or prior login"],
        "load_public_hub_repo_requires": ["huggingface_hub", "network", "repo id shaped as namespace/repo"],
        "private_hub_repo_adds_requirement": "valid token with read permission",
        "huggingface_hub_importable": module_available("huggingface_hub"),
    }


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--light-format",
        choices=["auto", "safetensors", "pytorch", "none"],
        default="auto",
        help="Lightweight local format to test. Default prefers safetensors, then pytorch.",
    )
    args = parser.parse_args()

    rt = require_runtime()
    data = make_synthetic_data(rt.np)
    with tempfile.TemporaryDirectory(prefix="bertopic-serialization-smoke-") as tmp:
        tmpdir = Path(tmp)
        model, fit_summary = fit_tiny_model(rt, data)
        light_format = choose_light_format(args.light_format)

        summary: dict[str, Any] = {
            "fit": fit_summary,
            "pickle": run_pickle_roundtrip(rt, model, data, tmpdir),
            "lightweight": None,
            "hub_guidance": hub_guidance_summary(),
        }

        if light_format is None:
            summary["lightweight"] = {
                "skipped": True,
                "reason": "No lightweight tensor dependency selected or available.",
            }
        else:
            summary["lightweight"] = run_light_roundtrip(rt, model, data, tmpdir, light_format)

    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
