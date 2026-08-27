#!/usr/bin/env python3
"""Self-contained point-cloud layout and tiny architecture smoke.

This script deliberately does not import the repository, PyG, torch_cluster,
torch_scatter, datasets, checkpoints, or visualization packages. It can be
run from any current working directory and performs no filesystem or network
I/O.
"""

from __future__ import annotations

import argparse
import sys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Run tiny dense/sparse point-cloud tensor contract checks."
    )
    parser.add_argument(
        "--mode",
        choices=("dense", "sparse", "all"),
        default="all",
        help="contract(s) to check (default: all)",
    )
    parser.add_argument("--batch", type=int, default=2, help="synthetic clouds")
    parser.add_argument("--points", type=int, default=8, help="points per cloud")
    parser.add_argument("--channels", type=int, default=3, help="input channels")
    parser.add_argument("--classes", type=int, default=5, help="output classes")
    parser.add_argument("--width", type=int, default=7, help="tiny hidden width")
    parser.add_argument("--seed", type=int, default=0, help="torch random seed")
    parser.add_argument(
        "--device",
        choices=("auto", "cpu"),
        default="auto",
        help="device for the tiny check; auto uses CUDA when available",
    )
    return parser


def validate_args(args: argparse.Namespace) -> None:
    for name in ("batch", "points", "channels", "classes", "width"):
        if getattr(args, name) < 1:
            raise ValueError("--{} must be >= 1".format(name))
    if args.channels < 3:
        raise ValueError("--channels must be >= 3 so coordinates occupy channels 0..2")


def require_torch():
    try:
        import torch
        import torch.nn as nn
    except Exception as exc:  # pragma: no cover - depends on the host
        raise RuntimeError(
            "tiny checks require PyTorch; --help does not require it"
        ) from exc
    return torch, nn


def assert_finite(name, tensor, torch) -> None:
    if not bool(torch.isfinite(tensor).all()):
        raise AssertionError("{} contains non-finite values".format(name))


def dense_check(args, torch, nn, device) -> str:
    class TinyDense(nn.Module):
        def __init__(self):
            super().__init__()
            self.body = nn.Sequential(
                nn.Conv2d(args.channels, args.width, kernel_size=1),
                nn.ReLU(),
                nn.Conv2d(args.width, args.classes, kernel_size=1),
            )

        def forward(self, features):
            return self.body(features)

    torch.manual_seed(args.seed)
    features = torch.randn(
        args.batch, args.channels, args.points, 1, device=device, dtype=torch.float32
    )
    # The first three channels are the coordinates used by the real KNN path.
    coordinates = features[:, :3, :, :]
    if coordinates.shape != (args.batch, 3, args.points, 1):
        raise AssertionError("dense coordinate contract failed")

    model = TinyDense().to(device)
    segmentation = model(features)
    expected = (args.batch, args.classes, args.points, 1)
    if tuple(segmentation.shape) != expected:
        raise AssertionError(
            "dense segmentation shape {} != {}".format(tuple(segmentation.shape), expected)
        )
    classification = torch.amax(segmentation, dim=(2, 3))
    expected_cls = (args.batch, args.classes)
    if tuple(classification.shape) != expected_cls:
        raise AssertionError(
            "dense classification shape {} != {}".format(
                tuple(classification.shape), expected_cls
            )
        )
    assert_finite("dense output", segmentation, torch)
    return "dense: {} -> segmentation {} and classification {}".format(
        tuple(features.shape), tuple(segmentation.shape), tuple(classification.shape)
    )


def sparse_check(args, torch, nn, device) -> str:
    class TinySparse(nn.Module):
        def __init__(self):
            super().__init__()
            self.body = nn.Sequential(
                nn.Linear(args.channels, args.width),
                nn.ReLU(),
                nn.Linear(args.width, args.classes),
            )

        def forward(self, features):
            return self.body(features)

    torch.manual_seed(args.seed)
    node_count = args.batch * args.points
    features = torch.randn(node_count, args.channels, device=device, dtype=torch.float32)
    positions = features[:, :3]
    batch = torch.arange(args.batch, device=device, dtype=torch.long).repeat_interleave(
        args.points
    )
    if features.shape[0] != positions.shape[0] or positions.shape[0] != batch.shape[0]:
        raise AssertionError("sparse node-alignment contract failed")
    if not bool(torch.equal(torch.unique(batch), torch.arange(args.batch, device=device))):
        raise AssertionError("sparse batch ids must be contiguous and zero based")

    model = TinySparse().to(device)
    segmentation = model(features)
    expected = (node_count, args.classes)
    if tuple(segmentation.shape) != expected:
        raise AssertionError(
            "sparse segmentation shape {} != {}".format(tuple(segmentation.shape), expected)
        )
    assert_finite("sparse output", segmentation, torch)

    # A small, dependency-free analogue of the per-graph global aggregation
    # used by the sparse task model. It verifies that graph membership is not
    # lost when a global feature is broadcast back to nodes.
    pooled = torch.stack(
        [segmentation[batch == graph].amax(dim=0) for graph in range(args.batch)]
    )
    broadcast = pooled[batch]
    if tuple(broadcast.shape) != expected:
        raise AssertionError("sparse global broadcast shape failed")
    assert_finite("sparse broadcast", broadcast, torch)
    return "sparse: {} nodes -> segmentation {} and broadcast {}".format(
        tuple(features.shape), tuple(segmentation.shape), tuple(broadcast.shape)
    )


def main(argv=None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        validate_args(args)
        torch, nn = require_torch()
        device = torch.device(
            "cuda" if args.device == "auto" and torch.cuda.is_available() else "cpu"
        )
        results = []
        if args.mode in ("dense", "all"):
            results.append(dense_check(args, torch, nn, device))
        if args.mode in ("sparse", "all"):
            results.append(sparse_check(args, torch, nn, device))
        print("pointcloud smoke ok (device={}):".format(device))
        for result in results:
            print("  " + result)
        return 0
    except (AssertionError, RuntimeError, ValueError) as exc:
        print("pointcloud smoke failed: {}".format(exc), file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
