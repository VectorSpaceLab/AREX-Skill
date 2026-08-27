#!/usr/bin/env python3
"""Synthetic IndexDataset smoke test for PyTorch Geometric Temporal.

This helper validates low-level index-batching mechanics without network access,
real dataset downloads, model training, or writes outside stdout/stderr.

Examples:
    python scripts/index_batching_smoke.py --help
    python scripts/index_batching_smoke.py --lags 3 --batch-size 2
    python scripts/index_batching_smoke.py --lazy --lags 3 --batch-size 2
"""

from __future__ import annotations

import argparse
import json
import sys
from typing import Any


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic no-network smoke test for "
            "torch_geometric_temporal.signal.index_dataset.IndexDataset."
        )
    )
    parser.add_argument(
        "--timesteps",
        type=int,
        default=16,
        help="Number of synthetic time steps to generate (default: 16).",
    )
    parser.add_argument(
        "--nodes",
        type=int,
        default=4,
        help="Number of synthetic graph nodes (default: 4).",
    )
    parser.add_argument(
        "--features",
        type=int,
        default=2,
        help="Number of synthetic node features (default: 2).",
    )
    parser.add_argument(
        "--lags",
        type=int,
        default=3,
        help="Input and target window length passed as IndexDataset horizon (default: 3).",
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=2,
        help="DataLoader batch size (default: 2).",
    )
    parser.add_argument(
        "--shuffle",
        action="store_true",
        help="Enable DataLoader shuffle; direct dataset[0] checks still remain deterministic.",
    )
    parser.add_argument(
        "--lazy",
        action="store_true",
        help="Use a Dask array and IndexDataset(lazy=True) to exercise lazy slicing.",
    )
    parser.add_argument(
        "--all-gpu",
        type=int,
        default=-1,
        metavar="DEVICE_ID",
        help=(
            "Optional GPU-index smoke path. Use -1 for CPU (default) or a CUDA "
            "device id such as 0. Fails fast if CUDA is unavailable."
        ),
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit a JSON summary instead of human-readable text.",
    )
    return parser


def fail(message: str, code: int = 1) -> int:
    print(f"index_batching_smoke: {message}", file=sys.stderr)
    return code


def import_runtime() -> tuple[Any, Any, Any, Any]:
    try:
        import numpy as np
        import torch
        from torch.utils.data import DataLoader
        from torch_geometric_temporal.signal.index_dataset import IndexDataset
    except ModuleNotFoundError as exc:  # pragma: no cover - depends on environment
        missing = exc.name or "unknown"
        raise SystemExit(
            fail(
                "missing required module "
                f"{missing!r}; install PyTorch Geometric Temporal with index-batching dependencies",
                code=2,
            )
        )
    return np, torch, DataLoader, IndexDataset


