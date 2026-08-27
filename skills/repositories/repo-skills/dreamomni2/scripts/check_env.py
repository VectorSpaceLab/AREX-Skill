#!/usr/bin/env python3
"""Verify the DreamOmni2 runtime environment.

This check is intentionally lightweight: it confirms the CUDA-enabled torch
stack, the bundled helpers, and the DreamOmni2 pipeline import path without
starting any model downloads.
"""

from __future__ import annotations

import argparse
import inspect
import sys
from pathlib import Path

from PIL import Image

from dreamomni2_common import REPO_ROOT as COMMON_REPO_ROOT, extract_vlm_text, resizeinput


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Verify the DreamOmni2 Python and GPU environment.")
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Optional DreamOmni2 checkout path to add to sys.path before importing the pipeline.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    repo_root = Path(args.repo_root).resolve() if args.repo_root else COMMON_REPO_ROOT
    if repo_root is None:
        repo_root = Path.cwd().resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))

    import gradio
    import torch

    try:
        from dreamomni2.pipeline_dreamomni2 import DreamOmni2Pipeline
    except Exception as exc:  # pragma: no cover - surfaced directly to the caller
        print(f"DreamOmni2 pipeline import failed: {exc}")
        return 1

    print(f"python: {sys.executable}")
    print(f"version: {sys.version.split()[0]}")
    print(f"torch: {torch.__version__} (cuda {torch.version.cuda})")
    print(f"gradio: {gradio.__version__}")
    print(f"cuda_available: {torch.cuda.is_available()}")
    print(f"cuda_device_count: {torch.cuda.device_count()}")

    if not torch.cuda.is_available():
        print("CUDA is not available in this environment.")
        return 1

    print(f"cuda_device_name: {torch.cuda.get_device_name(0)}")
    print(f"cuda_capability: {torch.cuda.get_device_capability(0)}")
    probe = torch.empty((1,), device="cuda")
    print(f"cuda_probe: {probe}")

    dummy = Image.new("RGB", (97, 193), color=(128, 64, 32))
    resized = resizeinput(dummy)
    print(f"resizeinput: {dummy.size} -> {resized.size}")
    print(f"extract_vlm_text: {extract_vlm_text('```hello```')}")
    print(f"pipeline_call_signature: {inspect.signature(DreamOmni2Pipeline.__call__)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
