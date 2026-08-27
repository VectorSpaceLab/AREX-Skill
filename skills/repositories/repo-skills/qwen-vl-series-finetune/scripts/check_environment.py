#!/usr/bin/env python3
"""Print a compact, safe inspection summary for the Qwen-VL finetune skill."""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata


def _version(name: str) -> str:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return "missing"


def _probe(module_name: str) -> dict[str, str]:
    try:
        importlib.import_module(module_name)
        return {"status": "ok"}
    except Exception as exc:  # noqa: BLE001
        return {"status": "error", "error": f"{type(exc).__name__}: {exc}"}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON only")
    parser.add_argument("--with-gradio", action="store_true", help="Also probe gradio")
    parser.add_argument("--with-qwen-vl-utils", action="store_true", help="Also probe qwen_vl_utils")
    args = parser.parse_args()

    report = {
        "python": sys.version.split()[0],
        "torch": _version("torch"),
        "transformers": _version("transformers"),
        "trl": _version("trl"),
        "peft": _version("peft"),
        "deepspeed": _version("deepspeed"),
        "bitsandbytes": _version("bitsandbytes"),
        "liger_kernel": _version("liger-kernel"),
        "cuda": {"available": None, "device_count": None, "version": None},
        "imports": {
            "torch": _probe("torch"),
            "transformers": _probe("transformers"),
            "trl": _probe("trl"),
            "peft": _probe("peft"),
            "deepspeed": _probe("deepspeed"),
        },
    }

    try:
        import torch

        report["cuda"] = {
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
            "version": getattr(torch.version, "cuda", None),
        }
    except Exception as exc:  # noqa: BLE001
        report["cuda"] = {"available": False, "device_count": 0, "version": None, "error": f"{type(exc).__name__}: {exc}"}

    if args.with_gradio:
        report["imports"]["gradio"] = _probe("gradio")
    if args.with_qwen_vl_utils:
        report["imports"]["qwen_vl_utils"] = _probe("qwen_vl_utils")

    payload = json.dumps(report, indent=None if args.json else 2, sort_keys=True)
    print(payload)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
