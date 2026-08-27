#!/usr/bin/env python3
"""Safe rLLM runtime smoke check.

This script imports core rLLM modules, inventories CLI commands from the lazy
Click group, and reports optional backend dependencies. It does not contact
providers, download datasets, build snapshots, or start training.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata
import importlib.util
import json
import sys
from typing import Any


def _version(dist: str) -> str | None:
    try:
        return importlib.metadata.version(dist)
    except importlib.metadata.PackageNotFoundError:
        return None


def _try_exec(label: str, code: str) -> dict[str, Any]:
    try:
        ns: dict[str, Any] = {}
        exec(code, ns, ns)
        return {"label": label, "ok": True, "error": None}
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return {"label": label, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _optional_module(name: str) -> dict[str, Any]:
    return {"module": name, "available": importlib.util.find_spec(name) is not None}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable report")
    args = parser.parse_args()

    report: dict[str, Any] = {
        "python": f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}",
        "distributions": {
            "rllm": _version("rllm"),
            "rllm-model-gateway": _version("rllm-model-gateway"),
        },
        "core_imports": [
            _try_exec("rllm decorators/types", "from rllm import rollout, evaluator, Task, Episode, Trajectory, Step"),
            _try_exec("AgentConfig", "from rllm.types import AgentConfig"),
            _try_exec("evaluation outputs", "from rllm.eval.types import EvalOutput, Signal"),
            _try_exec("trainer", "from rllm.trainer import AgentTrainer"),
            _try_exec("gateway", "from rllm_model_gateway import GatewayClient, GatewayConfig, TraceRecord"),
        ],
        "optional_modules": [_optional_module(m) for m in ["torch", "tinker", "verl", "fireworks", "cupy", "agentcore"]],
        "cli_commands": [],
        "torch_cuda": None,
    }

    try:
        from rllm.cli.main import _LazyGroup

        report["cli_commands"] = sorted(name for name in _LazyGroup._COMMANDS if name != "setup")
    except Exception as exc:  # noqa: BLE001
        report["cli_commands_error"] = f"{type(exc).__name__}: {exc}"

    if importlib.util.find_spec("torch") is not None:
        try:
            import torch

            cuda = torch.cuda.is_available()
            report["torch_cuda"] = {
                "available": bool(cuda),
                "torch_version": getattr(torch, "__version__", None),
                "cuda_version": getattr(torch.version, "cuda", None),
                "device_count": torch.cuda.device_count() if cuda else 0,
                "device_0": torch.cuda.get_device_name(0) if cuda else None,
            }
        except Exception as exc:  # noqa: BLE001
            report["torch_cuda"] = {"available": False, "error": f"{type(exc).__name__}: {exc}"}

    ok = all(item["ok"] for item in report["core_imports"])
    report["ok"] = ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print("rLLM smoke check")
        print("================")
        print(f"Python: {report['python']}")
        for dist, ver in report["distributions"].items():
            print(f"{dist}: {ver or 'not installed'}")
        print("\nCore imports:")
        for item in report["core_imports"]:
            status = "OK" if item["ok"] else f"FAIL ({item['error']})"
            print(f"- {item['label']}: {status}")
        print("\nCLI commands:", ", ".join(report.get("cli_commands") or []) or "unavailable")
        print("\nOptional modules:")
        for item in report["optional_modules"]:
            print(f"- {item['module']}: {'present' if item['available'] else 'missing'}")
        if report["torch_cuda"] is not None:
            print("\nTorch CUDA:", report["torch_cuda"])
        print("\nOverall:", "OK" if ok else "FAILED")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
