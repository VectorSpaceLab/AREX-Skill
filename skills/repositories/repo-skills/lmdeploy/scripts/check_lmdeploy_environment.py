#!/usr/bin/env python3
"""Safe LMDeploy environment diagnostic for agents.

This helper imports LMDeploy, reports package/config facts, checks optional
modules, and optionally runs CLI help commands. It never downloads model weights,
starts a server, or runs inference.

Examples:
  python scripts/check_lmdeploy_environment.py --include-cli
  python scripts/check_lmdeploy_environment.py --json
"""
from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import inspect
import json
import shutil
import subprocess
import sys
from dataclasses import asdict, is_dataclass


def version(name: str) -> str | None:
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def import_status(name: str) -> dict:
    try:
        module = importlib.import_module(name)
        return {"ok": True, "version": version(name), "file": getattr(module, "__file__", None)}
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}


def run_help(command: list[str], timeout: int) -> dict:
    exe = shutil.which(command[0]) if command else None
    if not exe and command and command[0] == "lmdeploy":
        command = [sys.executable, "-m", "lmdeploy", *command[1:]]
    elif exe:
        command = [exe, *command[1:]]
    try:
        proc = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        return {
            "command": command,
            "returncode": proc.returncode,
            "stdout_first_line": (proc.stdout or "").splitlines()[:1],
            "stderr_first_line": (proc.stderr or "").splitlines()[:1],
            "ok": proc.returncode == 0,
        }
    except Exception as exc:
        return {"command": command, "ok": False, "error": f"{type(exc).__name__}: {exc}"}


def dataclass_defaults(cls) -> dict:
    try:
        obj = cls()
    except Exception as exc:
        return {"error": f"{type(exc).__name__}: {exc}"}
    if is_dataclass(obj):
        data = asdict(obj)
    else:
        data = dict(getattr(obj, "__dict__", {}))
    safe = {}
    for key, value in data.items():
        if isinstance(value, (str, int, float, bool, type(None))):
            safe[key] = value
        elif isinstance(value, (list, tuple)):
            safe[key] = list(value)
        elif isinstance(value, dict):
            safe[key] = value
        else:
            safe[key] = repr(value)
    return safe


def collect(include_cli: bool, timeout: int) -> dict:
    report = {
        "python": sys.version.split()[0],
        "packages": {},
        "imports": {},
        "api": {},
        "torch": {},
        "cli": [],
        "notes": [],
    }
    for dist in ["lmdeploy", "torch", "transformers", "fastapi", "pydantic", "mmengine-lite", "xgrammar", "peft", "rdkit"]:
        report["packages"][dist] = version(dist)
    for module in ["lmdeploy", "torch", "transformers", "fastapi", "pydantic", "mmengine", "xgrammar", "peft", "rdkit"]:
        report["imports"][module] = import_status(module)

    if report["imports"]["lmdeploy"]["ok"]:
        import lmdeploy
        from lmdeploy import GenerationConfig, PytorchEngineConfig, TurbomindEngineConfig, pipeline
        from lmdeploy.messages import VisionConfig

        report["api"]["lmdeploy_version"] = getattr(lmdeploy, "__version__", None)
        report["api"]["pipeline_signature"] = str(inspect.signature(pipeline))
        report["api"]["generation_config_defaults"] = dataclass_defaults(GenerationConfig)
        report["api"]["pytorch_engine_defaults"] = dataclass_defaults(PytorchEngineConfig)
        report["api"]["turbomind_engine_defaults"] = dataclass_defaults(TurbomindEngineConfig)
        report["api"]["vision_config_defaults"] = dataclass_defaults(VisionConfig)

    if report["imports"]["torch"]["ok"]:
        import torch
        report["torch"] = {
            "version": getattr(torch, "__version__", None),
            "cuda_available": bool(torch.cuda.is_available()),
            "cuda_version": getattr(getattr(torch, "version", None), "cuda", None),
            "device_count": int(torch.cuda.device_count()) if torch.cuda.is_available() else 0,
        }

    if include_cli:
        commands = [
            ["lmdeploy", "--help"],
            ["lmdeploy", "chat", "--help"],
            ["lmdeploy", "serve", "api_server", "--help"],
            ["lmdeploy", "serve", "proxy", "--help"],
            ["lmdeploy", "lite", "auto_awq", "--help"],
            ["lmdeploy", "lite", "smooth_quant", "--help"],
        ]
        report["cli"] = [run_help(command, timeout) for command in commands]

    if not report["imports"].get("rdkit", {}).get("ok"):
        report["notes"].append("rdkit is optional for many LLM/VLM workflows but may be required for chemistry-specific model/media paths.")
    if report["imports"].get("lmdeploy", {}).get("ok") and not report["packages"].get("lmdeploy"):
        report["notes"].append("lmdeploy imports but distribution metadata is missing; verify the active Python environment.")
    return report


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect an LMDeploy install without loading model weights.")
    parser.add_argument("--include-cli", action="store_true", help="Run safe lmdeploy --help commands.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a text summary.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout per CLI help command in seconds.")
    args = parser.parse_args()

    report = collect(args.include_cli, args.timeout)
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        print(f"LMDeploy package: {report['packages'].get('lmdeploy')}")
        print(f"LMDeploy import: {report['imports']['lmdeploy']['ok']}")
        print(f"Torch CUDA: {report.get('torch', {}).get('cuda_available')} ({report.get('torch', {}).get('cuda_version')})")
        if report["api"].get("pipeline_signature"):
            print(f"pipeline: {report['api']['pipeline_signature']}")
        for item in report.get("cli", []):
            print(f"CLI {' '.join(item.get('command', []))}: {'ok' if item.get('ok') else 'failed'}")
        for note in report.get("notes", []):
            print(f"Note: {note}")
    return 0 if report["imports"].get("lmdeploy", {}).get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
