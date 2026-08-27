#!/usr/bin/env python3
"""Smoke-test dense SentenceTransformer embeddings without default network access."""

from __future__ import annotations

import argparse
import sys
from typing import Sequence


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Encode a few sentences with a user-supplied SentenceTransformer model and "
            "print embedding and similarity diagnostics. No model is loaded unless --model is provided."
        )
    )
    parser.add_argument(
        "--model",
        help="Model id or local model directory. Required for execution; omitted --help is safe and network-free.",
    )
    parser.add_argument(
        "--sentences",
        nargs="+",
        default=[
            "This framework generates embeddings for each input sentence.",
            "Sentence Transformers creates dense vector representations.",
            "The quick brown fox jumps over the lazy dog.",
        ],
        help="Sentences to encode. Provide at least one string.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Only load local files or cached model artifacts; do not download from the Hub.",
    )
    parser.add_argument(
        "--normalize",
        action="store_true",
        help="Return unit-normalized embeddings, useful for dot-product retrieval checks.",
    )
    parser.add_argument(
        "--precision",
        choices=["float32", "int8", "uint8", "binary", "ubinary"],
        default="float32",
        help="Embedding precision passed to SentenceTransformer.encode.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for encoding.",
    )
    parser.add_argument(
        "--truncate-dim",
        type=int,
        default=None,
        help="Optional embedding dimension truncation.",
    )
    parser.add_argument(
        "--device",
        default=None,
        help="Optional device string such as cpu, cuda, or mps.",
    )
    parser.add_argument(
        "--similarity",
        choices=["cosine", "dot", "euclidean", "manhattan"],
        default=None,
        help="Optional similarity function name to configure before scoring.",
    )
    return parser.parse_args(argv)


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)
    if not args.model:
        print("error: --model is required for execution; use --help for usage.", file=sys.stderr)
        return 2
    if not args.sentences:
        print("error: provide at least one sentence via --sentences.", file=sys.stderr)
        return 2
    if args.batch_size < 1:
        print("error: --batch-size must be >= 1.", file=sys.stderr)
        return 2
    if args.truncate_dim is not None and args.truncate_dim < 1:
        print("error: --truncate-dim must be >= 1 when provided.", file=sys.stderr)
        return 2

    try:
        import numpy as np
        from sentence_transformers import SentenceTransformer
    except Exception as exc:  # pragma: no cover - depends on user environment
        print(f"error: failed to import runtime dependencies: {exc}", file=sys.stderr)
        return 1

    try:
        model = SentenceTransformer(
            args.model,
            device=args.device,
            local_files_only=args.local_files_only,
            similarity_fn_name=args.similarity,
        )
        embeddings = model.encode(
            args.sentences,
            batch_size=args.batch_size,
            precision=args.precision,
            convert_to_numpy=True,
            normalize_embeddings=args.normalize,
            truncate_dim=args.truncate_dim,
            show_progress_bar=False,
        )
    except Exception as exc:  # pragma: no cover - model/backend dependent
        print(f"error: embedding smoke test failed: {exc}", file=sys.stderr)
        return 1

    embeddings = np.asarray(embeddings)
    expected_rows = len(args.sentences)
    if embeddings.ndim == 1:
        embeddings = embeddings.reshape(1, -1)
    if embeddings.shape[0] != expected_rows:
        print(f"error: expected {expected_rows} embedding rows, got {embeddings.shape[0]}", file=sys.stderr)
        return 1
    if not np.all(np.isfinite(embeddings.astype(np.float32, copy=False))):
        print("error: embeddings contain non-finite values.", file=sys.stderr)
        return 1

    similarities = model.similarity(embeddings, embeddings)
    norms = np.linalg.norm(embeddings.astype(np.float32, copy=False), axis=1)

    print(f"model: {args.model}")
    print(f"sentences: {expected_rows}")
    print(f"embedding_shape: {tuple(embeddings.shape)}")
    print(f"embedding_dtype: {embeddings.dtype}")
    print(f"similarity_shape: {tuple(similarities.shape)}")
    print(f"similarity_fn_name: {model.similarity_fn_name}")
    print(f"norm_min_max: ({norms.min():.6f}, {norms.max():.6f})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
