#!/usr/bin/env python3
"""Check dependencies and optional backends for Chinese-LLaMA-Alpaca workflows.

This helper is safe by default: it imports packages, reports versions, checks
CUDA visibility through torch when available, and never downloads models,
launches services, starts training, or reads private credentials.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from dataclasses import asdict, dataclass
from typing import Iterable

CORE_MODULES = ["torch", "transformers", "peft", "sentencepiece"]
TRAINING_MODULES = ["datasets", "sklearn"]
API_MODULES = ["fastapi", "uvicorn", "shortuuid", "pydantic"]
EVAL_MODULES = ["pandas", "numpy", "tqdm"]
OPTIONAL_MODULES = ["gradio", "langchain", "faiss", "openai", "xformers", "deepspeed"]


@dataclass
class ModuleStatus:
    name: str
    ok: bool
    version: str | None = None
    error: str | None = None


def check_module(name: str) -> ModuleStatus:
    try:
        module = importlib.import_module(name)
        return ModuleStatus(name=name, ok=True, version=str(getattr(module, "__version__", "unknown")))
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return ModuleStatus(name=name, ok=False, error=f"{type(exc).__name__}: {exc}")


def torch_backend() -> dict[str, object]:
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        return {"torch_imported": False, "error": f"{type(exc).__name__}: {exc}"}
    info: dict[str, object] = {
        "torch_imported": True,
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "cuda_device_count": int(torch.cuda.device_count()),
    }
    if torch.cuda.is_available():
        info["cuda_device_0"] = torch.cuda.get_device_name(0)
        info["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
        try:
            torch.empty((1,), device="cuda")
            info["cuda_allocation"] = "ok"
        except Exception as exc:  # noqa: BLE001
            info["cuda_allocation"] = f"failed: {type(exc).__name__}: {exc}"
    return info


def parse_args(argv: Iterable[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Check Chinese-LLaMA-Alpaca dependency and backend readiness.")
    parser.add_argument(
        "--include-optional",
        action="store_true",
        help="Also probe optional Gradio/LangChain/OpenAI/xFormers/DeepSpeed modules.",
    )
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON instead of text.")
    return parser.parse_args(argv)


def main(argv: Iterable[str] | None = None) -> int:
    args = parse_args(argv)
    modules = CORE_MODULES + TRAINING_MODULES + API_MODULES + EVAL_MODULES
    if args.include_optional:
        modules += OPTIONAL_MODULES
    results = [check_module(m) for m in modules]
    backend = torch_backend()
    payload = {
        "python": sys.version.split()[0],
        "modules": [asdict(r) for r in results],
        "backend": backend,
    }
    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"Python: {payload['python']}")
        for r in results:
            if r.ok:
                print(f"OK     {r.name}: {r.version}")
            else:
                print(f"MISSING {r.name}: {r.error}")
        print("Backend:")
        for key, value in backend.items():
            print(f"  {key}: {value}")
    required_missing = [r.name for r in results if not r.ok and r.name in CORE_MODULES]
    return 1 if required_missing else 0


if __name__ == "__main__":
    raise SystemExit(main())
