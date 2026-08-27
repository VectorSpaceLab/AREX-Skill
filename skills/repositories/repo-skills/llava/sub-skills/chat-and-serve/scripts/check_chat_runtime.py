#!/usr/bin/env python3
"""Inspect the LLaVA chat/serve runtime without downloading a model or starting a server.

The script checks package imports, conversation template availability, and optional
CUDA/SGLang visibility. It is safe to run from any directory.

Example:
    python scripts/check_chat_runtime.py --require-cuda
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description="Check LLaVA chat/serve imports and optional backend visibility.")
    parser.add_argument("--require-cuda", action="store_true", help="Return nonzero when CUDA is unavailable.")
    parser.add_argument("--json", action="store_true", help="Print only JSON output.")
    args = parser.parse_args()

    report = {"imports": {}, "dist": {}, "cuda": None, "sglang": None, "errors": []}
    for dist in ["llava", "torch", "torchvision", "transformers", "tokenizers", "accelerate", "gradio"]:
        try:
            report["dist"][dist] = metadata.version(dist)
        except metadata.PackageNotFoundError:
            report["errors"].append(f"missing distribution: {dist}")

    modules = [
        "llava",
        "llava.model.builder",
        "llava.mm_utils",
        "llava.conversation",
        "llava.eval.run_llava",
        "llava.serve.cli",
        "llava.serve.controller",
        "llava.serve.model_worker",
        "llava.serve.gradio_web_server",
    ]
    for module in modules:
        try:
            importlib.import_module(module)
            report["imports"][module] = True
        except Exception as exc:  # noqa: BLE001 - diagnostic script
            report["imports"][module] = False
            report["errors"].append(f"import failed for {module}: {type(exc).__name__}: {exc}")

    try:
        from llava.conversation import conv_templates

        report["templates"] = sorted(conv_templates.keys())
    except Exception as exc:  # noqa: BLE001
        report["errors"].append(f"conversation templates unavailable: {type(exc).__name__}: {exc}")

    try:
        import torch

        cuda = {
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "torch": torch.__version__,
            "torch_cuda": torch.version.cuda,
        }
        if torch.cuda.is_available():
            cuda["device0"] = torch.cuda.get_device_name(0)
            cuda["capability0"] = list(torch.cuda.get_device_capability(0))
        if args.require_cuda and not cuda["available"]:
            report["errors"].append("CUDA required but unavailable")
        report["cuda"] = cuda
    except Exception as exc:  # noqa: BLE001
        report["cuda"] = {"error": f"{type(exc).__name__}: {exc}"}
        if args.require_cuda:
            report["errors"].append("CUDA probe failed")

    try:
        importlib.import_module("sglang")
        report["sglang"] = True
    except Exception:
        report["sglang"] = False

    code = 1 if report["errors"] else 0
    text = json.dumps(report, indent=2, sort_keys=True)
    print(text if args.json else f"{text}\nSTATUS: {'PASS' if code == 0 else 'FAIL'}")
    return code


if __name__ == "__main__":
    raise SystemExit(main())
