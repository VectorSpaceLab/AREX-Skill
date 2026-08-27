#!/usr/bin/env python3
"""Tiny self-contained MinkowskiEngine layer smoke.

The script uses synthetic coordinates/features only. It defaults to CPU so it
can be used as a quick layer sanity check without datasets or network access.
"""

from __future__ import annotations

import argparse
import sys


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a deterministic MinkowskiEngine sparse layer smoke on synthetic "
            "coordinates. No downloads or repository checkout are required."
        )
    )
    parser.add_argument(
        "--device",
        default="cpu",
        choices=("cpu", "cuda"),
        help="Runtime device. Default: cpu. CUDA is used only when explicitly requested and available.",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=7,
        help="Torch random seed for deterministic layer initialization. Default: 7.",
    )
    parser.add_argument(
        "--num-classes",
        type=int,
        default=3,
        help="Number of logits emitted by the tiny global-pooling head. Default: 3.",
    )
    parser.add_argument("--quiet", action="store_true", help="Only print the final OK line.")
    return parser.parse_args(argv)


def import_runtime():
    try:
        import torch
        import torch.nn as nn
        import MinkowskiEngine as ME
    except Exception as exc:  # pragma: no cover - environment diagnostic
        raise SystemExit(
            "Failed to import torch and MinkowskiEngine. Install a working "
            f"MinkowskiEngine package, then rerun this smoke. Original error: {exc}"
        ) from exc
    return torch, nn, ME


def make_sparse_input(torch, ME, device: str):
    """Create a two-batch 2D sparse tensor with deterministic features."""
    batch_points = [
        torch.IntTensor([[0, 0], [1, 0], [0, 1], [2, 1]]),
        torch.IntTensor([[0, 0], [1, 0], [0, 1], [1, 1]]),
    ]
    coords = ME.utils.batched_coordinates(batch_points, dtype=torch.int32, device=device)
    feats = torch.arange(1, 1 + len(coords) * 2, dtype=torch.float32, device=device)
    feats = feats.view(len(coords), 2) / 10.0
    return ME.SparseTensor(features=feats, coordinates=coords, device=device)


def describe(name: str, sparse_tensor) -> str:
    stride = sparse_tensor.coordinate_map_key.get_tensor_stride()
    return f"{name}: points={len(sparse_tensor)} channels={sparse_tensor.F.shape[1]} stride={list(stride)}"


def build_tiny_network(nn, ME, num_classes: int):
    class TinySparseNet(ME.MinkowskiNetwork):
        def __init__(self):
            super().__init__(D=2)
            self.stem = nn.Sequential(
                ME.MinkowskiConvolution(2, 4, kernel_size=3, stride=1, bias=False, dimension=2),
                ME.MinkowskiBatchNorm(4),
                ME.MinkowskiReLU(inplace=True),
            )
            self.down = nn.Sequential(
                ME.MinkowskiConvolution(4, 8, kernel_size=3, stride=1, bias=False, dimension=2),
                ME.MinkowskiMaxPooling(kernel_size=2, stride=2, dimension=2),
            )
            self.up = ME.MinkowskiConvolutionTranspose(8, 4, kernel_size=2, stride=2, bias=False, dimension=2)
            self.global_pool = ME.MinkowskiGlobalAvgPooling()
            self.head = ME.MinkowskiLinear(8, num_classes, bias=True)

        def forward(self, x):
            skip = self.stem(x)
            down = self.down(skip)
            up = self.up(down, skip)  # target coordinates from skip connection
            averaged = ME.mean(up, skip)
            merged = ME.cat(up, skip)
            pooled = self.global_pool(merged)
            logits = self.head(pooled)
            return skip, down, up, averaged, merged, pooled, logits

    return TinySparseNet()


def run(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    torch, nn, ME = import_runtime()

    if args.device == "cuda":
        if not torch.cuda.is_available():
            raise SystemExit("CUDA was requested, but torch.cuda.is_available() is False.")
        if hasattr(ME, "is_cuda_available") and not ME.is_cuda_available():
            raise SystemExit("CUDA was requested, but MinkowskiEngine does not report CUDA support.")

    torch.manual_seed(args.seed)
    x = make_sparse_input(torch, ME, args.device)
    net = build_tiny_network(nn, ME, args.num_classes).to(args.device).eval()

    with torch.no_grad():
        skip, down, up, averaged, merged, pooled, logits = net(x)
        broadcasted = ME.MinkowskiBroadcastAddition()(merged, pooled)
        mask = torch.arange(len(broadcasted), device=broadcasted.F.device) % 2 == 0
        pruned = ME.MinkowskiPruning()(broadcasted, mask.bool())
        unioned = ME.MinkowskiUnion()(broadcasted, pruned)

        rows = torch.IntTensor([0, 0, 1, 1]).to(args.device)
        cols = torch.IntTensor([0, 1, 2, 3]).to(args.device)
        vals = torch.ones(4, dtype=torch.float32, device=args.device)
        mat = torch.arange(12, dtype=torch.float32, device=args.device).view(4, 3)
        spmm_out = ME.spmm(rows, cols, vals, torch.Size([2, 4]), mat)

    checks = [
        (x.F.shape[1] == 2, "input feature width"),
        (skip.F.shape[1] == 4, "stem feature width"),
        (down.F.shape[1] == 8, "downsample feature width"),
        (up.coordinate_map_key == skip.coordinate_map_key, "upsample coordinate alignment"),
        (averaged.F.shape[1] == 4, "ME.mean feature width"),
        (merged.F.shape[1] == 8, "ME.cat feature width"),
        (pooled.F.shape[0] == 2, "global pooling batch rows"),
        (logits.F.shape == torch.Size([2, args.num_classes]), "logit shape"),
        (broadcasted.F.shape == merged.F.shape, "broadcast shape"),
        (len(pruned) == int(mask.sum().item()), "pruning length"),
        (len(unioned) == len(broadcasted), "union support size"),
        (spmm_out.shape == torch.Size([2, 3]), "SPMM output shape"),
    ]
    failed = [name for ok, name in checks if not bool(ok)]
    if failed:
        raise SystemExit("Smoke check failed: " + ", ".join(failed))

    if not args.quiet:
        print(f"MinkowskiEngine version: {getattr(ME, '__version__', 'unknown')}")
        for name, tensor in [
            ("input", x),
            ("skip", skip),
            ("down", down),
            ("up", up),
            ("merged", merged),
            ("pooled", pooled),
            ("logits", logits),
            ("broadcasted", broadcasted),
            ("pruned", pruned),
            ("unioned", unioned),
        ]:
            print(describe(name, tensor))
        print(f"spmm: shape={tuple(spmm_out.shape)}")
    print("OK: layer_smoke completed")
    return 0


if __name__ == "__main__":
    raise SystemExit(run(sys.argv[1:]))
