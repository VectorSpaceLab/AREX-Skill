#!/usr/bin/env python3
"""Check that the repo's required checkpoints and config assets exist."""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml


REQUIRED_ALWAYS = [
    "FaceBoxes/weights/FaceBoxesProd.pth",
    "configs/bfm_noneck_v3.pkl",
    "configs/tri.pkl",
    "configs/BFM_UV.mat",
    "configs/indices.npy",
    "configs/param_mean_std_62d_120x120.pkl",
]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=Path.cwd(), help="Path to the 3DDFA_V2 checkout")
    parser.add_argument("--config", default="configs/mb1_120x120.yml", help="Config file to inspect")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).expanduser().resolve()
    cfg_path = repo_root / args.config
    cfg = yaml.safe_load(cfg_path.read_text())

    required = set(REQUIRED_ALWAYS)
    required.add(cfg.get("checkpoint_fp", ""))
    required.add(cfg.get("bfm_fp", ""))

    missing: list[str] = []
    for rel in sorted(p for p in required if p):
        path = repo_root / rel
        if not path.exists():
            missing.append(rel)
        else:
            print(f"ok {rel}")

    onnx_notes = [
        "weights/mb1_120x120.onnx",
        "FaceBoxes/weights/FaceBoxesProd.onnx",
        "configs/bfm_noneck_v3.onnx",
    ]
    for rel in onnx_notes:
        if (repo_root / rel).exists():
            print(f"ok {rel}")
        else:
            print(f"note {rel} missing; the ONNX workflows will auto-convert it if needed")

    if missing:
        print("missing assets:")
        for rel in missing:
            print(f"- {rel}")
        return 1

    print("asset-check-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
