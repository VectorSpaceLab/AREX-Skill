#!/usr/bin/env python3
"""Check whether the environment is ready for ScaledYOLOv4 export targets.

This helper targets the skill-owned ``runtime/`` mirror by default so it can
validate export prerequisites without depending on the original checkout.
"""

from __future__ import annotations

import argparse
import importlib.util
import platform
import sys
from pathlib import Path


def default_runtime_root() -> Path:
    here = Path(__file__).resolve()
    for parent in [here.parent, *here.parents]:
        candidate = parent / "runtime"
        if (candidate / "models" / "export.py").is_file() and (candidate / "models" / "yolo.py").is_file():
            return candidate
    raise RuntimeError("could not locate bundled runtime/ mirror containing models/export.py")


def module_available(name: str) -> tuple[bool, str]:
    spec = importlib.util.find_spec(name)
    if spec is None:
        return False, "missing"
    try:
        module = __import__(name)
        version = getattr(module, "__version__", "present")
        return True, str(version)
    except Exception as exc:  # pragma: no cover - diagnostic path
        return False, f"import failed: {exc}"


def resolve_path(base: Path, raw: str) -> Path:
    path = Path(raw.strip())
    if path.is_absolute():
        return path
    return (base / path).resolve()


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=None, help="source root used to resolve relative paths; defaults to this skill's bundled runtime/ mirror")
    parser.add_argument("--weights", type=str, default="yolov4-p5.pt", help="checkpoint path to validate")
    parser.add_argument("--img-size", nargs="+", type=int, default=[640, 640], help="input image size used for export planning")
    parser.add_argument("--batch-size", type=int, default=1)
    args = parser.parse_args()

    repo_root = (args.repo_root or default_runtime_root()).expanduser().resolve()
    if not (repo_root / "models" / "export.py").is_file():
        parser.error(f"--repo-root is not a ScaledYOLOv4 checkout: {repo_root}")

    weight_path = resolve_path(repo_root, args.weights)
    if not weight_path.is_file():
        parser.error(f"weights file not found: {weight_path}")

    if len(args.img_size) == 1:
        img_size = [args.img_size[0], args.img_size[0]]
    elif len(args.img_size) == 2:
        img_size = args.img_size
    else:
        parser.error("--img-size expects one or two integers")

    if any(x <= 0 for x in img_size):
        parser.error("--img-size values must be positive")
    if args.batch_size < 1:
        parser.error("--batch-size must be positive")

    torch_ok, torch_version = module_available("torch")
    onnx_ok, onnx_version = module_available("onnx")
    coreml_ok, coreml_version = module_available("coremltools")

    print("export environment check")
    print(f"platform: {platform.platform()}")
    print(f"python: {sys.version.split()[0]}")
    print(f"torch: {'ok' if torch_ok else 'missing'} ({torch_version})")
    print(f"onnx: {'ok' if onnx_ok else 'missing'} ({onnx_version})")
    print(f"coremltools: {'ok' if coreml_ok else 'missing'} ({coreml_version})")
    print(f"weights: {weight_path}")
    print(f"img_size: {img_size[0]} {img_size[1]}")
    print(f"batch_size: {args.batch_size}")

    if not torch_ok:
        print("missing required dependency: torch")
        return 1
    if not onnx_ok:
        print("warning: ONNX export will not be available until onnx is installed")
    if not coreml_ok:
        print("warning: CoreML export will not be available until coremltools is installed")
    if sys.platform != "darwin" and coreml_ok:
        print("warning: CoreML is typically only practical on macOS")

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
