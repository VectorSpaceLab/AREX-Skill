#!/usr/bin/env python3
"""Check Diffusers import, metadata, optional backends, and CLI availability."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import shutil
import subprocess
import sys


OPTIONAL_MODULES = [
    "torch",
    "transformers",
    "accelerate",
    "peft",
    "datasets",
    "safetensors",
    "onnx",
    "onnxruntime",
    "bitsandbytes",
    "gguf",
    "torchao",
]


def module_status(name: str) -> dict[str, object]:
    try:
        module = importlib.import_module(name)
    except Exception as exc:
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    version = getattr(module, "__version__", None)
    if version is None:
        try:
            version = metadata.version(name)
        except Exception:
            version = None
    return {"ok": True, "version": version}


def cli_probe(timeout: int) -> dict[str, object]:
    executable = shutil.which("diffusers-cli")
    if executable is None:
        return {"ok": False, "error": "diffusers-cli not found on PATH"}
    result = {"ok": True, "path": executable}
    for command in ([executable, "--help"], [executable, "env"]):
        key = "help" if command[-1] == "--help" else "env"
        try:
            completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
        except Exception as exc:
            result[key] = {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
            continue
        result[key] = {
            "ok": completed.returncode == 0,
            "returncode": completed.returncode,
            "stdout_head": completed.stdout.splitlines()[:12],
            "stderr_head": completed.stderr.splitlines()[:12],
        }
    return result


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--skip-cli", action="store_true", help="Skip diffusers-cli help/env checks.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout for CLI probes in seconds.")
    args = parser.parse_args()

    report: dict[str, object] = {"python": sys.version.split()[0], "modules": {}}
    report["modules"]["diffusers"] = module_status("diffusers")
    try:
        report["distribution"] = {"diffusers": metadata.version("diffusers")}
    except Exception as exc:
        report["distribution"] = {"diffusers_error": f"{type(exc).__name__}: {exc}"}

    for name in OPTIONAL_MODULES:
        report["modules"][name] = module_status(name)

    torch_status = report["modules"].get("torch", {})
    if isinstance(torch_status, dict) and torch_status.get("ok"):
        import torch

        report["torch_backend"] = {
            "cuda_available": torch.cuda.is_available(),
            "cuda_device_count": torch.cuda.device_count() if torch.cuda.is_available() else 0,
            "cuda_version": getattr(torch.version, "cuda", None),
        }
    else:
        report["torch_backend"] = {"cuda_available": False, "note": "torch unavailable"}

    if not args.skip_cli:
        report["diffusers_cli"] = cli_probe(args.timeout)

    diffusers_ok = bool(report["modules"]["diffusers"].get("ok"))
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Python: {report['python']}")
        for name, status in report["modules"].items():
            if status.get("ok"):
                print(f"{name}: ok {status.get('version') or ''}".rstrip())
            else:
                print(f"{name}: missing/error - {status.get('error')}")
        print(f"Torch backend: {report['torch_backend']}")
        if "diffusers_cli" in report:
            print(f"diffusers-cli: {report['diffusers_cli']}")
    return 0 if diffusers_ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
