#!/usr/bin/env python3
"""Check pix2tex CLI and selected imports without loading OCR weights."""
from __future__ import annotations

import argparse
import importlib
import json
import shutil
import subprocess
import sys
from importlib import metadata


def main() -> int:
    parser = argparse.ArgumentParser(description="Check pix2tex CLI without running OCR inference")
    parser.add_argument("--import-cli-module", action="store_true", help="import pix2tex.cli to catch dependency issues; does not instantiate LatexOCR")
    args = parser.parse_args()

    report = {
        "python": sys.version,
        "pix2tex_version": None,
        "pix2tex_cli_path": shutil.which("pix2tex"),
        "help": None,
        "imports": [],
    }
    try:
        report["pix2tex_version"] = metadata.version("pix2tex")
    except metadata.PackageNotFoundError:
        report["imports"].append({"name": "pix2tex distribution", "ok": False, "error": "not installed"})

    if report["pix2tex_cli_path"]:
        proc = subprocess.run(["pix2tex", "--help"], text=True, capture_output=True, timeout=20)
        report["help"] = {"returncode": proc.returncode, "first_lines": proc.stdout.splitlines()[:12], "stderr": proc.stderr.splitlines()[:5]}
    else:
        report["help"] = {"returncode": None, "error": "pix2tex entry point not found on PATH"}

    modules = ["pix2tex"]
    if args.import_cli_module:
        modules += ["pix2tex.cli", "torch", "timm", "transformers", "tokenizers", "albumentations"]
    for name in modules:
        try:
            importlib.import_module(name)
            report["imports"].append({"name": name, "ok": True, "error": None})
        except Exception as exc:  # noqa: BLE001
            report["imports"].append({"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"})

    print(json.dumps(report, indent=2, sort_keys=True))
    return 0 if report["help"] and report["help"].get("returncode") == 0 and all(item["ok"] for item in report["imports"]) else 1


if __name__ == "__main__":
    raise SystemExit(main())
