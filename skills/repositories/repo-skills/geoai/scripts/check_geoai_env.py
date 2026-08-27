#!/usr/bin/env python3
"""Read-only GeoAI environment smoke check.

Examples:
    python scripts/check_geoai_env.py
    python scripts/check_geoai_env.py --check-cli --check-cuda
    python scripts/check_geoai_env.py --pipeline-config pipeline.json --json

This helper imports the installed package and optionally checks CLI help,
CUDA availability, selected optional modules, and a pipeline config. It does
not download data/models, start services, run training, or modify files.
"""

from __future__ import annotations

import argparse
import importlib
import json
import subprocess
import sys
from pathlib import Path
from typing import Any


def _module_status(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
        return {"module": module, "ok": True, "file": getattr(imported, "__file__", None)}
    except Exception as exc:  # noqa: BLE001 - diagnostic script
        return {"module": module, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def _run_cli(args: list[str]) -> dict[str, Any]:
    proc = subprocess.run(
        [sys.executable, "-m", "geoai.cli", *args],
        text=True,
        capture_output=True,
        timeout=30,
    )
    output = (proc.stdout or proc.stderr or "").strip().splitlines()
    return {
        "command": [sys.executable, "-m", "geoai.cli", *args],
        "returncode": proc.returncode,
        "first_lines": output[:8],
    }


def _check_cuda() -> dict[str, Any]:
    status: dict[str, Any] = {"requested": True}
    try:
        import torch
    except Exception as exc:  # noqa: BLE001
        status.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
        return status

    status.update(
        {
            "torch_version": getattr(torch, "__version__", None),
            "torch_cuda_runtime": getattr(torch.version, "cuda", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "device_count": int(torch.cuda.device_count()) if hasattr(torch, "cuda") else 0,
        }
    )
    if torch.cuda.is_available():
        try:
            status["device0"] = torch.cuda.get_device_name(0)
            status["capability0"] = torch.cuda.get_device_capability(0)
            torch.empty((1,), device="cuda")
            status["allocation"] = "ok"
            status["ok"] = True
        except Exception as exc:  # noqa: BLE001
            status.update({"ok": False, "error": f"{type(exc).__name__}: {exc}"})
    else:
        status["ok"] = False
        status["error"] = "torch imported, but CUDA is not available"
    return status


def _check_pipeline_config(path: str) -> dict[str, Any]:
    p = Path(path)
    if not p.exists():
        return {"path": path, "ok": False, "error": "config path does not exist"}
    try:
        from geoai.pipeline import load_pipeline

        pipe = load_pipeline(str(p))
        return {
            "path": str(p),
            "ok": True,
            "name": pipe.name,
            "max_workers": pipe.max_workers,
            "steps": [repr(step) for step in pipe.steps],
        }
    except Exception as exc:  # noqa: BLE001
        return {"path": str(p), "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-cli", action="store_true", help="Run safe GeoAI CLI help checks.")
    parser.add_argument("--check-cuda", action="store_true", help="Import torch and allocate a tiny CUDA tensor if available.")
    parser.add_argument("--check-agents", action="store_true", help="Probe optional GeoAI agent dependencies.")
    parser.add_argument("--pipeline-config", help="Load a GeoAI JSON/YAML pipeline config without running it.")
    parser.add_argument("--module", action="append", default=[], help="Additional module to import, repeatable.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of human-readable text.")
    args = parser.parse_args(argv)

    result: dict[str, Any] = {"checks": {}}
    failures: list[str] = []

    pkg = _module_status("geoai")
    result["checks"]["geoai_import"] = pkg
    if pkg["ok"]:
        import geoai

        result["geoai_version"] = getattr(geoai, "__version__", None)
        result["lazy_symbol_count"] = len(getattr(geoai, "__all__", []))
    else:
        failures.append("geoai import failed")

    modules = list(args.module)
    if args.check_agents:
        modules.extend(["strands", "geoai.agents.geo_agents", "geoai.agents.map_tools", "geoai.agents.catalog_tools"])
    if modules:
        result["checks"]["modules"] = [_module_status(m) for m in modules]
        failures.extend([m["module"] for m in result["checks"]["modules"] if not m["ok"]])

    if args.check_cli:
        cli_checks = [_run_cli(["--help"]), _run_cli(["pipeline", "--help"])]
        result["checks"]["cli"] = cli_checks
        failures.extend(["geoai cli help" for c in cli_checks if c["returncode"] != 0])

    if args.check_cuda:
        cuda = _check_cuda()
        result["checks"]["cuda"] = cuda
        if not cuda.get("ok"):
            failures.append("cuda")

    if args.pipeline_config:
        pipe = _check_pipeline_config(args.pipeline_config)
        result["checks"]["pipeline_config"] = pipe
        if not pipe.get("ok"):
            failures.append("pipeline config")

    result["ok"] = not failures
    result["failures"] = failures

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"GeoAI environment smoke: {'OK' if result['ok'] else 'ISSUES'}")
        if "geoai_version" in result:
            print(f"  geoai version: {result['geoai_version']}")
            print(f"  lazy symbols: {result.get('lazy_symbol_count')}")
        for name, value in result["checks"].items():
            if name == "geoai_import":
                print(f"  import geoai: {'ok' if value['ok'] else value.get('error')}")
            elif name == "modules":
                for item in value:
                    print(f"  import {item['module']}: {'ok' if item['ok'] else item.get('error')}")
            elif name == "cli":
                for item in value:
                    print(f"  cli {' '.join(item['command'][-2:])}: rc={item['returncode']}; {item['first_lines'][:1]}")
            elif name == "cuda":
                print(f"  cuda: {'ok' if value.get('ok') else value.get('error')} ({value})")
            elif name == "pipeline_config":
                print(f"  pipeline config: {'ok' if value.get('ok') else value.get('error')} ({value.get('name', value.get('path'))})")
        if failures:
            print("Failures:", ", ".join(failures), file=sys.stderr)

    return 0 if result["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
