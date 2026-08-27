#!/usr/bin/env python3
"""Safe Flair package environment diagnostic.

The script imports only installed Python packages and prints version/backend/cache
facts. It does not load pretrained Flair models, datasets, or dictionaries and
therefore should not download resources.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import platform
import sys
import traceback
from typing import Any

REQUIRED_IMPORTS = [
    "flair",
    "torch",
    "transformers",
    "flair.data",
    "flair.tokenization",
    "flair.splitter",
    "flair.embeddings",
    "flair.models",
    "flair.trainers",
    "flair.nn",
]

OPTIONAL_IMPORTS = [
    "spacy",
    "scispacy",
    "pyab3p",
    "onnx",
    "onnxruntime",
    "gensim",
    "bpemb",
    "sentencepiece",
]

DISTRIBUTIONS = [
    "flair",
    "torch",
    "transformers",
    "sentence-transformers",
    "huggingface-hub",
    "spacy",
    "scispacy",
    "pyab3p",
    "onnx",
    "onnxruntime",
    "gensim",
    "bpemb",
]


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(name: str) -> dict[str, Any]:
    try:
        module = importlib.import_module(name)
        return {"ok": True, "module": name, "version": getattr(module, "__version__", None)}
    except Exception as exc:  # noqa: BLE001 - diagnostics should report all import failures.
        return {"ok": False, "module": name, "error": f"{type(exc).__name__}: {exc}"}


def collect(*, check_imports: bool) -> dict[str, Any]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "platform": platform.platform(),
        "environment": {
            "FLAIR_DEVICE": os.environ.get("FLAIR_DEVICE"),
            "FLAIR_CACHE_ROOT": os.environ.get("FLAIR_CACHE_ROOT"),
            "TRANSFORMERS_OFFLINE": os.environ.get("TRANSFORMERS_OFFLINE"),
            "HF_HUB_OFFLINE": os.environ.get("HF_HUB_OFFLINE"),
        },
        "distributions": {name: dist_version(name) for name in DISTRIBUTIONS},
        "required_imports": [],
        "optional_imports": [],
        "torch": {},
        "flair": {},
        "onnxruntime": {},
        "downloads_attempted": False,
    }

    if check_imports:
        report["required_imports"] = [import_status(name) for name in REQUIRED_IMPORTS]
        report["optional_imports"] = [import_status(name) for name in OPTIONAL_IMPORTS]

    try:
        import torch

        report["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "cuda_version": getattr(torch.version, "cuda", None),
        }
        if torch.cuda.is_available():
            report["torch"]["cuda_device_names"] = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
    except Exception as exc:  # noqa: BLE001
        report["torch"] = {"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc(limit=4)}

    try:
        import flair

        report["flair"] = {
            "version": getattr(flair, "__version__", None),
            "device": str(getattr(flair, "device", "unknown")),
            "cache_root": str(getattr(flair, "cache_root", "unknown")),
        }
    except Exception as exc:  # noqa: BLE001
        report["flair"] = {"error": f"{type(exc).__name__}: {exc}", "traceback": traceback.format_exc(limit=4)}

    try:
        import onnxruntime

        report["onnxruntime"] = {"available_providers": list(onnxruntime.get_available_providers())}
    except Exception as exc:  # noqa: BLE001
        report["onnxruntime"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    required_failures = [entry for entry in report.get("required_imports", []) if not entry.get("ok")]
    report["ok"] = not required_failures and "error" not in report.get("flair", {}) and "error" not in report.get("torch", {})
    return report


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Collect safe Flair package environment diagnostics.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text summary.")
    parser.add_argument("--check-imports", action="store_true", help="Import required/optional Flair-related modules and report status.")
    args = parser.parse_args(argv)

    report = collect(check_imports=args.check_imports)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"python: {report['python']}")
        print(f"platform: {report['platform']}")
        print(f"flair: {report['flair']}")
        print(f"torch: {report['torch']}")
        print(f"onnxruntime: {report['onnxruntime']}")
        if args.check_imports:
            print("required imports:")
            for item in report["required_imports"]:
                marker = "ok" if item.get("ok") else "FAIL"
                print(f"  {marker}: {item['module']} {item.get('error', '')}")
            print("optional imports:")
            for item in report["optional_imports"]:
                marker = "ok" if item.get("ok") else "missing/failed"
                print(f"  {marker}: {item['module']} {item.get('error', '')}")
    return 0 if report.get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
