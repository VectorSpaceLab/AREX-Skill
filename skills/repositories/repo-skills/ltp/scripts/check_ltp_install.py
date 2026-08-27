#!/usr/bin/env python3
"""Safe LTP install/API probe.

This script checks imports, package versions, sentence splitting, selected
ltp_extension utilities, ltp_core CRF construction, and optional CUDA visibility.
It does not download Hugging Face models, run training, or build Rust crates.

Examples:
  python scripts/check_ltp_install.py --json
  python scripts/check_ltp_install.py --check-cuda
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys
from typing import Any, Dict


def version(dist: str) -> str | None:
    try:
        return metadata.version(dist)
    except metadata.PackageNotFoundError:
        return None


def main() -> int:
    parser = argparse.ArgumentParser(description="Check LTP imports and lightweight runtime facts.")
    parser.add_argument("--check-cuda", action="store_true", help="also inspect torch CUDA availability and allocate one tiny tensor when available")
    parser.add_argument("--json", action="store_true", help="emit JSON instead of human-readable lines")
    args = parser.parse_args()

    result: Dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {
            "ltp": version("ltp"),
            "ltp-core": version("ltp-core"),
            "ltp-extension": version("ltp-extension"),
            "torch": version("torch"),
            "transformers": version("transformers"),
            "huggingface-hub": version("huggingface-hub"),
        },
        "imports": {},
        "smoke": {},
        "cuda": None,
        "errors": [],
    }

    for module in ["ltp", "ltp_core", "ltp_extension"]:
        try:
            imported = importlib.import_module(module)
            result["imports"][module] = {"ok": True, "module": getattr(imported, "__name__", module)}
        except Exception as exc:  # pragma: no cover - diagnostics only
            result["imports"][module] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            result["errors"].append(f"import {module} failed: {exc}")

    try:
        from ltp import StnSplit

        result["smoke"]["stn_split"] = StnSplit().split("汤姆生病了。他去了医院。")
    except Exception as exc:  # pragma: no cover
        result["errors"].append(f"StnSplit smoke failed: {exc}")

    try:
        from ltp_extension.algorithms import get_entities

        result["smoke"]["get_entities"] = get_entities(["B-Nh", "I-Nh", "O", "S-Ns"])
    except Exception as exc:  # pragma: no cover
        result["errors"].append(f"get_entities smoke failed: {exc}")

    try:
        from ltp_core.models.nn.crf import CRF

        result["smoke"]["crf_repr"] = repr(CRF(3))
    except Exception as exc:  # pragma: no cover
        result["errors"].append(f"CRF smoke failed: {exc}")

    if args.check_cuda:
        try:
            import torch

            cuda: Dict[str, Any] = {
                "torch": torch.__version__,
                "torch_cuda": torch.version.cuda,
                "available": bool(torch.cuda.is_available()),
                "device_count": int(torch.cuda.device_count()),
            }
            if torch.cuda.is_available():
                cuda["device_0"] = torch.cuda.get_device_name(0)
                cuda["capability_0"] = list(torch.cuda.get_device_capability(0))
                torch.empty((1,), device="cuda")
                cuda["tiny_allocation"] = "ok"
            result["cuda"] = cuda
        except Exception as exc:  # pragma: no cover
            result["cuda"] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            result["errors"].append(f"CUDA smoke failed: {exc}")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"Python: {result['python']}")
        for name, val in result["distributions"].items():
            print(f"{name}: {val or 'not installed'}")
        for name, info in result["imports"].items():
            print(f"import {name}: {'OK' if info.get('ok') else info.get('error')}")
        for name, val in result["smoke"].items():
            print(f"{name}: {val}")
        if result["cuda"] is not None:
            print(f"cuda: {result['cuda']}")
        if result["errors"]:
            print("Errors:")
            for error in result["errors"]:
                print(f"- {error}")

    return 0 if not result["errors"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
