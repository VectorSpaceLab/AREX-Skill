#!/usr/bin/env python3
"""Check whether a Python environment can operate SketchCode workflows.

The check is safe by default: it imports dependencies and optional SketchCode
runtime classes, validates optional model files, and can run a tiny compiler or
image-preprocessing smoke only when the required local inputs are supplied.
"""

import argparse
import importlib
import sys
from pathlib import Path
from typing import Optional

DEPENDENCIES = [
    ("keras", "Keras"),
    ("tensorflow", "TensorFlow"),
    ("cv2", "OpenCV"),
    ("nltk", "NLTK"),
    ("numpy", "NumPy"),
    ("PIL", "Pillow"),
]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Check SketchCode dependency and runtime import readiness.")
    parser.add_argument("--sketchcode-root", help="Optional SketchCode checkout root containing src/classes/ or a src directory containing classes/.")
    parser.add_argument("--model-json-file", help="Optional model JSON file to verify exists.")
    parser.add_argument("--model-weights-file", help="Optional weights .h5 file to verify exists.")
    parser.add_argument("--image", help="Optional PNG file for ImagePreprocessor.get_img_features smoke when runtime imports work.")
    return parser


def _add_runtime_path(root_arg: Optional[str]) -> Optional[Path]:
    if not root_arg:
        return None
    root = Path(root_arg).expanduser().resolve()
    if (root / "src" / "classes").is_dir():
        sys.path.insert(0, str(root / "src"))
        return root / "src"
    if (root / "classes").is_dir():
        sys.path.insert(0, str(root))
        return root
    raise SystemExit("Could not find classes/ under --sketchcode-root or --sketchcode-root/src.")


def _version(module) -> str:
    return str(getattr(module, "__version__", "version-unknown"))


def _check_import(module_name: str, label: str) -> bool:
    try:
        module = importlib.import_module(module_name)
    except Exception as exc:
        print(f"FAIL import {label} ({module_name}): {type(exc).__name__}: {exc}")
        return False
    print(f"OK import {label} ({module_name}) version={_version(module)}")
    return True


def _check_file(path_arg: Optional[str], label: str) -> bool:
    if not path_arg:
        print(f"SKIP {label}: not provided")
        return True
    path = Path(path_arg).expanduser()
    if path.is_file():
        print(f"OK {label}: exists")
        return True
    print(f"FAIL {label}: missing {path}")
    return False


def _check_runtime(image_arg: Optional[str]) -> bool:
    ok = True
    try:
        from classes.inference.Compiler import Compiler  # type: ignore
        html = Compiler("default").compile(["<START>", "header", "{", "btn-active", "}", "<END>"])
        if html and html != "HTML Parsing Error":
            print("OK SketchCode Compiler tiny smoke")
        else:
            print("FAIL SketchCode Compiler tiny smoke returned parsing error")
            ok = False
    except Exception as exc:
        print(f"FAIL import/smoke classes.inference.Compiler: {type(exc).__name__}: {exc}")
        ok = False

    for module_name in [
        "classes.inference.Evaluator",
        "classes.dataset.Dataset",
        "classes.dataset.ImagePreprocessor",
        "classes.model.SketchCodeModel",
    ]:
        try:
            importlib.import_module(module_name)
            print(f"OK import {module_name}")
        except Exception as exc:
            print(f"FAIL import {module_name}: {type(exc).__name__}: {exc}")
            ok = False

    if image_arg:
        try:
            from classes.dataset.ImagePreprocessor import ImagePreprocessor  # type: ignore
            arr = ImagePreprocessor().get_img_features(str(Path(image_arg).expanduser()))
            print(f"OK ImagePreprocessor smoke shape={getattr(arr, 'shape', None)}")
        except Exception as exc:
            print(f"FAIL ImagePreprocessor smoke: {type(exc).__name__}: {exc}")
            ok = False
    return ok


def main() -> int:
    args = build_parser().parse_args()
    print(f"Python: {sys.version.split()[0]}")
    runtime = _add_runtime_path(args.sketchcode_root)
    if runtime:
        print("SketchCode runtime path added for imports")
    else:
        print("SketchCode runtime path not provided; importing classes from current Python path if available")

    ok = True
    for module_name, label in DEPENDENCIES:
        ok = _check_import(module_name, label) and ok
    ok = _check_file(args.model_json_file, "model JSON") and ok
    ok = _check_file(args.model_weights_file, "model weights") and ok
    ok = _check_runtime(args.image) and ok
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
