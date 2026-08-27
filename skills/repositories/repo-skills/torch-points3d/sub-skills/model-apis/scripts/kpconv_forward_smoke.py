#!/usr/bin/env python3
"""Guarded KPConv application API smoke.

KPConv needs Torch Points3D, PyG compiled packages, and torch-points-kernels.
By default this helper checks imports and constructor availability only. Pass
`--run-forward` to execute a tiny synthetic forward pass.

Examples:
  python sub-skills/model-apis/scripts/kpconv_forward_smoke.py --check-imports
  python sub-skills/model-apis/scripts/kpconv_forward_smoke.py --run-forward --num-points 128
"""

from __future__ import annotations

import argparse
import json


def main() -> int:
    parser = argparse.ArgumentParser(description="Check or run a tiny Torch Points3D KPConv application smoke.")
    parser.add_argument("--check-imports", action="store_true", help="Only check required imports and signature availability.")
    parser.add_argument("--run-forward", action="store_true", help="Instantiate KPConv and run a synthetic forward pass.")
    parser.add_argument("--num-points", type=int, default=128, help="Synthetic points per sample for forward mode.")
    parser.add_argument("--input-nc", type=int, default=3, help="Feature channels per point.")
    parser.add_argument("--output-nc", type=int, default=5, help="Expected output channels when output head is enabled.")
    parser.add_argument("--in-feat", type=int, default=16, help="KPConv base feature width.")
    parser.add_argument("--in-grid-size", type=float, default=0.02, help="Input grid size used by default configs.")
    parser.add_argument("--num-layers", type=int, default=4, help="KPConv application depth.")
    parser.add_argument("--seed", type=int, default=0, help="Random seed for synthetic data.")
    parser.add_argument("--json", action="store_true", help="Emit JSON summary.")
    args = parser.parse_args()

    if not args.check_imports and not args.run_forward:
        args.check_imports = True

    try:
        import torch
        from torch_geometric.data import Batch, Data
        from torch_points3d.applications.kpconv import KPConv
        from torch_points3d.core.data_transform import GridSampling3D
        import torch_points_kernels  # noqa: F401
    except Exception as exc:  # noqa: BLE001
        raise SystemExit(f"KPConv dependency import failed: {type(exc).__name__}: {exc}")

    summary = {
        "imports": "passed",
        "forward": "not-run",
        "model": "KPConv",
        "num_points": args.num_points,
        "input_nc": args.input_nc,
        "output_nc": args.output_nc,
    }

    if args.run_forward:
        if args.num_points <= 0 or args.input_nc <= 0 or args.output_nc <= 0:
            parser.error("num-points, input-nc, and output-nc must be positive")
        torch.manual_seed(args.seed)
        torch.set_num_threads(1)
        transform = GridSampling3D(0.01)
        samples = []
        for _ in range(2):
            data = Data(pos=torch.randn(args.num_points, 3), x=torch.randn(args.num_points, args.input_nc))
            samples.append(transform(data))
        batch = Batch.from_data_list(samples)
        model = KPConv(
            architecture="unet",
            input_nc=args.input_nc,
            output_nc=args.output_nc,
            in_feat=args.in_feat,
            in_grid_size=args.in_grid_size,
            num_layers=args.num_layers,
        )
        model.eval()
        with torch.no_grad():
            out = model(batch)
        if not hasattr(out, "x"):
            raise SystemExit("Forward output has no x attribute")
        if out.x.shape[1] != args.output_nc:
            raise SystemExit(f"Unexpected output channel count: got {out.x.shape[1]}, expected {args.output_nc}")
        summary.update({"forward": "passed", "output_x_shape": list(out.x.shape)})

    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print("KPConv smoke completed")
        for key, value in summary.items():
            print(f"{key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
