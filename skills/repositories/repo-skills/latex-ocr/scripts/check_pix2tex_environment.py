#!/usr/bin/env python3
"""Check a pix2tex/LaTeX-OCR runtime without downloading checkpoints.

Example:
    python check_pix2tex_environment.py --check-api --check-train-imports
"""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib import metadata


def check_import(name: str) -> dict:
    try:
        importlib.import_module(name)
        return {"name": name, "ok": True, "error": None}
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check pix2tex environment without loading model weights")
    parser.add_argument("--check-api", action="store_true", help="also check API optional dependencies")
    parser.add_argument("--check-gui-imports", action="store_true", help="also check GUI optional dependency imports")
    parser.add_argument("--check-train-imports", action="store_true", help="also check training optional dependency imports")
    args = parser.parse_args()

    modules = ["pix2tex", "torch", "PIL", "cv2", "timm", "transformers", "tokenizers", "albumentations"]
    if args.check_api:
        modules += ["fastapi", "uvicorn", "streamlit", "st_img_pastebutton", "pix2tex.api.app"]
    if args.check_gui_imports:
        modules += ["PyQt6", "PyQt6.QtWebEngineWidgets", "pynput", "screeninfo", "latex2sympy2"]
    if args.check_train_imports:
        modules += ["imagesize", "torchtext", "Levenshtein", "wandb"]

    report = {
        "python": sys.version,
        "executable": sys.executable,
        "distributions": {d: version(d) for d in ["pix2tex", "torch", "torchvision", "timm", "transformers", "albumentations", "fastapi", "streamlit"]},
        "imports": [check_import(m) for m in modules],
        "cli": {"pix2tex": shutil.which("pix2tex")},
        "torch": {},
    }
    try:
        import torch

        report["torch"] = {
            "version": torch.__version__,
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()),
        }
    except Exception as exc:  # noqa: BLE001
        report["torch"] = {"error": f"{type(exc).__name__}: {exc}"}

    if shutil.which("pix2tex"):
        proc = subprocess.run(["pix2tex", "--help"], text=True, capture_output=True, timeout=20)
        report["cli"]["help_returncode"] = proc.returncode
        report["cli"]["help_first_line"] = proc.stdout.splitlines()[0] if proc.stdout else proc.stderr.splitlines()[0] if proc.stderr else ""

    print(json.dumps(report, indent=2, sort_keys=True))
    failed = [item for item in report["imports"] if not item["ok"]]
    return 1 if failed else 0


if __name__ == "__main__":
    raise SystemExit(main())
