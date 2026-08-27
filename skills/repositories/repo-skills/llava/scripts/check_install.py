#!/usr/bin/env python3
"""Check a LLaVA Python environment without downloading models or running servers.

Example:
    python scripts/check_install.py --require-cuda
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from typing import Any


def probe(require_cuda: bool = False) -> tuple[int, dict[str, Any]]:
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {},
        "imports": {},
        "cuda": None,
        "errors": [],
    }

    for dist in [
        "llava",
        "torch",
        "torchvision",
        "transformers",
        "tokenizers",
        "accelerate",
        "gradio",
    ]:
        try:
            report["distributions"][dist] = metadata.version(dist)
        except metadata.PackageNotFoundError:
            report["errors"].append(f"missing distribution: {dist}")

    for module in [
        "llava",
        "llava.model.builder",
        "llava.mm_utils",
        "llava.conversation",
        "llava.eval.run_llava",
        "llava.serve.cli",
    ]:
        try:
            imported = importlib.import_module(module)
            report["imports"][module] = bool(imported)
        except Exception as exc:  # noqa: BLE001 - diagnostic should report import errors
            report["imports"][module] = False
            report["errors"].append(f"import failed for {module}: {type(exc).__name__}: {exc}")

    try:
        import torch

        cuda = {
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
        }
        if torch.cuda.is_available():
            cuda["device0"] = torch.cuda.get_device_name(0)
            cuda["capability0"] = list(torch.cuda.get_device_capability(0))
            torch.empty((1,), device="cuda")
            cuda["allocation"] = "passed"
        report["cuda"] = cuda
        if require_cuda and not cuda["available"]:
            report["errors"].append("CUDA was required but torch.cuda.is_available() is false")
    except Exception as exc:  # noqa: BLE001
        report["cuda"] = {"error": f"{type(exc).__name__}: {exc}"}
        if require_cuda:
            report["errors"].append("CUDA probe failed")

    return (1 if report["errors"] else 0), report


def main() -> int:
    parser = argparse.ArgumentParser(description="Check LLaVA importability and optional CUDA visibility.")
    parser.add_argument("--require-cuda", action="store_true", help="Return nonzero if CUDA is unavailable.")
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON only.")
    args = parser.parse_args()

    code, report = probe(require_cuda=args.require_cuda)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(json.dumps(report, indent=2, sort_keys=True))
        print("STATUS:", "PASS" if code == 0 else "FAIL")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
