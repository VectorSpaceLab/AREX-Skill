#!/usr/bin/env python3
"""Check whether a TimeMixer checkout can be imported from a clean source-root path.

This script is a safe diagnostic helper. It does not train, download data, or
run benchmark examples. It only attempts imports and an optional CUDA probe.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check TimeMixer checkout imports and optional CUDA availability."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="TimeMixer checkout root containing run.py, models/, data_provider/, and utils/.",
    )
    parser.add_argument(
        "--check-cuda",
        action="store_true",
        help="Include a tiny torch CUDA availability probe in the JSON output.",
    )
    return parser


def import_module(name: str, errors: List[str]) -> str:
    try:
        __import__(name)
        return "ok"
    except Exception as exc:  # pragma: no cover - diagnostic path
        errors.append(f"{name}: {exc.__class__.__name__}: {exc}")
        return "error"


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    repo_root = Path(args.repo_root).expanduser().resolve()
    if not (repo_root / "run.py").exists():
        print(
            json.dumps(
                {
                    "status": "error",
                    "message": "--repo-root must point to a TimeMixer checkout containing run.py",
                    "repo_root": str(repo_root),
                },
                indent=2,
                sort_keys=True,
            )
        )
        return 2

    sys.path.insert(0, str(repo_root))
    errors: List[str] = []
    imports = {
        "run": import_module("run", errors),
        "models.TimeMixer": import_module("models.TimeMixer", errors),
        "data_provider.data_factory": import_module("data_provider.data_factory", errors),
        "exp.exp_long_term_forecasting": import_module("exp.exp_long_term_forecasting", errors),
        "exp.exp_short_term_forecasting": import_module("exp.exp_short_term_forecasting", errors),
        "exp.exp_imputation": import_module("exp.exp_imputation", errors),
        "exp.exp_anomaly_detection": import_module("exp.exp_anomaly_detection", errors),
        "exp.exp_classification": import_module("exp.exp_classification", errors),
        "utils.timefeatures": import_module("utils.timefeatures", errors),
    }

    torch_summary: Dict[str, Any] = {"available": False}
    if any(status == "ok" for status in imports.values()):
        try:
            import torch

            torch_summary = {
                "available": True,
                "version": torch.__version__,
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            }
            if args.check_cuda and torch.cuda.is_available():
                torch.empty(1, device="cuda")
        except Exception as exc:  # pragma: no cover - diagnostic path
            errors.append(f"torch: {exc.__class__.__name__}: {exc}")
            torch_summary = {"available": False, "error": f"{exc.__class__.__name__}: {exc}"}

    payload = {
        "status": "ok" if not errors else "error",
        "repo_root": str(repo_root),
        "imports": imports,
        "torch": torch_summary,
        "errors": errors,
        "notes": [
            "This helper only checks imports and optional CUDA presence.",
            "Use the model-architecture smoke helper for tensor shape checks.",
        ],
    }
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
