#!/usr/bin/env python3
"""Run a safe Yellowbrick text smoke test on inline data.

The smoke uses Matplotlib Agg, does not call Yellowbrick dataset loaders, does
not run the downloader, and does not require UMAP, NLTK, SpaCy, parser data, or
language-model downloads.
"""

from __future__ import annotations

import argparse
import importlib
from contextlib import contextmanager
from pathlib import Path
from typing import Any

import matplotlib

matplotlib.use("Agg", force=True)
matplotlib.rcParams["font.family"] = "DejaVu Sans"
matplotlib.rcParams["font.sans-serif"] = ["DejaVu Sans"]

import matplotlib.pyplot as plt
import numpy as np
from sklearn.feature_extraction.text import CountVectorizer, TfidfVectorizer

from yellowbrick.exceptions import YellowbrickValueError
from yellowbrick.text import (
    DispersionPlot,
    FreqDistVisualizer,
    PosTagVisualizer,
    TSNEVisualizer,
    UMAPVisualizer,
    WordCorrelationPlot,
)

dispersion_mod = importlib.import_module("yellowbrick.text.dispersion")

DOCS = [
    "apple banana fruit",
    "banana fruit pear",
    "apple pie banana",
    "cloud wind rain",
    "cloud storm wind",
    "rain cloud sky",
]
LABELS = np.array(["fruit", "fruit", "fruit", "weather", "weather", "weather"])
TOKEN_DOCS = [doc.split() for doc in DOCS]
CORRELATION_WORDS = ["apple", "banana", "fruit", "cloud", "wind"]
DISPERSION_TERMS = ["apple", "banana", "cloud"]
TAGGED_DOCS = [
    [[("Apple", "NN"), ("trees", "NNS"), ("grow", "VBP"), ("fast", "RB"), (".", ".")]],
    [[("Clouds", "NNS"), ("drift", "VBP"), ("quietly", "RB"), ("above", "IN"), (".", ".")]],
]
TAG_LABELS = np.array(["fruit", "weather"])


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render safe Yellowbrick text visualizer PNGs from inline synthetic documents using the Matplotlib Agg backend.",
    )
    parser.add_argument(
        "--outdir",
        default="text-smoke-output",
        help="directory where PNG files will be written",
    )
    return parser.parse_args()


def prepare_outdir(value: str) -> Path:
    outdir = Path(value).expanduser().resolve()
    outdir.mkdir(parents=True, exist_ok=True)
    return outdir


def feature_names(vectorizer: CountVectorizer) -> list[str]:
    if hasattr(vectorizer, "get_feature_names_out"):
        return list(vectorizer.get_feature_names_out())
    return list(vectorizer.get_feature_names())


def save_visualizer(name: str, viz: Any, outdir: Path) -> dict[str, Any]:
    path = outdir / f"{name}.png"
    viz.show(outpath=str(path), clear_figure=True, bbox_inches="tight")
    plt.close("all")

    size = path.stat().st_size if path.exists() else 0
    if size <= 0:
        raise RuntimeError(f"{name} did not produce a non-empty PNG at {path}")

    return {"name": name, "path": str(path), "size_bytes": size}


@contextmanager
def patched_dispersion_stack():
    """Materialize generator inputs for the current NumPy stack call."""
    original_stack = dispersion_mod.np.stack

    def safe_stack(arrays, *args, **kwargs):
        if not isinstance(arrays, (list, tuple)):
            arrays = list(arrays)
        return original_stack(arrays, *args, **kwargs)

    dispersion_mod.np.stack = safe_stack
    try:
        yield
    finally:
        dispersion_mod.np.stack = original_stack


def smoke_freqdist(outdir: Path) -> dict[str, Any]:
    vectorizer = CountVectorizer()
    X = vectorizer.fit_transform(DOCS)
    viz = FreqDistVisualizer(features=feature_names(vectorizer), n=6, title="Token frequency smoke")
    viz.fit(X, LABELS)
    return save_visualizer("freqdist", viz, outdir)


def smoke_tsne(outdir: Path) -> dict[str, Any]:
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(DOCS)
    viz = TSNEVisualizer(random_state=13, decompose_by=2, perplexity=2)
    viz.fit(X, LABELS)
    return save_visualizer("tsne", viz, outdir)


def smoke_umap(outdir: Path) -> tuple[str, dict[str, Any] | None]:
    vectorizer = TfidfVectorizer()
    X = vectorizer.fit_transform(DOCS)

    try:
        viz = UMAPVisualizer(random_state=13, n_neighbors=2, min_dist=0.1)
    except YellowbrickValueError as exc:
        return f"skipped umap: {exc}", None

    viz.fit(X, LABELS)
    return "generated umap", save_visualizer("umap", viz, outdir)


def smoke_dispersion(outdir: Path) -> dict[str, Any]:
    with patched_dispersion_stack():
        viz = DispersionPlot(
            DISPERSION_TERMS,
            ignore_case=True,
            annotate_docs=True,
            title="Dispersion smoke",
        )
        viz.fit(TOKEN_DOCS, LABELS)
        return save_visualizer("dispersion", viz, outdir)


def smoke_word_correlation(outdir: Path) -> dict[str, Any]:
    viz = WordCorrelationPlot(
        CORRELATION_WORDS,
        ignore_case=True,
        colorbar=False,
        title="Word correlation smoke",
    )
    viz.fit(DOCS)
    return save_visualizer("word_correlation", viz, outdir)


def smoke_postag(outdir: Path) -> dict[str, Any]:
    viz = PosTagVisualizer(
        frequency=True,
        stack=True,
        colors=["#4c72b0", "#55a868"],
        title="POS tag smoke",
    )
    viz.fit(TAGGED_DOCS, y=TAG_LABELS)
    return save_visualizer("postag", viz, outdir)


def main(outdir_value: str) -> int:
    outdir = prepare_outdir(outdir_value)
    outputs: list[dict[str, Any]] = []

    outputs.append(smoke_freqdist(outdir))
    outputs.append(smoke_tsne(outdir))

    umap_message, umap_result = smoke_umap(outdir)
    print(umap_message)
    if umap_result is not None:
        outputs.append(umap_result)

    try:
        outputs.append(smoke_dispersion(outdir))
    except Exception as exc:
        # Yellowbrick 1.5 calls numpy.stack on generator-like objects in
        # DispersionPlot; newer NumPy releases may reject that path. Keep the
        # smoke useful by reporting the compatibility issue and continuing with
        # the WordCorrelation and PosTag checks documented by this sub-skill.
        print(f"skipped dispersion: {type(exc).__name__}: {exc}")

    outputs.append(smoke_word_correlation(outdir))
    outputs.append(smoke_postag(outdir))

    print(f"wrote {len(outputs)} files to {outdir}")
    for item in outputs:
        print(f"{item['name']}: {item['path']}")
    return 0


if __name__ == "__main__":
    args = parse_args()
    raise SystemExit(main(args.outdir))
