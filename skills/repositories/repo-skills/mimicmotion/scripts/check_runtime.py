#!/usr/bin/env python3
"""Preflight MimicMotion's runtime stack.

This helper is safe to run from any working directory. Pass `--repo-root` to a
checkout of MimicMotion so the local source package can be imported without
hardcoding a path.

Typical usage:
    python scripts/check_runtime.py --repo-root /path/to/MimicMotion
    python scripts/check_runtime.py --repo-root /path/to/MimicMotion --skip-models
"""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
import sys
from importlib import metadata
from pathlib import Path
from typing import Iterable

REQUIRED_MODULES = [
    "torch",
    "torchvision",
    "diffusers",
    "transformers",
    "decord",
    "einops",
    "omegaconf",
    "onnxruntime",
    "cog",
    "cv2",
    "PIL",
    "numpy",
    "inference",
    "predict",
    "mimicmotion.utils.loader",
    "mimicmotion.utils.utils",
    "mimicmotion.dwpose.preprocess",
    "mimicmotion.dwpose.dwpose_detector",
    "mimicmotion.pipelines.pipeline_mimicmotion",
]

REQUIRED_MODEL_FILES = [
    Path("models/DWPose/yolox_l.onnx"),
    Path("models/DWPose/dw-ll_ucoco_384.onnx"),
    Path("models/MimicMotion_1-1.pth"),
]

DISTIBUTION_NAMES = [
    "torch",
    "torchvision",
    "diffusers",
    "transformers",
    "decord",
    "einops",
    "omegaconf",
    "onnxruntime-gpu",
    "onnxruntime",
    "cog",
    "av",
    "opencv-python",
    "matplotlib",
]


def _add_repo_root(repo_root: Path) -> Path:
    repo_root = repo_root.resolve()
    if str(repo_root) not in sys.path:
        sys.path.insert(0, str(repo_root))
    return repo_root


def _distribution_versions(names: Iterable[str]) -> dict[str, str | None]:
    versions: dict[str, str | None] = {}
    for name in names:
        try:
            versions[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            versions[name] = None
    return versions


def _module_status(name: str) -> str:
    try:
        importlib.import_module(name)
        return "ok"
    except Exception as exc:  # pragma: no cover - surfaced to user
        return f"{type(exc).__name__}: {exc}"


def _model_status(models_dir: Path) -> dict[str, list[str]]:
    missing = [str(path) for path in REQUIRED_MODEL_FILES if not (models_dir / path).exists()]
    return {"missing": missing, "present": [] if missing else [str(path) for path in REQUIRED_MODEL_FILES]}


def validate_runtime(repo_root: Path, models_dir: Path | None = None, *, skip_models: bool = False) -> dict:
    repo_root = _add_repo_root(repo_root)
    if not repo_root.exists():
        raise FileNotFoundError(f"repo root does not exist: {repo_root}")

    if not shutil.which("ffmpeg"):
        raise RuntimeError("ffmpeg is required for video writing but was not found on PATH")

    import torch  # local import after repo root setup
    import onnxruntime as ort

    if not torch.cuda.is_available():
        raise RuntimeError("CUDA is required for MimicMotion but torch.cuda.is_available() is false")

    providers = list(ort.get_available_providers())
    if "CUDAExecutionProvider" not in providers:
        raise RuntimeError(f"onnxruntime-gpu is missing CUDAExecutionProvider: {providers}")

    import_results = {name: _module_status(name) for name in REQUIRED_MODULES}
    failed_imports = {name: status for name, status in import_results.items() if status != "ok"}
    if failed_imports:
        raise RuntimeError(f"required imports failed: {failed_imports}")

    model_results = {"checked": False, "missing": []}
    if not skip_models:
        models_dir = models_dir or repo_root / "models"
        model_results = _model_status(models_dir)
        if model_results["missing"]:
            raise RuntimeError(f"missing required model files under {models_dir}: {model_results['missing']}")
        model_results["checked"] = True

    return {
        "repo_root": str(repo_root),
        "python": sys.executable,
        "torch": torch.__version__,
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_version": torch.version.cuda,
        "cuda_device_count": torch.cuda.device_count(),
        "cuda_device_name": torch.cuda.get_device_name(0),
        "cuda_device_capability": list(torch.cuda.get_device_capability(0)),
        "onnxruntime_providers": providers,
        "imports": import_results,
        "distributions": _distribution_versions(DISTIBUTION_NAMES),
        "ffmpeg": shutil.which("ffmpeg"),
        "models": model_results,
    }


def _parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Validate MimicMotion runtime dependencies and assets.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Path to a MimicMotion checkout")
    parser.add_argument(
        "--models-dir",
        type=Path,
        default=None,
        help="Path to the models directory; defaults to <repo-root>/models",
    )
    parser.add_argument(
        "--skip-models",
        action="store_true",
        help="Skip local model file checks and only validate the runtime stack",
    )
    return parser.parse_args()


def main() -> int:
    args = _parse_args()
    try:
        report = validate_runtime(args.repo_root, args.models_dir, skip_models=args.skip_models)
    except Exception as exc:  # pragma: no cover - surfaced to user
        print(f"[FAIL] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    print("[OK] MimicMotion runtime is ready")
    print(f"repo_root={report['repo_root']}")
    print(f"python={report['python']}")
    print(f"torch={report['torch']}")
    print(f"cuda_available={report['cuda_available']}")
    print(f"cuda_version={report['cuda_version']}")
    print(f"cuda_device_count={report['cuda_device_count']}")
    print(f"cuda_device_name={report['cuda_device_name']}")
    print(f"cuda_device_capability={report['cuda_device_capability']}")
    print(f"onnxruntime_providers={report['onnxruntime_providers']}")
    if not args.skip_models:
        print(f"models_checked={report['models']['checked']}")
        print(f"models_present={report['models']['present']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
