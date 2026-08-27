#!/usr/bin/env python3
"""Inspect local document/PDF/LaTeX backends used by GPT Academic."""
from __future__ import annotations

import argparse
import importlib.util
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

MODULES = {"pymupdf/fitz": "fitz", "PyPDF2": "PyPDF2", "python-docx": "docx", "latex2mathml": "latex2mathml", "markdown": "markdown", "llama_index.core": "llama_index.core", "llama_parse": "llama_parse", "arxiv": "arxiv", "nougat-ocr optional": "nougat"}
COMMANDS = ["pdflatex", "latexdiff", "ffmpeg"]


def setup_repo(repo_root: str | None):
    if not repo_root:
        return {}
    root = Path(repo_root).resolve()
    if (root / "toolbox.py").exists():
        sys.path.insert(0, str(root))
        os.chdir(root)
    try:
        from toolbox import get_conf
        keys = ["DOC2X_API_KEY", "GROBID_URLS", "MATHPIX_APPID", "MATHPIX_APPKEY"]
        values = get_conf(*keys)
        return {k: bool(v) for k, v in zip(keys, values)}
    except Exception:
        return {}


def module_status(module_name: str) -> str:
    return "present" if importlib.util.find_spec(module_name) is not None else "missing"


def command_status(command: str):
    path = shutil.which(command)
    if not path:
        return {"status": "missing", "path": None}
    try:
        proc = subprocess.run([command, "--version"], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, timeout=5)
    except Exception as exc:  # noqa: BLE001
        return {"status": "present", "path": path, "version_probe": f"{type(exc).__name__}: {exc}"}
    return {"status": "present", "path": path, "version_probe": proc.stdout.splitlines()[:2]}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--repo-root", help="optional GPT Academic checkout root for config presence checks")
    args = parser.parse_args()
    conf_presence = setup_repo(args.repo_root)
    result = {"modules": {label: module_status(mod) for label, mod in MODULES.items()}, "commands": {cmd: command_status(cmd) for cmd in COMMANDS}, "credentials_present": {"DOC2X_API_KEY_env": bool(os.environ.get("DOC2X_API_KEY")), "MATHPIX_APPID_env": bool(os.environ.get("MATHPIX_APPID")), "MATHPIX_APPKEY_env": bool(os.environ.get("MATHPIX_APPKEY")), **conf_presence}, "notes": ["NOUGAT is optional and may require a large model download plus GPU/CPU runtime.", "DOC2X and Mathpix checks report presence only; values are never printed.", "pdflatex and latexdiff are required only for LaTeX rebuild/diff PDF workflows."]}
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
