#!/usr/bin/env python3
"""Inspect whether a 3DDFA checkout is ready for Python inference.

The script is diagnostic-only: it does not import or run the native image/video
CLIs. It checks files and importable packages, then prints command suggestions
that the caller can choose to run separately.
"""
from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path
from typing import Iterable


CORE_FILES = (
    "main.py",
    "video_demo.py",
    "mobilenet_v1.py",
    "models/phase1_wpdc_vdc.pth.tar",
    "visualize/tri.mat",
)

TRAIN_CONFIG_FILES = (
    "train.configs/keypoints_sim.npy",
    "train.configs/w_shp_sim.npy",
    "train.configs/w_exp_sim.npy",
    "train.configs/u_shp.npy",
    "train.configs/u_exp.npy",
    "train.configs/param_whitening.pkl",
    "train.configs/Model_PAF.pkl",
    "train.configs/pncc_code.npy",
)

PYTHON_MODULES = (
    ("torch", "torch"),
    ("torchvision", "torchvision"),
    ("numpy", "numpy"),
    ("scipy", "scipy"),
    ("opencv-python", "cv2"),
    ("matplotlib", "matplotlib"),
    ("dlib", "dlib"),
)


class ResultCounter:
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
    parser = argparse.ArgumentParser(
        description="Check 3DDFA Python inference resources and print safe command suggestions."
    )
    parser.add_argument(
        "--repo-root",
        default=".",
        help="Path to a 3DDFA checkout (default: current directory).",
    )
    parser.add_argument(
        "--image",
        default="samples/test1.jpg",
        help="Image path to use in printed dlib-default command suggestions.",
    )
    parser.add_argument(
        "--bbox-image",
        default="samples/emma_input.jpg",
        help="Image path to use in printed bbox-only command suggestions.",
    )
    parser.add_argument(
        "--require-cython",
        action="store_true",
        help="Treat a missing compiled mesh_core_cython extension as an error instead of a warning.",
    )
    parser.add_argument(
        "--require-dlib-predictor",
        action="store_true",
        help="Treat missing models/shape_predictor_68_face_landmarks.dat as an error.",
    )
    return parser.parse_args()


def rel_exists(root: Path, rel_path: str) -> bool:
    return (root / rel_path).exists()


def check_files(root: Path, rel_paths: Iterable[str], counter: ResultCounter) -> None:
    for rel_path in rel_paths:
        if rel_exists(root, rel_path):
            counter.ok(rel_path)
        else:
            counter.error(rel_path)


def check_module(display_name: str, module_name: str, counter: ResultCounter) -> bool:
    try:
        spec = importlib.util.find_spec(module_name)
    except Exception as exc:  # pragma: no cover - environment-specific find_spec failure
        counter.warn(f"module {display_name}", f"find_spec failed: {exc}")
        return False
    if spec is None:
        counter.warn(f"module {display_name}", "not importable in this Python")
        return False
    counter.ok(f"module {display_name}")
    return True


def check_optional_assets(root: Path, args: argparse.Namespace, counter: ResultCounter) -> None:
    predictor = "models/shape_predictor_68_face_landmarks.dat"
    if rel_exists(root, predictor):
        counter.ok(predictor, "dlib landmark predictor available")
    elif args.require_dlib_predictor:
        counter.error(predictor, "required for default --dlib_landmark=true path")
    else:
        counter.warn(predictor, "missing; bbox-only inference can avoid the predictor model")

    cython_dir = root / "utils" / "cython"
    built = sorted(cython_dir.glob("mesh_core_cython*.so")) + sorted(
        cython_dir.glob("mesh_core_cython*.pyd")
    )
    if built:
        counter.ok("utils/cython/mesh_core_cython extension", ", ".join(p.name for p in built))
    elif args.require_cython:
        counter.error(
            "utils/cython/mesh_core_cython extension",
            "required by default render/depth/PNCC startup path",
        )
    else:
        counter.warn(
            "utils/cython/mesh_core_cython extension",
            "not built; native CLI render imports may fail until built",
        )

    for rel_path in ("utils/cython/setup.py", "utils/cython/mesh_core_cython.pyx"):
        if rel_exists(root, rel_path):
            counter.ok(rel_path)
        else:
            counter.warn(rel_path, "Cython build source missing")


def print_command_suggestions(root: Path, args: argparse.Namespace, dlib_importable: bool) -> None:
    smoke_script = Path(__file__).resolve().with_name("smoke_mobilenet_forward.py")
    print("\nCommand suggestions (not executed):")
    print(
        f"  python {smoke_script} --repo-root {root} --arch mobilenet_1 --num-classes 62"
    )

    bbox_image = args.bbox_image
    bbox_sidecar = root / f"{bbox_image}.bbox"
    if bbox_sidecar.exists():
        print(
            "  python main.py -f {img} --mode cpu --dlib_bbox=false --dlib_landmark=false "
            "--bbox_init=two --show_flg=false".format(img=bbox_image)
        )
    else:
        print(
            "  # Provide <image>.bbox, then use: python main.py -f <image> --mode cpu "
            "--dlib_bbox=false --dlib_landmark=false --bbox_init=two --show_flg=false"
        )

    predictor = root / "models" / "shape_predictor_68_face_landmarks.dat"
    if dlib_importable and predictor.exists():
        print(f"  python main.py -f {args.image} --mode cpu --show_flg=false")
    else:
        print(
            "  # Default detector/landmark inference needs importable dlib and "
            "models/shape_predictor_68_face_landmarks.dat"
        )

    cython_exts = list((root / "utils" / "cython").glob("mesh_core_cython*.so")) + list(
        (root / "utils" / "cython").glob("mesh_core_cython*.pyd")
    )
    if not cython_exts:
        print("  (cd utils/cython && python setup.py build_ext -i)  # build render extension")

    print("  python video_demo.py -v 0 -m cpu  # interactive camera/display demo only")
    print(
        "\nNotes: main.py imports dlib and render utilities before argument parsing; "
        "these suggestions assume diagnostics above are acceptable."
    )


def main() -> int:
    args = parse_args()
    root = Path(args.repo_root).expanduser().resolve()
    counter = ResultCounter()

    print("3DDFA Python inference diagnostic")
    print("Repo root: <provided --repo-root>")
    if not root.is_dir():
        counter.error("repo root", "not a directory")
        return 1

    print("\nCore files:")
    check_files(root, CORE_FILES, counter)

    print("\ntrain.configs resources:")
    if (root / "train.configs").is_dir():
        counter.ok("train.configs directory")
    else:
        counter.error("train.configs directory")
    check_files(root, TRAIN_CONFIG_FILES, counter)

    print("\nPython modules:")
    module_results = {
        module_name: check_module(display_name, module_name, counter)
        for display_name, module_name in PYTHON_MODULES
    }

    print("\nOptional / mode-specific assets:")
    check_optional_assets(root, args, counter)

    bbox_image = args.bbox_image
    bbox_sidecar = root / f"{bbox_image}.bbox"
    if bbox_sidecar.exists():
        counter.ok(f"{bbox_image}.bbox", "bbox-only suggestion can use this sidecar")
    else:
        counter.warn(f"{bbox_image}.bbox", "bbox-only suggestion will require a sidecar")

    print_command_suggestions(root, args, module_results.get("dlib", False))

    print("\nSummary:")
    print(f"  errors: {counter.errors}")
    print(f"  warnings: {counter.warnings}")
    if counter.errors:
        print("  status: not ready for unmodified native inference")
        return 1
    print("  status: required files found; review warnings before native inference")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
