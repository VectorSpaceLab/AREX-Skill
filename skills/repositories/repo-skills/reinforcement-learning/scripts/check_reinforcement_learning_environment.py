#!/usr/bin/env python3
"""Check dependencies/backends needed by the reinforcement-learning skill.

This script is self-contained. It does not import source repository files, open
render windows, download Atari ROMs, log in to W&B, or run training.
"""
from __future__ import annotations

import argparse
import importlib
import json
from importlib.metadata import PackageNotFoundError, version
from typing import Any


def dist_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "missing"


def import_status(module: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(module)
        return {"module": module, "ok": True, "version": getattr(mod, "__version__", None)}
    except Exception as exc:  # noqa: BLE001 - report diagnostic without hiding type
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    parser.add_argument("--include-optional-cuda", action="store_true", help="probe CUDA if torch imports")
    args = parser.parse_args()

    modules = ["torch", "torchvision", "gymnasium", "ale_py", "numpy", "pygame", "cv2", "wandb", "moviepy", "envpool"]
    dists = ["torch", "torchvision", "gymnasium", "ale-py", "numpy", "matplotlib", "pygame", "opencv-python-headless", "wandb", "moviepy", "envpool"]
    imports = [import_status(m) for m in modules]

    torch_backend: dict[str, Any] = {"checked": False}
    if any(item["module"] == "torch" and item["ok"] for item in imports):
        import torch

        x = torch.tensor([[1.0, 2.0], [3.0, 4.0]])
        torch_backend = {
            "checked": True,
            "version": torch.__version__,
            "cuda_runtime": torch.version.cuda,
            "cpu_tensor_sum": float((x @ x).sum().item()),
        }
        if args.include_optional_cuda:
            torch_backend.update(
                {
                    "cuda_available": bool(torch.cuda.is_available()),
                    "cuda_device_count": int(torch.cuda.device_count()),
                }
            )
            if torch.cuda.is_available():
                torch_backend["cuda_device_0"] = torch.cuda.get_device_name(0)
                torch_backend["cuda_capability_0"] = torch.cuda.get_device_capability(0)

    result = {
        "status": "ok" if all(item["ok"] for item in imports) else "missing-dependencies",
        "distributions": {d: dist_version(d) for d in dists},
        "imports": imports,
        "torch_backend": torch_backend,
        "notes": [
            "Atari ROM availability is not checked.",
            "W&B credentials/network are not checked.",
            "Rendering/display availability is not checked.",
            "Full training or benchmark convergence is not checked.",
        ],
    }

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"status: {result['status']}")
        print("distributions:")
        for name, val in result["distributions"].items():
            print(f"  {name}: {val}")
        print("imports:")
        for item in imports:
            print(f"  {item['module']}: {'ok' if item['ok'] else item['error']}")
        print("torch_backend:", json.dumps(torch_backend, sort_keys=True))
        for note in result["notes"]:
            print(f"note: {note}")

    if result["status"] != "ok":
        raise SystemExit(1)


if __name__ == "__main__":
    main()
