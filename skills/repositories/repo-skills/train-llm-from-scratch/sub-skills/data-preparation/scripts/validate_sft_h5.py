#!/usr/bin/env python3
"""Validate packed SFT HDF5 data without requiring the source repository.

Expected schema: two aligned datasets, ``tokens`` and ``loss_mask``, both shape
``(rows, context_length)``. ``loss_mask`` must be binary and non-degenerate: it
should train assistant completion tokens, not all prompt tokens and not nothing.
"""

from __future__ import annotations

import argparse
import json
import sys
import tempfile
from pathlib import Path


def _positive_int(value: str) -> int:
    try:
        out = int(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if out <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return out


def _fraction(value: str) -> float:
    try:
        out = float(value)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if not 0.0 <= out <= 1.0:
        raise argparse.ArgumentTypeError("must be in [0, 1]")
    return out


def _require_deps():
    try:
        import h5py
        import numpy as np
    except ModuleNotFoundError as exc:
        raise SystemExit(f"missing dependency: {exc.name}. Install h5py and numpy to validate SFT HDF5 files.") from exc
    return h5py, np


def _fail(message: str) -> None:
    raise SystemExit(f"VALIDATION FAILED: {message}")


def validate(args: argparse.Namespace) -> dict:
    h5py, np = _require_deps()
    path = Path(args.path)
    if not path.exists():
        _fail(f"file not found: {path}")

    with h5py.File(path, "r") as h5:
        missing = [name for name in (args.tokens_dataset, args.mask_dataset) if name not in h5]
        if missing:
            keys = ", ".join(sorted(h5.keys())) or "<none>"
            _fail(f"missing dataset(s) {missing}; available top-level keys: {keys}")

        tokens = h5[args.tokens_dataset]
        masks = h5[args.mask_dataset]
        token_shape = tuple(int(x) for x in tokens.shape)
        mask_shape = tuple(int(x) for x in masks.shape)
        if token_shape != mask_shape:
            _fail(f"tokens shape {token_shape} != loss_mask shape {mask_shape}")
        if len(token_shape) != 2:
            _fail(f"packed SFT datasets must be 2-D (rows, context_length); got {token_shape}")
        rows, width = token_shape
        if rows <= 0:
            _fail("packed SFT file has zero rows")
        if args.context_length is not None and width != args.context_length:
            _fail(f"context length mismatch: file width {width}, expected {args.context_length}")

        sample_rows = min(rows, args.max_rows)
        total = 0
        trained = 0
        min_token = None
        max_token = None
        non_binary_values: set[int] = set()
        rows_with_training = 0
        rows_all_training = 0
        high_token_count = 0
        negative_count = 0

        for start in range(0, sample_rows, args.chunk_rows):
            end = min(sample_rows, start + args.chunk_rows)
            tk = np.asarray(tokens[start:end])
            mk = np.asarray(masks[start:end])
            if tk.shape != mk.shape:
                _fail(f"chunk shape mismatch at rows {start}:{end}: {tk.shape} vs {mk.shape}")
            if tk.size == 0:
                continue
            total += int(tk.size)
            trained += int(mk.sum())
            t_min = int(tk.min())
            t_max = int(tk.max())
            min_token = t_min if min_token is None else min(min_token, t_min)
            max_token = t_max if max_token is None else max(max_token, t_max)
            unique_mask = set(int(x) for x in np.unique(mk).tolist())
            non_binary_values.update(x for x in unique_mask if x not in (0, 1))
            rows_with_training += int((mk.sum(axis=1) > 0).sum())
            rows_all_training += int((mk.sum(axis=1) == mk.shape[1]).sum())
            high_token_count += int((tk > args.max_token_id).sum())
            negative_count += int((tk < 0).sum())

        if non_binary_values:
            _fail(f"loss_mask contains values outside {{0,1}} in sampled rows: {sorted(non_binary_values)}")
        if negative_count:
            _fail(f"found {negative_count} negative token ids in sampled rows")
        if high_token_count:
            _fail(f"found {high_token_count} token ids above max-token-id {args.max_token_id} in sampled rows")
        if total == 0:
            _fail("no tokens sampled")

        trained_fraction = trained / total
        if trained <= 0:
            _fail("loss_mask trains zero tokens in sampled rows")
        if trained == total:
            _fail("loss_mask is all ones in sampled rows; prompt tokens are probably being trained")
        if trained_fraction < args.min_trained_fraction:
            _fail(f"trained fraction {trained_fraction:.6f} is below minimum {args.min_trained_fraction:.6f}")
        if trained_fraction > args.max_trained_fraction:
            _fail(f"trained fraction {trained_fraction:.6f} is above maximum {args.max_trained_fraction:.6f}")

        summary = {
            "path": str(path),
            "tokens_dataset": args.tokens_dataset,
            "mask_dataset": args.mask_dataset,
            "shape": token_shape,
            "tokens_dtype": str(tokens.dtype),
            "loss_mask_dtype": str(masks.dtype),
            "sampled_rows": int(sample_rows),
            "sampled_tokens": int(total),
            "sample_min_token": min_token,
            "sample_max_token": max_token,
            "max_token_id": int(args.max_token_id),
            "trained_tokens_in_sample": int(trained),
            "trained_fraction_in_sample": trained_fraction,
            "rows_with_any_training_in_sample": int(rows_with_training),
            "rows_all_training_in_sample": int(rows_all_training),
        }
        if max_token is not None and max_token > args.warn_tokenizer_max:
            summary["warning"] = (
                f"sample max token {max_token} exceeds tokenizer data max {args.warn_tokenizer_max}; "
                "this may be invalid for raw r50k_base-prepared data even if it is within model vocab"
            )
    return summary


def make_fixture(path: Path, *, bad: str | None = None) -> None:
    h5py, np = _require_deps()
    path.parent.mkdir(parents=True, exist_ok=True)
    token_rows = [
        [27, 91, 7220, 91, 29, 198, 2061, 318, 362, 10, 17, 30, 50256, 27, 91, 562, 10167],
        [91, 29, 198, 27, 29, 41484, 29, 19, 3556, 29, 50256, 0, 0, 0, 0, 0],
    ]
    tokens = np.asarray([row[:16] for row in token_rows], dtype=np.int32)
    masks = np.asarray(
        [
            [0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0],
            [0, 0, 0, 0, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0],
        ],
        dtype=np.int8,
    )
    if bad == "zeros":
        masks[:] = 0
    elif bad == "ones":
        masks[:] = 1
    elif bad == "nonbinary":
        masks[0, 0] = 2
    elif bad == "range":
        tokens[0, 0] = 999999
    with h5py.File(path, "w") as h5:
        h5.create_dataset("tokens", data=tokens)
        h5.create_dataset("loss_mask", data=masks)


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        good = Path(td) / "sft.h5"
        make_fixture(good)
        args = build_parser().parse_args([str(good), "--context-length", "16"])
        summary = validate(args)
        assert summary["shape"] == (2, 16)
        assert 0.0 < summary["trained_fraction_in_sample"] < 1.0

        bad = Path(td) / "bad_zeros.h5"
        make_fixture(bad, bad="zeros")
        args = build_parser().parse_args([str(bad)])
        try:
            validate(args)
        except SystemExit as exc:
            assert "zero tokens" in str(exc)
        else:  # pragma: no cover
            raise AssertionError("zero-mask fixture should fail")
    print("SELF TEST PASSED")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Validate packed SFT HDF5 tokens/loss_mask schema and mask health.")
    p.add_argument("path", nargs="?", help="Packed SFT HDF5 file")
    p.add_argument("--tokens-dataset", default="tokens", help="Token dataset name")
    p.add_argument("--mask-dataset", default="loss_mask", help="Loss-mask dataset name")
    p.add_argument("--context-length", type=_positive_int, default=None, help="Require this row width")
    p.add_argument("--max-token-id", type=int, default=50303, help="Fail if any sampled token id exceeds this model-vocab max")
    p.add_argument("--warn-tokenizer-max", type=int, default=50256, help="Warn when sampled ids exceed this raw-tokenizer data max")
    p.add_argument("--min-trained-fraction", type=_fraction, default=0.0, help="Minimum acceptable trained-token fraction in sampled rows")
    p.add_argument("--max-trained-fraction", type=_fraction, default=0.98, help="Maximum acceptable trained-token fraction in sampled rows")
    p.add_argument("--max-rows", type=_positive_int, default=10_000, help="Number of leading rows to scan")
    p.add_argument("--chunk-rows", type=_positive_int, default=1024, help="Rows per HDF5 read chunk")
    p.add_argument("--json", action="store_true", help="Emit JSON summary only")
    p.add_argument("--self-test", action="store_true", help="Run temporary fixture checks and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test()
        return 0
    if args.path is None:
        raise SystemExit("path is required unless --self-test is used")
    summary = validate(args)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("VALIDATION PASSED")
        print(f"path: {summary['path']}")
        print(f"shape: {summary['shape']} | dtypes: tokens={summary['tokens_dtype']} loss_mask={summary['loss_mask_dtype']}")
        print(f"sampled rows/tokens: {summary['sampled_rows']} / {summary['sampled_tokens']}")
        print(f"sample token min/max: {summary['sample_min_token']} / {summary['sample_max_token']}")
        print(f"trained fraction in sample: {summary['trained_fraction_in_sample']:.6f}")
        print(f"rows with any training: {summary['rows_with_any_training_in_sample']} / {summary['sampled_rows']}")
        print(f"rows all training: {summary['rows_all_training_in_sample']} / {summary['sampled_rows']}")
        if "warning" in summary:
            print(f"WARNING: {summary['warning']}")
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:
        try:
            sys.stdout.close()
        finally:
            raise SystemExit(1)
