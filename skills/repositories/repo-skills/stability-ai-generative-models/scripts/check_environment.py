#!/usr/bin/env python3
"""Check whether a Python environment can inspect generative-models APIs safely.

This helper does not load checkpoints, start demos, download models, or require CUDA.
It reports importability and optional backend facts for the public `sgm` package.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import importlib.util
import json
from typing import Any, Dict, Iterable

REQUIRED_IMPORTS = [
    "sgm",
    "sgm.inference.api",
    "sgm.models.diffusion",
    "sgm.models.autoencoder",
    "sgm.modules.encoders.modules",
]

OPTIONAL_IMPORTS = [
    "torch",
    "pytorch_lightning",
    "omegaconf",
    "einops",
    "safetensors",
    "open_clip",
    "transformers",
    "imwatermark",
    "cv2",
    "streamlit",
    "gradio",
    "rembg",
]

DISTRIBUTIONS = ["sgm", "torch", "pytorch-lightning", "omegaconf"]


def import_status(name: str) -> Dict[str, Any]:
    try:
        spec = importlib.util.find_spec(name)
    except ModuleNotFoundError as exc:
        return {"available": False, "imports": False, "error": f"{type(exc).__name__}: {exc}"}
    status: Dict[str, Any] = {"available": spec is not None}
    if spec is None:
        status["imports"] = False
        return status
    try:
        importlib.import_module(name)
        status["imports"] = True
    except Exception as exc:  # pragma: no cover - environment dependent
        status["imports"] = False
        status["error"] = f"{type(exc).__name__}: {exc}"
    return status


def dist_versions(names: Iterable[str]) -> Dict[str, Any]:
    out: Dict[str, Any] = {}
    for name in names:
        try:
            out[name] = metadata.version(name)
        except metadata.PackageNotFoundError:
            out[name] = None
    return out


def torch_backend() -> Dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception as exc:  # pragma: no cover - environment dependent
        return {"available": False, "error": f"{type(exc).__name__}: {exc}"}
    result: Dict[str, Any] = {
        "available": True,
        "version": getattr(torch, "__version__", None),
        "cuda_version": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
    }
    if result["cuda_available"]:
        result["cuda_device_name_0"] = torch.cuda.get_device_name(0)
        result["cuda_capability_0"] = torch.cuda.get_device_capability(0)
    return result


def collect() -> Dict[str, Any]:
    return {
        "required_imports": {name: import_status(name) for name in REQUIRED_IMPORTS},
        "optional_imports": {name: import_status(name) for name in OPTIONAL_IMPORTS},
        "distributions": dist_versions(DISTRIBUTIONS),
        "torch_backend": torch_backend(),
        "notes": [
            "This check never loads model checkpoints or starts UI servers.",
            "CUDA unavailable is acceptable for static API/config inspection but not for checkpoint-backed sampling.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Exit non-zero when a required import is unavailable or fails to import.",
    )
    args = parser.parse_args()
    report = collect()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("generative-models environment check")
        for name, status in report["required_imports"].items():
            state = "ok" if status.get("imports") else "missing/failed"
            print(f"required {name}: {state}")
        torch_info = report["torch_backend"]
        print(
            "torch: "
            f"available={torch_info.get('available')} "
            f"version={torch_info.get('version')} "
            f"cuda_available={torch_info.get('cuda_available')}"
        )
    if args.strict:
        for status in report["required_imports"].values():
            if not status.get("imports"):
                return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
