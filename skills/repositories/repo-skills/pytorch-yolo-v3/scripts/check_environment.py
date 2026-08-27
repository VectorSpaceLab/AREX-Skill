#!/usr/bin/env python3
"""Safe environment and import preflight for pytorch-yolo-v3 workflows.

This helper checks Python dependencies, optional CUDA visibility, and, when a
user checkout is provided, top-level repository module imports plus cfg/class
presence. It never downloads weights, opens images/videos/cameras, or runs model
inference.
"""

from __future__ import annotations

import argparse
import importlib
import os
from pathlib import Path
import sys
from typing import Dict, List, Sequence

DEPENDENCIES = ["torch", "cv2", "numpy", "pandas", "PIL", "matplotlib"]
REPO_MODULES = ["bbox", "preprocess", "util", "darknet"]


class EnvFailure(RuntimeError):
    """Raised for actionable environment failures."""


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Check pytorch-yolo-v3 Python dependencies and optional checkout imports without weights or inference."
    )
    parser.add_argument("--repo-root", default=None, help="Optional user checkout/source tree containing darknet.py and related modules.")
    parser.add_argument("--expect-cuda", action="store_true", help="Fail if PyTorch does not report CUDA availability.")
    parser.add_argument("--check-files", action="store_true", help="When --repo-root is set, check expected cfg/data/palette files exist.")
    return parser


def import_dependency(name: str):
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        raise EnvFailure(f"dependency import failed for {name!r}: {type(exc).__name__}: {exc}") from exc
    version = getattr(module, "__version__", None)
    print(f"PASS dependency {name}: {version or 'imported'}")
    return module


def check_cuda(torch_module, expect_cuda: bool) -> None:
    available = bool(torch_module.cuda.is_available())
    print(f"INFO torch.cuda.is_available: {available}")
    if available:
        try:
            print(f"INFO torch.cuda.device_count: {torch_module.cuda.device_count()}")
            print(f"INFO torch.version.cuda: {torch_module.version.cuda}")
        except Exception as exc:
            print(f"WARNING CUDA query failed: {type(exc).__name__}: {exc}")
    if expect_cuda and not available:
        raise EnvFailure("--expect-cuda was set but torch.cuda.is_available() is false")


def check_repo_imports(repo_root: Path) -> None:
    if not repo_root.is_dir():
        raise EnvFailure(f"--repo-root is not a directory: {repo_root}")
    sys.path.insert(0, str(repo_root))
    for module_name in REPO_MODULES:
        sys.modules.pop(module_name, None)
    for module_name in REPO_MODULES:
        try:
            module = importlib.import_module(module_name)
        except Exception as exc:
            raise EnvFailure(
                f"repository module import failed for {module_name!r}. Check --repo-root and installed dependencies: {type(exc).__name__}: {exc}"
            ) from exc
        module_file = getattr(module, "__file__", "<unknown>")
        print(f"PASS repo module {module_name}: {module_file}")


def check_expected_files(repo_root: Path) -> None:
    expected = [
        "darknet.py",
        "detect.py",
        "video_demo.py",
        "video_demo_half.py",
        "cam_demo.py",
        "cfg/yolov3.cfg",
        "data/coco.names",
        "pallete",
    ]
    missing: List[str] = []
    for rel in expected:
        path = repo_root / rel
        if path.exists():
            print(f"PASS file {rel}")
        else:
            print(f"WARNING missing expected file {rel}")
            missing.append(rel)
    weights = repo_root / "yolov3.weights"
    if weights.exists():
        print("INFO local yolov3.weights exists")
    else:
        print("INFO local yolov3.weights not found; full detection needs user-supplied weights")
    if missing:
        raise EnvFailure("missing expected repository files: " + ", ".join(missing))


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        modules: Dict[str, object] = {}
        for dep in DEPENDENCIES:
            modules[dep] = import_dependency(dep)
        check_cuda(modules["torch"], args.expect_cuda)
        if args.repo_root:
            repo_root = Path(args.repo_root).expanduser().resolve()
            check_repo_imports(repo_root)
            if args.check_files:
                check_expected_files(repo_root)
    except EnvFailure as exc:
        print(f"FAIL {exc}", file=sys.stderr)
        return 1
    print("PASS pytorch-yolo-v3 environment preflight completed without downloads, weights, GUI, camera, video, or inference")
    return 0


if __name__ == "__main__":
    os.environ.setdefault("PYTHONDONTWRITEBYTECODE", "1")
    raise SystemExit(main())
