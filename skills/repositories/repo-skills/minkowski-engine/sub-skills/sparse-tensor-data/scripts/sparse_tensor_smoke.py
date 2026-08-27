#!/usr/bin/env python3
"""Run a tiny MinkowskiEngine sparse-tensor smoke test.

This helper is safe by default: it uses a tiny synthetic dataset, does not
require downloads, and does not mutate the repository.
"""
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

import torch


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, help="Optional local checkout root to add to sys.path.")
    parser.add_argument("--device", choices=("cpu", "cuda", "auto"), default="cpu")
    parser.add_argument("--skip-convolution", action="store_true", help="Only check tensor construction and quantization.")
    return parser.parse_args()


def add_repo_root(repo_root: Path | None) -> None:
    if not repo_root:
        return
    sys.path.insert(0, str(repo_root.resolve()))


def choose_device(requested: str, me):
    if requested == "cpu":
        return "cpu"
    cuda_ok = torch.cuda.is_available() and me.is_cuda_available()
    if requested == "cuda" and not cuda_ok:
        raise SystemExit("CUDA requested but not available in the current environment")
    return "cuda" if cuda_ok else "cpu"


def main() -> int:
    args = parse_args()
    add_repo_root(args.repo_root)

    try:
        import MinkowskiEngine as ME
    except Exception as exc:  # noqa: BLE001
        print(f"failed to import MinkowskiEngine: {exc}", file=sys.stderr)
        return 1

    device = choose_device(args.device, ME)

    coords_a = torch.tensor([[0, 0], [0, 1], [1, 0]], dtype=torch.int32)
    feats_a = torch.tensor([[1.0], [2.0], [3.0]], dtype=torch.float32)
    coords_b = torch.tensor([[0, 1], [1, 1]], dtype=torch.int32)
    feats_b = torch.tensor([[4.0], [5.0]], dtype=torch.float32)

    bcoords, bfeats = ME.utils.sparse_collate([coords_a, coords_b], [feats_a, feats_b])
    st = ME.SparseTensor(features=bfeats, coordinates=bcoords, device=device)

    field_coords = ME.utils.batched_coordinates([coords_a.float()], dtype=torch.float32)
    field = ME.TensorField(features=torch.tensor([[1.0], [2.0], [3.0]]), coordinates=field_coords, device=device)
    sparse_from_field = field.sparse()
    dense, min_coordinate, tensor_stride = sparse_from_field.dense()
    round_trip = ME.to_sparse(dense)

    summary = {
        "device": device,
        "batched_coords_shape": list(bcoords.shape),
        "batched_feats_shape": list(bfeats.shape),
        "sparse_len": len(st),
        "field_len": len(field),
        "field_sparse_len": len(sparse_from_field),
        "dense_shape": list(dense.shape),
        "round_trip_len": len(round_trip),
    }

    if not args.skip_convolution:
        conv = ME.MinkowskiConvolution(1, 2, kernel_size=3, stride=1, dimension=2)
        if device == "cuda":
            conv = conv.cuda()
        out = conv(st)
        shared = ME.SparseTensor(features=st.F, coordinate_manager=st.coordinate_manager, coordinate_map_key=st.coordinate_map_key)
        summary.update({
            "conv_shape": list(out.F.shape),
            "shared_add_shape": list((st + shared).F.shape),
        })

    print(json.dumps(summary, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
