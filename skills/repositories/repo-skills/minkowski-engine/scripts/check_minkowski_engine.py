#!/usr/bin/env python3
"""Check that MinkowskiEngine imports and runs a tiny smoke test.

This helper is safe by default: it does not download data, train a model, or
mutate the checkout. It can optionally prepend a local repository root to
`sys.path` for live checkout inspection, but it is primarily intended to verify
an already installed MinkowskiEngine package.

Examples:
  python check_minkowski_engine.py --help
  python check_minkowski_engine.py --smoke
  python check_minkowski_engine.py --repo-root /path/to/MinkowskiEngine --smoke
"""
from __future__ import annotations

import argparse
import json
import sys
from importlib import metadata
from pathlib import Path


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--repo-root",
        type=Path,
        help="Optional local repository root to add to sys.path before import.",
    )
    parser.add_argument(
        "--device",
        choices=("cpu", "cuda", "auto"),
        default="cpu",
        help="Smoke-test device to use.",
    )
    parser.add_argument(
        "--smoke",
        dest="smoke",
        action="store_true",
        help="Run a tiny SparseTensor + MinkowskiConvolution smoke test.",
    )
    parser.add_argument(
        "--no-smoke",
        dest="smoke",
        action="store_false",
        help="Skip the tiny smoke test and only verify import/metadata.",
    )
    parser.set_defaults(smoke=True)
    return parser.parse_args()


def maybe_add_repo_root(repo_root: Path | None) -> None:
    if not repo_root:
        return
    repo_root = repo_root.resolve()
    if not repo_root.exists():
        raise SystemExit(f"repo root does not exist: {repo_root}")
    sys.path.insert(0, str(repo_root))


def choose_device(requested: str, torch, me):
    if requested == "cpu":
        return "cpu"
    cuda_ok = bool(getattr(torch.cuda, "is_available", lambda: False)()) and bool(
        getattr(me, "is_cuda_available", lambda: False)()
    )
    if requested == "cuda":
        if not cuda_ok:
            raise SystemExit(
                "CUDA smoke requested but torch.cuda.is_available() or ME.is_cuda_available() is false"
            )
        return "cuda"
    return "cuda" if cuda_ok else "cpu"


def run_smoke(me, torch, device: str) -> dict:
    coords = torch.IntTensor([[0, 0, 0], [0, 1, 0], [0, 1, 1]])
    feats = torch.arange(6, dtype=torch.float32).view(3, 2)
    if device == "cuda":
        coords = coords.cuda()
        feats = feats.cuda()
    st = me.SparseTensor(features=feats, coordinates=coords, device=device)
    conv = me.MinkowskiConvolution(2, 4, kernel_size=3, stride=1, dimension=2)
    if device == "cuda":
        conv = conv.cuda()
    out = conv(st)
    pooled = me.MinkowskiGlobalAvgPooling()(out)
    return {
        "input_features": list(st.F.shape),
        "conv_features": list(out.F.shape),
        "pooled_features": list(pooled.F.shape),
        "tensor_stride": list(out.coordinate_map_key.get_tensor_stride()),
        "device": device,
    }


def main() -> int:
    args = parse_args()
    maybe_add_repo_root(args.repo_root)

    try:
        import MinkowskiEngine as me
        import torch
    except Exception as exc:  # noqa: BLE001
        print("MinkowskiEngine import failed:", exc, file=sys.stderr)
        return 1

    try:
        dist_version = metadata.version("MinkowskiEngine")
    except metadata.PackageNotFoundError:
        dist_version = "unknown"

    print(json.dumps({"package_version": dist_version, "module_version": me.__version__}, indent=2))
    print(json.dumps({"torch_version": torch.__version__, "torch_cuda": torch.version.cuda, "torch_cuda_available": torch.cuda.is_available(), "me_cuda_available": me.is_cuda_available()}, indent=2))

    if not args.smoke:
        return 0

    device = choose_device(args.device, torch, me)
    result = run_smoke(me, torch, device)
    print(json.dumps({"smoke": result}, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
