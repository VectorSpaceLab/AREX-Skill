#!/usr/bin/env python3
"""Smoke-test SparseEncoder embeddings, sparsity, and decoded token weights."""

from __future__ import annotations

import argparse
import sys
from collections.abc import Sequence


def parse_args(argv: Sequence[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Encode sentences with sentence-transformers SparseEncoder and print sparse diagnostics.",
    )
    parser.add_argument(
        "--model",
        default="naver/splade-cocondenser-ensembledistil",
        help="SparseEncoder model id or local model directory.",
    )
    parser.add_argument(
        "--sentences",
        nargs="+",
        default=[
            "This framework generates sparse embeddings for input text.",
            "The quick brown fox jumps over the lazy dog.",
            "Search systems can combine lexical and semantic retrieval.",
        ],
        help="One or more sentences to encode.",
    )
    parser.add_argument(
        "--max-active-dims",
        type=int,
        default=None,
        help="Optional cap for non-zero dimensions per embedding.",
    )
    parser.add_argument(
        "--top-k",
        type=int,
        default=10,
        help="Number of decoded token weights to print per sentence.",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=32,
        help="Batch size for SparseEncoder.encode.",
    )
    parser.add_argument(
        "--local-files-only",
        action="store_true",
        help="Only load model files already available locally; do not download from the Hub.",
    )
    parser.add_argument(
        "--dense-output",
        action="store_true",
        help="Return dense tensors instead of sparse COO tensors for comparison/debugging.",
    )
    return parser.parse_args(argv)


def tensor_memory_kb(tensor) -> float:
    if getattr(tensor, "is_sparse", False):
        tensor = tensor.coalesce()
        values_bytes = tensor.values().element_size() * tensor.values().nelement()
        indices_bytes = tensor.indices().element_size() * tensor.indices().nelement()
        return (values_bytes + indices_bytes) / 1024
    return tensor.element_size() * tensor.nelement() / 1024


def main(argv: Sequence[str] | None = None) -> int:
    args = parse_args(argv)

    if args.max_active_dims is not None and args.max_active_dims <= 0:
        print("--max-active-dims must be a positive integer", file=sys.stderr)
        return 2
    if args.top_k <= 0:
        print("--top-k must be a positive integer", file=sys.stderr)
        return 2
    if args.batch_size <= 0:
        print("--batch-size must be a positive integer", file=sys.stderr)
        return 2

    try:
        from sentence_transformers import SparseEncoder
    except ImportError as exc:
        print("Could not import sentence_transformers. Install with: pip install -U sentence-transformers", file=sys.stderr)
        print(str(exc), file=sys.stderr)
        return 1

    try:
        model = SparseEncoder(args.model, local_files_only=args.local_files_only)
        embeddings = model.encode(
            args.sentences,
            batch_size=args.batch_size,
            convert_to_tensor=True,
            convert_to_sparse_tensor=not args.dense_output,
            save_to_cpu=True,
            max_active_dims=args.max_active_dims,
            show_progress_bar=False,
        )
    except Exception as exc:
        print(f"SparseEncoder smoke run failed: {exc}", file=sys.stderr)
        if args.local_files_only:
            print("The model may not be cached locally; retry without --local-files-only only if downloads are allowed.", file=sys.stderr)
        return 1

    print(f"Model: {args.model}")
    print(f"Sentences: {len(args.sentences)}")
    print(f"Embedding shape: {tuple(embeddings.shape)}")
    print(f"Sparse tensor: {getattr(embeddings, 'is_sparse', False)}")
    print(f"Similarity function: {model.similarity_fn_name}")
    print(f"Approx embedding memory: {tensor_memory_kb(embeddings):.2f} KiB")

    stats = model.sparsity(embeddings)
    print(f"Average active dimensions: {stats['active_dims']:.2f}")
    print(f"Sparsity ratio: {stats['sparsity_ratio']:.4%}")

    try:
        similarities = model.similarity(embeddings, embeddings).cpu()
        print("Similarity matrix:")
        for row in similarities.tolist():
            print("  " + " ".join(f"{score:8.3f}" for score in row))
    except Exception as exc:
        print(f"Could not compute similarity: {exc}", file=sys.stderr)

    try:
        decoded = model.decode(embeddings, top_k=args.top_k)
        if len(args.sentences) == 1 and decoded and isinstance(decoded[0], tuple):
            decoded = [decoded]
        print(f"Top decoded token weights (top_k={args.top_k}):")
        for index, sentence in enumerate(args.sentences):
            token_scores = decoded[index] if index < len(decoded) else []
            formatted = ", ".join(f"{token.strip() or repr(token)}:{weight:.2f}" for token, weight in token_scores)
            print(f"  {index}: {sentence}")
            print(f"     {formatted}")
    except Exception as exc:
        print(f"Could not decode token weights: {exc}", file=sys.stderr)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
