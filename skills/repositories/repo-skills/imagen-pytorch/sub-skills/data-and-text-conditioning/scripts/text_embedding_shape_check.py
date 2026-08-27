#!/usr/bin/env python3
"""Check Imagen-Pytorch text-embedding metadata without loading T5.

This script validates shape contracts for precomputed text embeddings and masks
from CLI arguments only. It performs no network access and loads no models.
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from dataclasses import dataclass

DEFAULT_MAX_TEXT_LEN = 256
DEFAULT_T5_NAME = "google/t5-v1_1-base"


@dataclass(frozen=True)
class ShapeCheckResult:
    ok: bool
    warnings: list[str]
    errors: list[str]
    summary: dict


def parse_shape(raw: str | None) -> tuple[int, ...] | None:
    if raw is None:
        return None
    cleaned = raw.strip()
    if not cleaned:
        return None
    parts = [part for part in re.split(r"[xX,\s]+", cleaned) if part]
    try:
        dims = tuple(int(part) for part in parts)
    except ValueError as exc:  # pragma: no cover - guarded by CLI use
        raise argparse.ArgumentTypeError(f"invalid shape value: {raw}") from exc
    if any(dim <= 0 for dim in dims):
        raise argparse.ArgumentTypeError(f"shape dimensions must be positive: {raw}")
    return dims


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check text-embedding and text-mask shapes for Imagen-Pytorch.")
    parser.add_argument(
        "--text-embeds-shape",
        required=True,
        type=parse_shape,
        help="Embedding shape as batch,seq,dim or batchxseqxdim",
    )
    parser.add_argument(
        "--text-masks-shape",
        type=parse_shape,
        default=None,
        help="Mask shape as batch,seq or batchxseq",
    )
    parser.add_argument(
        "--expected-batch-size",
        type=int,
        default=None,
        help="Optional batch size that the embeddings must match",
    )
    parser.add_argument(
        "--expected-embed-dim",
        type=int,
        default=None,
        help="Optional embedding width that the embeddings must match",
    )
    parser.add_argument(
        "--max-text-len",
        type=int,
        default=DEFAULT_MAX_TEXT_LEN,
        help="Maximum allowed token length before truncation",
    )
    parser.add_argument(
        "--require-mask",
        action="store_true",
        help="Fail if no text mask shape is supplied",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of human-readable text",
    )
    return parser.parse_args(argv)


def check_shapes(args: argparse.Namespace) -> ShapeCheckResult:
    embeds = args.text_embeds_shape
    masks = args.text_masks_shape

    warnings: list[str] = []
    errors: list[str] = []

    if len(embeds) != 3:
        errors.append(f"text_embeds must be rank-3, got shape {embeds}")
        batch = seq_len = embed_dim = None
    else:
        batch, seq_len, embed_dim = embeds

    if args.expected_batch_size is not None and batch is not None and batch != args.expected_batch_size:
        errors.append(f"batch size mismatch: expected {args.expected_batch_size}, got {batch}")

    if args.expected_embed_dim is not None and embed_dim is not None and embed_dim != args.expected_embed_dim:
        errors.append(f"embedding dim mismatch: expected {args.expected_embed_dim}, got {embed_dim}")

    if seq_len is not None and seq_len > args.max_text_len:
        errors.append(f"sequence length {seq_len} exceeds max_text_len {args.max_text_len}")

    if masks is None:
        if args.require_mask:
            errors.append("text_masks shape was required but not supplied")
        else:
            warnings.append("text_masks shape not supplied; the model will infer masks only if embeddings are zero-padded")
    else:
        if len(masks) != 2:
            errors.append(f"text_masks must be rank-2, got shape {masks}")
        elif batch is not None and masks[0] != batch:
            errors.append(f"mask batch mismatch: expected {batch}, got {masks[0]}")
        elif seq_len is not None and masks[1] != seq_len:
            errors.append(f"mask length mismatch: expected {seq_len}, got {masks[1]}")

    summary = {
        "default_t5_name": DEFAULT_T5_NAME,
        "max_text_len": args.max_text_len,
        "text_embeds_shape": embeds,
        "text_masks_shape": masks,
        "expected_batch_size": args.expected_batch_size,
        "expected_embed_dim": args.expected_embed_dim,
    }
    return ShapeCheckResult(ok=not errors, warnings=warnings, errors=errors, summary=summary)


def print_human(result: ShapeCheckResult) -> None:
    print(f"default T5 name: {result.summary['default_t5_name']}")
    print(f"max text length: {result.summary['max_text_len']}")
    print(f"text_embeds_shape: {result.summary['text_embeds_shape']}")
    print(f"text_masks_shape: {result.summary['text_masks_shape']}")
    if result.summary["expected_batch_size"] is not None:
        print(f"expected batch size: {result.summary['expected_batch_size']}")
    if result.summary["expected_embed_dim"] is not None:
        print(f"expected embed dim: {result.summary['expected_embed_dim']}")
    if result.warnings:
        print("warnings:")
        for warning in result.warnings:
            print(f"  - {warning}")
    if result.errors:
        print("errors:")
        for error in result.errors:
            print(f"  - {error}")
    else:
        print("shape check: ok")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    result = check_shapes(args)

    if args.json:
        print(json.dumps({**result.summary, "warnings": result.warnings, "errors": result.errors, "ok": result.ok}, indent=2, sort_keys=True, default=list))
    else:
        print_human(result)

    return 0 if result.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
