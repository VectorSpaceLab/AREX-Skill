#!/usr/bin/env python3
"""Report AgileRL LLM optional dependency availability without loading models."""

from __future__ import annotations

import argparse
import importlib
import json

MODULES = [
    "agilerl",
    "agilerl.llm_envs",
    "agilerl.training.train_llm",
    "torch",
    "transformers",
    "datasets",
    "peft",
    "vllm",
    "deepspeed",
    "bitsandbytes",
    "liger_kernel",
    "accelerate",
]


def probe(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"name": name, "ok": True, "version": getattr(module, "__version__", None)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    report: dict[str, object] = {"modules": [probe(name) for name in MODULES]}
    try:
        import torch
        report["torch_cuda"] = {
            "available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()),
            "cuda_version": torch.version.cuda,
        }
    except Exception as exc:  # noqa: BLE001 - diagnostic helper
        report["torch_cuda"] = {"error": f"{type(exc).__name__}: {exc}"}

    required = [item for item in report["modules"] if item["name"] in {"agilerl", "agilerl.llm_envs"}]  # type: ignore[index]
    report["ok"] = all(item["ok"] for item in required)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        for item in report["modules"]:  # type: ignore[index]
            print(f"{item['name']}: {'ok' if item['ok'] else item['error']}")
        print(f"torch_cuda: {report['torch_cuda']}")
        print(f"overall: {'ok' if report['ok'] else 'failed'}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
