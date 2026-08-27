#!/usr/bin/env python3
"""Check OpenChat package imports, model registry facts, and optional CUDA.

This diagnostic is safe by default: it does not download model weights, start a
server, call external APIs, or run benchmarks. Run it from any directory with the
Python environment that should use OpenChat.
"""

from __future__ import annotations

import argparse
import importlib
import json
import sys
from importlib import metadata
from typing import Any


def dist_version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(module: str) -> dict[str, Any]:
    try:
        mod = importlib.import_module(module)
        return {"module": module, "ok": True, "file": getattr(mod, "__file__", None)}
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def registry_summary() -> dict[str, Any]:
    try:
        from ochat.config import MODEL_CONFIG_MAP
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}

    models: dict[str, Any] = {}
    for key, cfg in MODEL_CONFIG_MAP.items():
        models[key] = {
            "serving_aliases": list(cfg.serving_aliases),
            "model_max_context": cfg.model_max_context,
            "has_hf_chat_template": bool(cfg.hf_chat_template),
        }
    return {"ok": True, "models": models}


def cuda_summary() -> dict[str, Any]:
    try:
        import torch
    except Exception as exc:  # pragma: no cover - diagnostic path
        return {"ok": False, "error": f"could not import torch: {type(exc).__name__}: {exc}"}

    result: dict[str, Any] = {
        "ok": True,
        "torch_version": getattr(torch, "__version__", None),
        "torch_cuda_version": getattr(torch.version, "cuda", None),
        "cuda_available": bool(torch.cuda.is_available()),
        "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
    }
    if torch.cuda.is_available():
        try:
            device = torch.empty((1,), device="cuda")
            result.update(
                {
                    "device0_name": torch.cuda.get_device_name(0),
                    "device0_capability": list(torch.cuda.get_device_capability(0)),
                    "tiny_tensor_device": str(device.device),
                }
            )
        except Exception as exc:  # pragma: no cover - diagnostic path
            result["ok"] = False
            result["allocation_error"] = f"{type(exc).__name__}: {exc}"
    return result


def build_report(check_cuda: bool) -> dict[str, Any]:
    modules = [
        "ochat",
        "ochat.config",
        "ochat.serving.openai_api_protocol",
        "ochat.serving.openai_api_server",
        "ochat.evaluation.run_eval",
        "ochat.evaluation.match_answer",
    ]
    report: dict[str, Any] = {
        "python": sys.version.split()[0],
        "distributions": {
            name: dist_version(name)
            for name in ["ochat", "torch", "transformers", "vllm", "ray", "fastapi", "openai", "flash-attn"]
        },
        "imports": [import_status(module) for module in modules],
        "model_registry": registry_summary(),
    }
    if check_cuda:
        report["cuda"] = cuda_summary()
    return report


def report_ok(report: dict[str, Any], require_cuda: bool) -> bool:
    if any(not item.get("ok") for item in report["imports"]):
        return False
    if not report["model_registry"].get("ok"):
        return False
    if require_cuda and not report.get("cuda", {}).get("cuda_available"):
        return False
    if require_cuda and not report.get("cuda", {}).get("ok", False):
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check OpenChat imports and optional CUDA availability.")
    parser.add_argument("--check-cuda", action="store_true", help="Also verify torch CUDA availability and allocate a tiny CUDA tensor.")
    parser.add_argument("--require-cuda", action="store_true", help="Exit non-zero unless CUDA is available and the tiny tensor allocation succeeds.")
    parser.add_argument("--json", action="store_true", help="Print full JSON diagnostics instead of a concise summary.")
    args = parser.parse_args()

    check_cuda = args.check_cuda or args.require_cuda
    report = build_report(check_cuda=check_cuda)
    ok = report_ok(report, require_cuda=args.require_cuda)

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"ochat distribution: {report['distributions'].get('ochat')}")
        for item in report["imports"]:
            status = "ok" if item.get("ok") else f"FAIL ({item.get('error')})"
            print(f"import {item['module']}: {status}")
        registry = report["model_registry"]
        if registry.get("ok"):
            print("model types: " + ", ".join(sorted(registry["models"])))
        else:
            print(f"model registry: FAIL ({registry.get('error')})")
        if check_cuda:
            cuda = report.get("cuda", {})
            print(f"cuda available: {cuda.get('cuda_available')} ({cuda.get('device_count', 0)} device(s))")
            if cuda.get("device0_name"):
                print(f"device0: {cuda['device0_name']} capability={cuda.get('device0_capability')}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
