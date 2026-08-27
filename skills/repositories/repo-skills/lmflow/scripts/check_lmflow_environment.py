#!/usr/bin/env python
"""Check a usable LMFlow inspection environment.

This helper prints package versions, route-map information, and optional backend
availability without starting any long-running job.

Examples:
  python scripts/check_lmflow_environment.py
  python scripts/check_lmflow_environment.py --check cuda,ray,vllm
  python scripts/check_lmflow_environment.py --repo-root /path/to/checkout
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import sys
from pathlib import Path


def _maybe_add_repo_root(repo_root: str | None) -> None:
    if not repo_root:
        return
    root = Path(repo_root).resolve()
    if root.exists() and str(root) not in sys.path:
        sys.path.insert(0, str(root))


def _safe_version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "missing"


def main() -> int:
    parser = argparse.ArgumentParser(description="Check the LMFlow environment.")
    parser.add_argument("--repo-root", help="Optional repository root to add to sys.path before import.")
    parser.add_argument(
        "--check",
        default="",
        help="Comma-separated optional checks: cuda,ray,vllm,sglang,trl,deepspeed,flash_attn,multimodal",
    )
    args = parser.parse_args()
    _maybe_add_repo_root(args.repo_root)

    import lmflow
    from lmflow.pipeline.auto_pipeline import PIPELINE_MAPPING, PIPELINE_NEEDS_EXTRAS
    from lmflow.utils.conversation_template import PRESET_TEMPLATES

    print(f"lmflow={lmflow.__version__}")
    print(f"distribution={_safe_version('lmflow')}")
    print(f"transformers={_safe_version('transformers')}")
    print(f"datasets={_safe_version('datasets')}")
    print(f"torch={_safe_version('torch')}")
    print(f"pipelines={','.join(sorted(PIPELINE_MAPPING))}")
    print(f"needs_extras={','.join(sorted(PIPELINE_NEEDS_EXTRAS))}")
    print(f"templates={len(PRESET_TEMPLATES)}")

    checks = [chunk.strip() for chunk in args.check.split(",") if chunk.strip()]
    if "cuda" in checks:
        import torch

        print(f"cuda_available={torch.cuda.is_available()}")
        print(f"cuda_device_count={torch.cuda.device_count()}")
        if torch.cuda.is_available():
            print(f"cuda_device_name={torch.cuda.get_device_name(0)}")
            print(f"cuda_capability={torch.cuda.get_device_capability(0)}")
    for name in [c for c in checks if c != "cuda"]:
        try:
            mod = importlib.import_module(name)
            print(f"{name}=ok:{getattr(mod, '__file__', 'namespace')}")
        except Exception as exc:  # noqa: BLE001
            print(f"{name}=missing:{type(exc).__name__}:{exc}")
            return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
