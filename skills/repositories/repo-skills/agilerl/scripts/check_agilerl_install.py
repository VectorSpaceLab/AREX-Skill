#!/usr/bin/env python3
"""Safe AgileRL installation and optional dependency probe."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import sys

CORE_MODULES = [
    "agilerl",
    "agilerl.training",
    "agilerl.hpo",
    "agilerl.modules",
    "agilerl.networks",
    "agilerl.components",
    "agilerl.vector",
    "agilerl.wrappers",
    "agilerl.data",
    "agilerl.llm_envs",
]

OPTIONAL_MODULES = [
    "torch",
    "gymnasium",
    "pettingzoo",
    "supersuit",
    "h5py",
    "minari",
    "wandb",
    "jax",
    "transformers",
    "datasets",
    "peft",
    "vllm",
    "deepspeed",
    "bitsandbytes",
    "liger_kernel",
]


def probe_module(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
        return {"name": name, "ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"name": name, "ok": True, "version": getattr(module, "__version__", None)}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-optional", action="store_true", help="Probe optional RL/LLM dependencies too.")
    parser.add_argument("--json", action="store_true", help="Print JSON instead of a text summary.")
    args = parser.parse_args()

    report: dict[str, object] = {
        "python": sys.version.split()[0],
        "agilerl_distribution": None,
        "core_imports": [probe_module(name) for name in CORE_MODULES],
    }
    try:
        report["agilerl_distribution"] = metadata.version("agilerl")
    except Exception as exc:  # noqa: BLE001 - diagnostic tool
        report["agilerl_distribution_error"] = f"{type(exc).__name__}: {exc}"

    if args.check_optional:
        report["optional_imports"] = [probe_module(name) for name in OPTIONAL_MODULES]

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        if report.get("agilerl_distribution"):
            print(f"AgileRL distribution: {report['agilerl_distribution']}")
        else:
            print(f"AgileRL distribution: missing ({report.get('agilerl_distribution_error')})")
        for item in report["core_imports"]:  # type: ignore[index]
            status = "ok" if item["ok"] else f"missing: {item['error']}"
            print(f"core {item['name']}: {status}")
        for item in report.get("optional_imports", []):  # type: ignore[assignment]
            status = "ok" if item["ok"] else f"missing: {item['error']}"
            print(f"optional {item['name']}: {status}")

    core_ok = all(item["ok"] for item in report["core_imports"])  # type: ignore[index]
    return 0 if core_ok and report.get("agilerl_distribution") else 1


if __name__ == "__main__":
    raise SystemExit(main())
