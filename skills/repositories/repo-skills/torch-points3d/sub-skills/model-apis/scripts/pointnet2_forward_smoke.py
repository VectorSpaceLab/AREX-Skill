#!/usr/bin/env python3
"""CPU-safe PointNet2 application API forward smoke.

This adapts the repository's standalone PointNet2 segmentation example into a
self-contained helper. It creates synthetic point-cloud batches, performs one
forward pass, and asserts the requested output channel count. No downloads,
checkpoints, or GPU allocation are required.

Example:
  python sub-skills/model-apis/scripts/pointnet2_forward_smoke.py --num-points 1024 --input-nc 5 --output-nc 10
"""

from __future__ import annotations

import argparse
import json
import random


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a tiny Torch Points3D PointNet2 forward smoke test on CPU.")
    parser.add_argument("--num-points", type=int, default=1024, help="Synthetic points per sample; keep >=512 for default configs.")
    parser.add_argument("--input-nc", type=int, default=5, help="Feature channels per point.")
    parser.add_argument("--output-nc", type=int, default=10, help="Expected output channels after the optional API head.")
    parser.add_argument("--batch-size", type=int, default=2, help="Number of synthetic samples.")
    parser.add_argument("--num-layers", type=int, default=3, help="PointNet2 application config depth.")
    parser.add_argument("--architecture", choices=["unet", "encoder"], default="unet", help="Application architecture to build.")
    parser.add_argument("--multiscale", action="store_true", help="Use multiscale PointNet2 application config.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for deterministic synthetic data.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = parser.parse_args()

    if args.num_points <= 0 or args.input_nc <= 0 or args.output_nc <= 0 or args.batch_size <= 0:
        parser.error("num-points, input-nc, output-nc, and batch-size must be positive")

    try:
        import torch
        from torch_geometric.data import Batch, Data
        from torch_points3d.applications.pointnet2 import PointNet2
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"Import failed; install Torch Points3D and PyG dependencies first: {type(exc).__name__}: {exc}")

    random.seed(args.seed)
    torch.manual_seed(args.seed)
    torch.set_num_threads(1)

    items = []
    for _ in range(args.batch_size):
        pos = torch.randn((args.num_points, 3)).unsqueeze(0)
        feats = torch.randn((args.num_points, args.input_nc)).unsqueeze(0)
        items.append(Data(pos=pos, x=feats))
    batch = Batch.from_data_list(items)
    input_pos_shape = list(batch.pos.shape)
    input_x_shape = list(batch.x.shape)

    model = PointNet2(
        architecture=args.architecture,
        input_nc=args.input_nc,
        num_layers=args.num_layers,
        output_nc=args.output_nc,
        multiscale=args.multiscale,
    )
    model.eval()
    with torch.no_grad():
        out = model(batch)

    if not hasattr(out, "x"):
        raise SystemExit("Forward output has no x attribute")
    if out.x.shape[1] != args.output_nc:
        raise SystemExit(f"Unexpected output channel count: got {out.x.shape[1]}, expected {args.output_nc}")

    summary = {
        "model": "PointNet2",
        "architecture": args.architecture,
        "multiscale": args.multiscale,
        "input_pos_shape": input_pos_shape,
        "input_x_shape": input_x_shape,
        "output_x_shape": list(out.x.shape),
        "output_nc": args.output_nc,
        "status": "passed",
    }
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("PointNet2 forward smoke passed")
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
