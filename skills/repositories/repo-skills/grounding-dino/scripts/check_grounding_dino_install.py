#!/usr/bin/env python3
"""Check a GroundingDINO installation without loading weights or downloading files."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import sys
from pathlib import Path


def status(label: str, ok: bool, detail: str = "") -> None:
    marker = "OK" if ok else "FAIL"
    suffix = f" - {detail}" if detail else ""
    print(f"[{marker}] {label}{suffix}")


def optional_import(name: str) -> str:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - report optional import diagnostics
        return f"missing ({type(exc).__name__}: {exc})"
    version = getattr(module, "__version__", None)
    return f"available{f' {version}' if version else ''}"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, help="Optional GroundingDINO config file to load with SLConfig.")
    args = parser.parse_args()

    failed = False

    try:
        version = metadata.version("groundingdino")
        status("distribution groundingdino", True, version)
    except metadata.PackageNotFoundError:
        status("distribution groundingdino", False, "not installed")
        return 1

    required_modules = [
        "groundingdino",
        "groundingdino.util.inference",
        "groundingdino.util.slconfig",
        "groundingdino.models",
        "groundingdino.datasets.cocogrounding_eval",
        "groundingdino.util.vl_utils",
        "groundingdino.util.box_ops",
    ]
    for module_name in required_modules:
        try:
            importlib.import_module(module_name)
            status(f"import {module_name}", True)
        except Exception as exc:  # noqa: BLE001 - diagnostics tool
            failed = True
            status(f"import {module_name}", False, f"{type(exc).__name__}: {exc}")

    try:
        import torch

        status("torch", True, f"{torch.__version__}, cuda_available={torch.cuda.is_available()}")
    except Exception as exc:  # noqa: BLE001
        failed = True
        status("torch", False, f"{type(exc).__name__}: {exc}")

    try:
        from groundingdino.util import inference

        for name in ["load_model", "load_image", "predict", "annotate"]:
            status(f"signature {name}", True, str(inspect.signature(getattr(inference, name))))
        status("signature Model", True, str(inspect.signature(inference.Model)))
    except Exception as exc:  # noqa: BLE001
        failed = True
        status("inference signatures", False, f"{type(exc).__name__}: {exc}")

    if args.config:
        try:
            from groundingdino.util.slconfig import SLConfig

            config = SLConfig.fromfile(str(args.config))
            detail = f"modelname={config.modelname}, backbone={config.backbone}, num_queries={config.num_queries}"
            status("config load", True, detail)
        except Exception as exc:  # noqa: BLE001
            failed = True
            status("config load", False, f"{type(exc).__name__}: {exc}")

    print("Optional workflow dependencies:")
    for name in ["fiftyone", "gradio", "huggingface_hub", "pycocotools", "supervision"]:
        print(f"- {name}: {optional_import(name)}")

    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