def to_cpu_tensor(value: Any, torch: Any) -> Any:
    if not torch.is_tensor(value):
        value = torch.as_tensor(value)
    return value.detach().cpu()


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.timesteps <= 0:
        parser.error("--timesteps must be positive")
    if args.nodes <= 0:
        parser.error("--nodes must be positive")
    if args.features <= 0:
        parser.error("--features must be positive")
    if args.lags <= 0:
        parser.error("--lags must be positive")
    if args.batch_size <= 0:
        parser.error("--batch-size must be positive")
    if args.timesteps - (2 * args.lags - 1) <= 0:
        parser.error("--timesteps must allow at least one start index: timesteps - (2 * lags - 1) > 0")
    if args.lazy and args.all_gpu != -1:
        parser.error("--lazy and --all-gpu are mutually exclusive in this smoke helper")

    np, torch, DataLoader, IndexDataset = import_runtime()

    data_np = np.arange(
        args.timesteps * args.nodes * args.features,
        dtype=np.float32,
    ).reshape(args.timesteps, args.nodes, args.features)

    if args.all_gpu != -1:
        if not torch.cuda.is_available():
            return fail("--all-gpu was requested but torch.cuda.is_available() is False", code=2)
        device = torch.device(f"cuda:{args.all_gpu}")
        data = torch.as_tensor(data_np, dtype=torch.float32, device=device)
        gpu = True
        lazy = False
        mode = f"gpu:{args.all_gpu}"
    elif args.lazy:
        try:
            import dask.array as da
        except ModuleNotFoundError:
            return fail("--lazy requires dask.array to be importable", code=2)
        chunk_t = max(args.lags, min(args.timesteps, 4))
        data = da.from_array(data_np, chunks=(chunk_t, args.nodes, args.features))
        gpu = False
        lazy = True
        mode = "lazy-dask-cpu"
    else:
        data = data_np
        gpu = False
        lazy = False
        mode = "cpu"

    indices = np.arange(args.timesteps - (2 * args.lags - 1), dtype=np.int64)
    dataset = IndexDataset(indices, data, args.lags, lazy=lazy, gpu=gpu)
    loader = DataLoader(dataset, batch_size=args.batch_size, shuffle=args.shuffle)

    if len(dataset) != int(indices.shape[0]):
        return fail(f"unexpected dataset length: got {len(dataset)}, expected {indices.shape[0]}")

    direct_x, direct_y = dataset[0]
    expected_x = torch.as_tensor(data_np[0 : args.lags], dtype=torch.float32)
    expected_y = torch.as_tensor(data_np[args.lags : 2 * args.lags], dtype=torch.float32)

    direct_x_cpu = to_cpu_tensor(direct_x, torch).float()
    direct_y_cpu = to_cpu_tensor(direct_y, torch).float()

    if tuple(direct_x_cpu.shape) != tuple(expected_x.shape):
        return fail(f"unexpected direct X shape: got {tuple(direct_x_cpu.shape)}, expected {tuple(expected_x.shape)}")
    if tuple(direct_y_cpu.shape) != tuple(expected_y.shape):
        return fail(f"unexpected direct y shape: got {tuple(direct_y_cpu.shape)}, expected {tuple(expected_y.shape)}")
    if not torch.equal(direct_x_cpu, expected_x):
        return fail("direct X window contents do not match expected data[0:lags]")
    if not torch.equal(direct_y_cpu, expected_y):
        return fail("direct y window contents do not match expected data[lags:2*lags]")

    batch_x, batch_y = next(iter(loader))
    batch_x_cpu = to_cpu_tensor(batch_x, torch).float()
    batch_y_cpu = to_cpu_tensor(batch_y, torch).float()

    expected_tail = (args.lags, args.nodes, args.features)
    if tuple(batch_x_cpu.shape[1:]) != expected_tail:
        return fail(f"unexpected batch X tail shape: got {tuple(batch_x_cpu.shape[1:])}, expected {expected_tail}")
    if tuple(batch_y_cpu.shape[1:]) != expected_tail:
        return fail(f"unexpected batch y tail shape: got {tuple(batch_y_cpu.shape[1:])}, expected {expected_tail}")
    if batch_x_cpu.shape[0] > args.batch_size:
        return fail(f"batch dimension exceeds --batch-size: {batch_x_cpu.shape[0]} > {args.batch_size}")

    summary = {
        "ok": True,
        "mode": mode,
        "import_path": "torch_geometric_temporal.signal.index_dataset.IndexDataset",
        "sample_count": int(len(dataset)),
        "lags": int(args.lags),
        "batch_size": int(args.batch_size),
        "shuffle": bool(args.shuffle),
        "batch_x_shape": list(batch_x_cpu.shape),
        "batch_y_shape": list(batch_y_cpu.shape),
        "direct_x_sum": float(direct_x_cpu.sum().item()),
        "direct_y_sum": float(direct_y_cpu.sum().item()),
    }

    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print("IndexDataset smoke passed")
        print(f"  mode: {summary['mode']}")
        print(f"  import: {summary['import_path']}")
        print(f"  samples: {summary['sample_count']}")
        print(f"  X batch shape: {tuple(summary['batch_x_shape'])}")
        print(f"  y batch shape: {tuple(summary['batch_y_shape'])}")
        print(f"  direct window sums: X={summary['direct_x_sum']:.1f}, y={summary['direct_y_sum']:.1f}")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
