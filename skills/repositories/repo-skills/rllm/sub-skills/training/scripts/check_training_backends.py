#!/usr/bin/env python3
"""Report rLLM optional training backend readiness without launching training."""

from __future__ import annotations

import argparse
import importlib.util
import json
from typing import Any


def module_available(name: str) -> bool:
    return importlib.util.find_spec(name) is not None


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "imports": {
            "rllm.trainer.AgentTrainer": False,
            "rllm_model_gateway": False,
        },
        "optional_modules": {m: module_available(m) for m in ["tinker", "verl", "fireworks", "cupy", "agentcore"]},
        "torch": None,
    }

    try:
        from rllm.trainer import AgentTrainer  # noqa: F401

        report["imports"]["rllm.trainer.AgentTrainer"] = True
    except Exception as exc:  # noqa: BLE001
        report["imports"]["rllm.trainer.AgentTrainer_error"] = f"{type(exc).__name__}: {exc}"

    try:
        import rllm_model_gateway  # noqa: F401

        report["imports"]["rllm_model_gateway"] = True
    except Exception as exc:  # noqa: BLE001
        report["imports"]["rllm_model_gateway_error"] = f"{type(exc).__name__}: {exc}"

    if module_available("torch"):
        try:
            import torch

            cuda = torch.cuda.is_available()
            report["torch"] = {
                "version": getattr(torch, "__version__", None),
                "cuda_version": getattr(torch.version, "cuda", None),
                "cuda_available": bool(cuda),
                "device_count": torch.cuda.device_count() if cuda else 0,
                "device_0": torch.cuda.get_device_name(0) if cuda else None,
            }
        except Exception as exc:  # noqa: BLE001
            report["torch"] = {"error": f"{type(exc).__name__}: {exc}"}

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("rLLM training backend readiness")
        print("Core imports:")
        for name, value in report["imports"].items():
            print(f"- {name}: {value}")
        print("Optional modules:")
        for name, available in report["optional_modules"].items():
            print(f"- {name}: {'present' if available else 'missing'}")
        print("Torch:", report["torch"])
    return 0 if report["imports"].get("rllm.trainer.AgentTrainer") else 1


if __name__ == "__main__":
    raise SystemExit(main())
