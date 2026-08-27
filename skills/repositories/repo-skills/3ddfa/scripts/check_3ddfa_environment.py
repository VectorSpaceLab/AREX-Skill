#!/usr/bin/env python3
"""Shared 3DDFA checkout diagnostic.

This script is safe by default: it checks files, importable packages, and small
source-root imports without running native inference, training, benchmarks,
downloads, CMake, or GUI/video workflows.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Iterable

CORE_FILES = (
    "readme.md",
    "main.py",
    "mobilenet_v1.py",
    "models/phase1_wpdc_vdc.pth.tar",
    "visualize/tri.mat",
)

CONFIG_FILES = (
    "train.configs/keypoints_sim.npy",
    "train.configs/w_shp_sim.npy",
    "train.configs/w_exp_sim.npy",
    "train.configs/u_shp.npy",
    "train.configs/u_exp.npy",
    "train.configs/param_whitening.pkl",
    "train.configs/Model_PAF.pkl",
    "train.configs/pncc_code.npy",
)

TRAINING_FILES = (
    "train.py",
    "vdc_loss.py",
    "wpdc_loss.py",
    "training/train_wpdc.sh",
    "training/train_vdc.sh",
    "training/train_pdc.sh",
)

CPP_FILES = (
    "c++/CMakeLists.txt",
    "c++/demo.cpp",
    "c++/convert_to_onnx.py",
    "c++/weights/param_mean.txt",
    "c++/weights/param_std.txt",
    "c++/weights/u_base.txt",
    "c++/weights/w_shp_base.txt",
    "c++/weights/w_exp_base.txt",
)

MODULES = (
    ("torch", "torch", True),
    ("torchvision", "torchvision", True),
    ("numpy", "numpy", True),
    ("scipy", "scipy", True),
    ("opencv-python", "cv2", True),
    ("matplotlib", "matplotlib", True),
    ("cython", "Cython", False),
    ("dlib", "dlib", False),
    ("imageio", "imageio", False),
)


class Counter:
    def __init__(self) -> None:
        self.errors = 0
        self.warnings = 0

    def ok(self, label: str, detail: str = "") -> None:
        print(f"OK   {label}{': ' + detail if detail else ''}")

    def warn(self, label: str, detail: str = "") -> None:
        self.warnings += 1
        print(f"WARN {label}{': ' + detail if detail else ''}")

    def error(self, label: str, detail: str = "") -> None:
        self.errors += 1
        print(f"MISS {label}{': ' + detail if detail else ''}")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check a 3DDFA checkout for safe repo-skill workflows.")
    parser.add_argument("--repo-root", default=".", help="Path to a 3DDFA checkout.")
    parser.add_argument("--require-dlib", action="store_true", help="Treat missing Python dlib as an error.")
    parser.add_argument("--require-cython-render", action="store_true", help="Treat missing mesh_core_cython extension as an error.")
    parser.add_argument("--check-training", action="store_true", help="Also check training recipe files.")
    parser.add_argument("--check-cpp", action="store_true", help="Also check optional C++ port source files.")
    return parser.parse_args()


def check_files(root: Path, rels: Iterable[str], counter: Counter, missing_is_warning: bool = False) -> None:
    for rel in rels:
        if (root / rel).exists():
            counter.ok(rel)
        elif missing_is_warning:
            counter.warn(rel, "missing optional file")
        else:
            counter.error(rel)


def module_available(module: str) -> bool:
    try:
        return importlib.util.find_spec(module) is not None
    except Exception:
        return False


def check_modules(args: argparse.Namespace, counter: Counter) -> None:
    for display, module, required in MODULES:
        found = module_available(module)
        if found:
            counter.ok(f"module {display}")
        elif required or (display == "dlib" and args.require_dlib):
            counter.error(f"module {display}", "not importable")
        else:
            counter.warn(f"module {display}", "optional/not importable")


def check_optional_assets(root: Path, args: argparse.Namespace, counter: Counter) -> None:
    predictor = root / "models" / "shape_predictor_68_face_landmarks.dat"
    if predictor.exists():
        counter.ok("models/shape_predictor_68_face_landmarks.dat")
    else:
        counter.warn("models/shape_predictor_68_face_landmarks.dat", "needed for default dlib landmark path")

    cython_dir = root / "utils" / "cython"
    built = list(cython_dir.glob("mesh_core_cython*.so")) + list(cython_dir.glob("mesh_core_cython*.pyd"))
    if built:
        counter.ok("utils/cython/mesh_core_cython extension", ", ".join(p.name for p in built))
    elif args.require_cython_render:
        counter.error("utils/cython/mesh_core_cython extension", "not built")
    else:
        counter.warn("utils/cython/mesh_core_cython extension", "build before depth/PNCC/native render imports")

    for rel in ("test.data", "c++/weights/mb_1.onnx", "c++/weights/tiny-yolo-azface-fddb_82000.weights"):
        if (root / rel).exists():
            counter.ok(rel)
        else:
            counter.warn(rel, "external optional artifact not present")


def try_source_imports(root: Path, counter: Counter) -> None:
    sys.path.insert(0, str(root))
    try:
        import mobilenet_v1  # type: ignore
        counter.ok("source import mobilenet_v1", hasattr(mobilenet_v1, "mobilenet_1") and "mobilenet_1" or "imported")
    except Exception as exc:
        counter.error("source import mobilenet_v1", f"{type(exc).__name__}: {exc}")

    try:
        from utils.ddfa import reconstruct_vertex  # type: ignore
        counter.ok("source import utils.ddfa.reconstruct_vertex", getattr(reconstruct_vertex, "__name__", "imported"))
    except Exception as exc:
        counter.error("source import utils.ddfa", f"{type(exc).__name__}: {exc}")

    try:
        from vdc_loss import VDCLoss  # type: ignore
        from wpdc_loss import WPDCLoss  # type: ignore
        counter.ok("source import loss modules", f"{VDCLoss.__name__}, {WPDCLoss.__name__}")
    except Exception as exc:
        counter.warn("source import loss modules", f"{type(exc).__name__}: {exc}")


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    counter = Counter()

    print("3DDFA environment diagnostic")
    print("Repo root: <provided --repo-root>")
    if not root.is_dir():
        counter.error("repo root", "not a directory")
        return 1

    print("\nCore files:")
    check_files(root, CORE_FILES, counter)

    print("\n3DMM/config resources:")
    check_files(root, CONFIG_FILES, counter)

    print("\nPython modules:")
    check_modules(args, counter)

    print("\nOptional assets:")
    check_optional_assets(root, args, counter)

    if args.check_training:
        print("\nTraining/evaluation files:")
        check_files(root, TRAINING_FILES, counter, missing_is_warning=True)

    if args.check_cpp:
        print("\nC++ port files:")
        check_files(root, CPP_FILES, counter, missing_is_warning=True)

    print("\nSource import probes:")
    try_source_imports(root, counter)

    print("\nSummary:")
    print(f"  errors: {counter.errors}")
    print(f"  warnings: {counter.warnings}")
    if counter.errors:
        print("  status: required checks failed; route to troubleshooting before native workflows")
        return 1
    print("  status: required files/imports passed; review warnings for optional workflow gates")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
