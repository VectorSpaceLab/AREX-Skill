#!/usr/bin/env python3
"""Inspect a QualityScaler checkout for required runtime layout.

Purpose:
- Check that the repo layout contains the app entry script, runtime assets,
  and model slots expected by the generated QualityScaler skill.
- Report missing runtime prerequisites without modifying the checkout.

Example:
  python inspect_qualityscaler_layout.py --repo-root /path/to/QualityScaler
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from typing import Iterable

APP_ENTRY = "QualityScaler.py"
REQUIRED_FILES = ["README.md", "requirements.txt"]
REQUIRED_DIRS = ["AI-onnx", "Assets"]
REQUIRED_RUNTIME_ASSETS = [
    "Assets/exiftool.exe",
    "Assets/ffmpeg.exe",
]
MODEL_NAMES = [
    "LVAx2",
    "RealESR_Gx4",
    "RealESR_Ax4",
    "BSRGANx2",
    "BSRGANx4",
    "RealESRGANx4",
    "MSharpx4",
    "IRCNN_Mx1",
    "IRCNN_Lx1",
]


def _blend_repo_path(repo_root: Path, relative_path: str) -> Path:
    return repo_root / Path(relative_path)


def _missing(paths: Iterable[Path]) -> list[str]:
    return [str(path) for path in paths if not path.exists()]


def inspect_layout(repo_root: Path) -> dict:
    repo_root = repo_root.resolve()
    required_files = [repo_root / name for name in [APP_ENTRY, *REQUIRED_FILES]]
    required_dirs = [repo_root / name for name in REQUIRED_DIRS]
    runtime_assets = [repo_root / name for name in REQUIRED_RUNTIME_ASSETS]
    model_files = [repo_root / "AI-onnx" / f"{model}_fp16.onnx" for model in MODEL_NAMES]

    result = {
        "repo_root": str(repo_root),
        "app_entry": str(repo_root / APP_ENTRY),
        "required_files_missing": _missing(required_files),
        "required_dirs_missing": _missing(required_dirs),
        "runtime_assets_missing": _missing(runtime_assets),
        "model_files_present": [path.name for path in model_files if path.exists()],
        "model_files_missing": [path.name for path in model_files if not path.exists()],
    }
    result["ok"] = not (
        result["required_files_missing"]
        or result["required_dirs_missing"]
        or result["runtime_assets_missing"]
        or result["model_files_missing"]
    )
    return result


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect a QualityScaler checkout for required runtime files and asset layout.",
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to the QualityScaler repository root (default: current directory).",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a human summary.",
    )
    return parser


def main() -> int:
    args = build_parser().parse_args()
    result = inspect_layout(Path(args.repo_root))

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"repo_root: {result['repo_root']}")
        print(f"app_entry: {result['app_entry']}")
        print(f"required_files_missing: {result['required_files_missing'] or '[]'}")
        print(f"required_dirs_missing: {result['required_dirs_missing'] or '[]'}")
        print(f"runtime_assets_missing: {result['runtime_assets_missing'] or '[]'}")
        print(f"model_files_present: {result['model_files_present'] or '[]'}")
        print(f"model_files_missing: {result['model_files_missing'] or '[]'}")
        print(f"ok: {result['ok']}")

    return 0 if result["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
