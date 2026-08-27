#!/usr/bin/env python3
"""Inspect a flat-token HDF5 file without requiring the source repository.

The expected pretraining schema is a one-dimensional integer dataset named
``tokens`` containing r50k_base token ids with EOT separators (50256). The script
prints shape/dtype/range/EOT/head statistics and can optionally decode the head
when tiktoken is installed.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import tempfile
from pathlib import Path


def _positive_int(value: str) -> int:
    try:
        out = int(value)
    except ValueError as exc:  # pragma: no cover - argparse prints this path
        raise argparse.ArgumentTypeError(str(exc)) from exc
    if out <= 0:
        raise argparse.ArgumentTypeError("must be positive")
    return out


def _load_head_and_stats(path: Path, dataset: str, sample_tokens: int, expect_eot_id: int | None) -> dict:
    try:
        import h5py
        import numpy as np
    except ModuleNotFoundError as exc:
        raise SystemExit(f"missing dependency: {exc.name}. Install h5py and numpy to inspect HDF5 files.") from exc

    if not path.exists():
        raise SystemExit(f"file not found: {path}")

    with h5py.File(path, "r") as h5:
        if dataset not in h5:
            keys = ", ".join(sorted(h5.keys())) or "<none>"
            raise SystemExit(f"dataset {dataset!r} not found. Available top-level keys: {keys}")
        dset = h5[dataset]
        shape = tuple(int(x) for x in dset.shape)
        if len(shape) != 1:
            raise SystemExit(f"dataset {dataset!r} must be one-dimensional for flat pretraining tokens; got shape {shape}")
        n = shape[0]
        head_n = min(n, sample_tokens)
        head = np.asarray(dset[:head_n]) if head_n else np.asarray([], dtype=dset.dtype)
        summary = {
            "path": str(path),
            "dataset": dataset,
            "shape": shape,
            "dtype": str(dset.dtype),
            "sample_tokens": int(head_n),
            "head_ids": head[: min(20, head.size)].astype(int).tolist(),
        }
        if head.size:
            summary.update(
                {
                    "sample_min": int(head.min()),
                    "sample_max": int(head.max()),
                    "negative_count_in_sample": int((head < 0).sum()),
                }
            )
            if expect_eot_id is not None:
                summary["expect_eot_id"] = int(expect_eot_id)
                summary["eot_count_in_sample"] = int((head == expect_eot_id).sum())
        else:
            summary.update({"sample_min": None, "sample_max": None, "negative_count_in_sample": 0})
            if expect_eot_id is not None:
                summary.update({"expect_eot_id": int(expect_eot_id), "eot_count_in_sample": 0})
    return summary


def _decode_head(ids: list[int], max_chars: int) -> str:
    try:
        import tiktoken
    except ModuleNotFoundError as exc:
        raise SystemExit("--decode-head requires tiktoken; install tiktoken or omit --decode-head") from exc
    enc = tiktoken.get_encoding("r50k_base")
    # r50k_base can decode ordinary ids 0..50255; EOT and padded vocab ids are skipped.
    clean = [int(t) for t in ids if 0 <= int(t) < 50256]
    return enc.decode(clean)[:max_chars]


def make_fixture(path: Path) -> None:
    """Create a tiny valid flat-token HDF5 fixture for --self-test only."""
    import h5py
    import numpy as np

    path.parent.mkdir(parents=True, exist_ok=True)
    tokens = np.asarray([15496, 995, 50256, 1212, 318, 257, 1332, 50256], dtype=np.int32)
    with h5py.File(path, "w") as h5:
        h5.create_dataset("tokens", data=tokens)


def run_self_test() -> None:
    with tempfile.TemporaryDirectory() as td:
        path = Path(td) / "flat_tokens.h5"
        make_fixture(path)
        summary = _load_head_and_stats(path, "tokens", 100, 50256)
        assert summary["shape"] == (8,)
        assert summary["sample_min"] >= 0
        assert summary["eot_count_in_sample"] == 2
    print("SELF TEST PASSED")


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Inspect a flat HDF5 tokens dataset for pretraining data.")
    p.add_argument("path", nargs="?", type=Path, help="HDF5 file to inspect")
    p.add_argument("--dataset", default="tokens", help="HDF5 dataset name (default: tokens)")
    p.add_argument("--sample-tokens", type=_positive_int, default=100_000, help="Head sample size for min/max/EOT stats")
    p.add_argument("--expect-eot-id", type=int, default=None, help="Count this EOT token id in the sample, commonly 50256")
    p.add_argument("--decode-head", action="store_true", help="Decode the first --decode-tokens ids with r50k_base (requires tiktoken)")
    p.add_argument("--decode-tokens", type=_positive_int, default=80, help="Number of initial ids to decode when --decode-head is set")
    p.add_argument("--decode-max-chars", type=_positive_int, default=500, help="Maximum decoded characters to print")
    p.add_argument("--json", action="store_true", help="Emit machine-readable JSON only")
    p.add_argument("--self-test", action="store_true", help="Run a tiny temporary fixture check and exit")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.self_test:
        run_self_test()
        return 0
    if args.path is None:
        raise SystemExit("path is required unless --self-test is used")

    summary = _load_head_and_stats(args.path, args.dataset, args.sample_tokens, args.expect_eot_id)
    if args.decode_head:
        decode_n = min(args.decode_tokens, len(summary["head_ids"]))
        # Re-read the requested number when more than the printed head ids are needed.
        if decode_n < args.decode_tokens:
            import h5py
            import numpy as np

            with h5py.File(args.path, "r") as h5:
                decode_ids = np.asarray(h5[args.dataset][: args.decode_tokens]).astype(int).tolist()
        else:
            decode_ids = summary["head_ids"][:decode_n]
        summary["decoded_head"] = _decode_head(decode_ids, args.decode_max_chars)

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(f"path: {summary['path']}")
        print(f"dataset: {summary['dataset']}")
        print(f"shape: {summary['shape']} | dtype: {summary['dtype']}")
        print(f"sample tokens: {summary['sample_tokens']}")
        print(f"sample min/max: {summary['sample_min']} / {summary['sample_max']}")
        print(f"negative ids in sample: {summary['negative_count_in_sample']}")
        if "expect_eot_id" in summary:
            print(f"EOT id {summary['expect_eot_id']} count in sample: {summary['eot_count_in_sample']}")
        print(f"head ids: {summary['head_ids']}")
        if "decoded_head" in summary:
            print("decoded head:")
            print(repr(summary["decoded_head"]))
    return 0


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except BrokenPipeError:  # allow piping to head
        try:
            sys.stdout.close()
        finally:
            raise SystemExit(1)
