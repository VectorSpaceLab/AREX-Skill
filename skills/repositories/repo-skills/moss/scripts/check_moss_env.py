#!/usr/bin/env python3
"""Safe MOSS environment probe.

This helper checks Python imports and optional CUDA availability without
loading MOSS checkpoints, downloading model files, starting services, or running
training. Use it when a future task needs to verify that a MOSS source checkout
or Hugging Face `trust_remote_code` environment is ready for local work.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional


def add_repo_root(repo_root: Optional[str]) -> None:
    if repo_root:
        root = Path(repo_root).expanduser().resolve()
        sys.path.insert(0, str(root))


def import_status(module: str) -> Dict[str, object]:
    try:
        imported = importlib.import_module(module)
        return {"module": module, "ok": True, "file": getattr(imported, "__file__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def cuda_status(require_cuda: bool) -> Dict[str, object]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"torch_imported": False, "ok": not require_cuda, "error": f"{type(exc).__name__}: {exc}"}

    status: Dict[str, object] = {
        "torch_imported": True,
        "torch_version": getattr(torch, "__version__", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()),
        "cuda_version": getattr(torch.version, "cuda", None),
    }
    if torch.cuda.is_available():
        try:
            tensor = torch.ones(2, device="cuda")
            status.update({
                "cuda_tensor_sum": float(tensor.sum().item()),
                "device_name": torch.cuda.get_device_name(0),
            })
        except Exception as exc:  # pragma: no cover - diagnostic path
            status["cuda_error"] = f"{type(exc).__name__}: {exc}"
    status["ok"] = (not require_cuda) or bool(status.get("cuda_available")) and "cuda_error" not in status
    return status


def main() -> int:
    parser = argparse.ArgumentParser(description="Check MOSS imports and optional CUDA without loading checkpoints.")
    parser.add_argument("--repo-root", help="Optional MOSS source checkout root to add to sys.path for local-module checks.")
    parser.add_argument("--require-cuda", action="store_true", help="Return nonzero if CUDA is unavailable or a tiny CUDA tensor check fails.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable report.")
    args = parser.parse_args()

    add_repo_root(args.repo_root)
    modules: List[str] = [
        "torch",
        "transformers",
        "accelerate",
        "huggingface_hub",
        "models.configuration_moss",
        "models.modeling_moss",
        "models.tokenization_moss",
    ]
    imports = [import_status(module) for module in modules]
    cuda = cuda_status(args.require_cuda)
    ok = all(item["ok"] for item in imports) and bool(cuda.get("ok"))
    report = {"ok": ok, "imports": imports, "cuda": cuda}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("MOSS environment check:", "PASS" if ok else "FAIL")
        for item in imports:
            print(f"- {item['module']}: {'ok' if item['ok'] else item['error']}")
        print(f"- CUDA available: {cuda.get('cuda_available')} devices={cuda.get('device_count')} version={cuda.get('cuda_version')}")
        if cuda.get("device_name"):
            print(f"- CUDA device[0]: {cuda['device_name']}")
    return 0 if ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
