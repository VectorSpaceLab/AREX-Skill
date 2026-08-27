#!/usr/bin/env python3
"""Safe textgenrnn embedding/similarity smoke helper.

The helper intentionally disables PCA and t-SNE by default so it can run on a
small text list. Use --pca-dims or --tsne-dims only when the sample count is
large enough for the requested reduction.
"""

from __future__ import annotations

import argparse
import sys
from typing import Iterable, Optional


DEFAULT_TEXTS = [
    "Never gonna give you up, never gonna let you down",
    "Never gonna run around and desert you",
    "Never gonna make you cry, never gonna say goodbye",
    "Never gonna tell a lie and hurt you",
]


def positive_int(value: str) -> int:
    try:
        parsed = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(f"expected an integer, got {value!r}") from exc
    if parsed <= 0:
        raise argparse.ArgumentTypeError("expected a positive integer")
    return parsed


def optional_positive_int(value: str) -> Optional[int]:
    if value.lower() in {"none", "null", "raw", "off"}:
        return None
    return positive_int(value)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Encode sample texts with textgenrnn.encode_text_vectors and print "
            "vector shape plus nearest-text similarity rankings."
        )
    )
    parser.add_argument(
        "--texts",
        action="append",
        default=None,
        help=(
            "Text to encode. Repeat for multiple texts. Defaults to a small "
            "four-line fixture."
        ),
    )
    parser.add_argument(
        "--pca-dims",
        type=optional_positive_int,
        default=None,
        metavar="N|none",
        help=(
            "PCA dimensions for encode_text_vectors. Default is none/raw; use "
            "N only when N <= min(number of texts, raw vector width)."
        ),
    )
    parser.add_argument(
        "--tsne-dims",
        type=positive_int,
        default=None,
        metavar="N",
        help=(
            "Optional t-SNE output dimensions, usually 2 or 3. Requires enough "
            "texts for scikit-learn t-SNE perplexity."
        ),
    )
    parser.add_argument(
        "--tsne-seed",
        type=int,
        default=123,
        help="Random seed passed to t-SNE when --tsne-dims is used. Default: 123.",
    )
    parser.add_argument(
        "--similarity-query",
        default=None,
        help="Query string for similarity ranking. Default: the first encoded text.",
    )
    parser.add_argument(
        "--use-pca",
        action="store_true",
        help=(
            "Use textgenrnn.similarity(..., use_pca=True). Default is raw-vector "
            "similarity, which is safer for small candidate lists."
        ),
    )
    parser.add_argument(
        "--top-k",
        type=positive_int,
        default=3,
        help="Number of similarity pairs to print. Default: 3.",
    )
    return parser


def load_textgenrnn_class():
    try:
        from textgenrnn import textgenrnn  # type: ignore
    except Exception as exc:  # pragma: no cover - depends on user environment
        print("ERROR: could not import textgenrnn.", file=sys.stderr)
        print(f"Cause: {exc}", file=sys.stderr)
        print(
            "Hint: run inside an environment with textgenrnn installed, a "
            "pre-Keras-3 TensorFlow stack such as 2.15.x, and pkg_resources "
            "available from setuptools.",
            file=sys.stderr,
        )
        raise SystemExit(2) from exc
    return textgenrnn


def print_hints(exc: BaseException, *, phase: str, text_count: int, pca_dims: Optional[int]) -> None:
    message = str(exc)
    lowered = message.lower()
    print(f"ERROR during {phase}: {message}", file=sys.stderr)

    hints = []
    if "must use more than 1 text" in lowered:
        hints.append("PCA cannot be fit on one text; rerun with --pca-dims none.")
    if "n_components" in lowered or "pca" in lowered:
        hints.append(
            "PCA dimensions must be small enough for the sample count; use "
            "--pca-dims none or choose N <= min(number of texts, raw vector width)."
        )
    if "perplexity" in lowered or "tsne" in lowered or "t-sne" in lowered:
        hints.append(
            "t-SNE needs enough texts for its perplexity; omit --tsne-dims for "
            "smoke tests or provide a much larger text list."
        )
    if "tensorflow.compat.v1.keras" in lowered:
        hints.append("Use a pre-Keras-3 TensorFlow/Keras stack, such as TensorFlow 2.15.x.")
    if "pkg_resources" in lowered:
        hints.append("Install/pin setuptools so pkg_resources is available, for example setuptools<81.")
    if phase == "similarity" and pca_dims is None:
        hints.append("If --use-pca caused this, rerun without --use-pca for a small candidate list.")

    hints.append(f"Current text count: {text_count}; requested pca_dims: {pca_dims!r}.")
    for hint in dict.fromkeys(hints):
        print(f"Hint: {hint}", file=sys.stderr)


def summarize_texts(texts: Iterable[str]) -> None:
    texts = list(texts)
    print(f"texts: {len(texts)}")
    for idx, text in enumerate(texts[:5], start=1):
        snippet = text.replace("\n", " ")[:80]
        print(f"  {idx}. {snippet}")
    if len(texts) > 5:
        print(f"  ... {len(texts) - 5} more")


def main(argv: Optional[list[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    texts = args.texts if args.texts is not None else list(DEFAULT_TEXTS)
    if not texts:
        print("ERROR: at least one text is required.", file=sys.stderr)
        return 2

    summarize_texts(texts)
    textgenrnn = load_textgenrnn_class()
    textgen = textgenrnn()

    try:
        vectors = textgen.encode_text_vectors(
            texts,
            pca_dims=args.pca_dims,
            tsne_dims=args.tsne_dims,
            tsne_seed=args.tsne_seed if args.tsne_dims is not None else None,
        )
    except Exception as exc:  # pragma: no cover - environment/data dependent
        print_hints(exc, phase="encoding", text_count=len(texts), pca_dims=args.pca_dims)
        return 3

    shape = getattr(vectors, "shape", None)
    print(f"encoded_shape: {shape}")
    if shape is not None and len(shape) == 2:
        print(f"rows_match_texts: {shape[0] == len(texts)}")

    query = args.similarity_query if args.similarity_query is not None else texts[0]
    try:
        pairs = textgen.similarity(query, texts, use_pca=args.use_pca)
    except Exception as exc:  # pragma: no cover - environment/data dependent
        print_hints(exc, phase="similarity", text_count=len(texts), pca_dims=args.pca_dims)
        return 4

    print(f"similarity_query: {query}")
    print(f"similarity_use_pca: {args.use_pca}")
    print("top_similarity_pairs:")
    for candidate, score in pairs[: args.top_k]:
        print(f"  {float(score): .6f}\t{candidate}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
