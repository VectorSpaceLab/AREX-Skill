#!/usr/bin/env python3
"""Smoke-test the repo's core public imports and model constructors."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import yaml

SCRIPT_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(SCRIPT_DIR))
from bootstrap_runtime import ensure_repo_root  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=Path.cwd(), help="Path to the 3DDFA_V2 checkout")
    parser.add_argument("--config", default="configs/mb1_120x120.yml", help="Config file to load")
    args = parser.parse_args()

    repo_root = ensure_repo_root(args.repo_root)
    cfg = yaml.safe_load((repo_root / args.config).read_text())

    from FaceBoxes import FaceBoxes
    from FaceBoxes.FaceBoxes_ONNX import FaceBoxes_ONNX
    from TDDFA import TDDFA
    from TDDFA_ONNX import TDDFA_ONNX
    import utils.render  # noqa: F401

    detector = FaceBoxes()
    aligner = TDDFA(**cfg)
    _ = FaceBoxes_ONNX
    _ = TDDFA_ONNX

    print(f"FaceBoxes={type(detector).__name__}")
    print(f"TDDFA={type(aligner).__name__}")
    print(f"tri={aligner.tri.shape}")
    print("core-imports-ok")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
