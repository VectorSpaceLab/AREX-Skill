#!/usr/bin/env python3
"""Read-only Protenix environment checker for the generated repo skill."""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import shutil
import subprocess
import sys
from typing import Any


def result(ok: bool, **kwargs: Any) -> dict[str, Any]:
    payload = {"ok": ok}
    payload.update(kwargs)
    return payload


def check_distribution(name: str) -> dict[str, Any]:
    try:
        dist = metadata.distribution(name)
    except Exception as exc:  # noqa: BLE001
        return result(False, error=f"{type(exc).__name__}: {exc}")
    entry_points = [
        {"group": ep.group, "name": ep.name, "value": ep.value}
        for ep in dist.entry_points
    ]
    return result(
        True,
        metadata_name=dist.metadata.get("Name"),
        version=dist.version,
        summary=dist.metadata.get("Summary"),
        entry_points=entry_points,
    )


def check_import(module: str) -> dict[str, Any]:
    try:
        imported = importlib.import_module(module)
    except Exception as exc:  # noqa: BLE001
        return result(False, error=f"{type(exc).__name__}: {exc}")
    return result(True, module=module, loaded=bool(imported))


def run_command(command: list[str], timeout: int = 20) -> dict[str, Any]:
    try:
        completed = subprocess.run(command, text=True, capture_output=True, timeout=timeout, check=False)
    except FileNotFoundError as exc:
        return result(False, error=f"not found: {exc.filename}")
    except subprocess.TimeoutExpired:
        return result(False, error=f"timed out after {timeout}s")
    return result(
        completed.returncode == 0,
        returncode=completed.returncode,
        stdout=(completed.stdout or "")[:4000],
        stderr=(completed.stderr or "")[:4000],
    )


def check_torch() -> dict[str, Any]:
    try:
        import torch  # type: ignore
    except Exception as exc:  # noqa: BLE001
        return result(False, error=f"{type(exc).__name__}: {exc}")
    payload: dict[str, Any] = {
        "version": getattr(torch, "__version__", None),
        "cuda_build": getattr(getattr(torch, "version", None), "cuda", None),
        "cuda_available": False,
        "cuda_device_count": 0,
    }
    try:
        payload["cuda_available"] = bool(torch.cuda.is_available())
        payload["cuda_device_count"] = int(torch.cuda.device_count())
        if payload["cuda_available"] and payload["cuda_device_count"]:
            payload["cuda_device_0"] = torch.cuda.get_device_name(0)
            payload["cuda_capability_0"] = list(torch.cuda.get_device_capability(0))
    except Exception as exc:  # noqa: BLE001
        payload["cuda_error"] = f"{type(exc).__name__}: {exc}"
    return result(True, **payload)


def check_cli(command_name: str, timeout: int) -> dict[str, Any]:
    command_path = shutil.which(command_name)
    if not command_path:
        return result(False, error="console script is not on PATH")
    return run_command([command_path, "--help"], timeout=timeout)


def main() -> int:
    parser = argparse.ArgumentParser(description="Check Protenix package, CLI, backend, and external-tool availability without running prediction.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of a human-readable summary.")
    parser.add_argument("--skip-cli-help", action="store_true", help="Do not execute protenix --help.")
    parser.add_argument("--timeout", type=int, default=20, help="Timeout for CLI help checks in seconds.")
    args = parser.parse_args()

    modules = ["protenix", "runner.batch_inference", "configs", "torch", "Bio", "rdkit", "gemmi", "biotite"]
    optional_modules = ["cuequivariance", "deepspeed", "triton"]
    tools = ["hmmsearch", "hmmbuild", "nhmmer", "hmmalign", "kalign", "mmseqs"]

    report: dict[str, Any] = {
        "python": sys.version.replace("\n", " "),
        "distribution": check_distribution("protenix"),
        "imports": {name: check_import(name) for name in modules},
        "optional_imports": {name: check_import(name) for name in optional_modules},
        "torch": check_torch(),
        "environment": {
            "PROTENIX_ROOT_DIR_set": bool(os.environ.get("PROTENIX_ROOT_DIR")),
            "LAYERNORM_TYPE": os.environ.get("LAYERNORM_TYPE"),
            "CUTLASS_PATH_set": bool(os.environ.get("CUTLASS_PATH")),
        },
        "external_tools": {name: shutil.which(name) is not None for name in tools},
    }
    if not args.skip_cli_help:
        report["cli_help"] = check_cli("protenix", args.timeout)

    critical_ok = bool(report["distribution"]["ok"] and report["imports"]["protenix"]["ok"] and report["imports"]["runner.batch_inference"]["ok"])
    if "cli_help" in report:
        critical_ok = critical_ok and bool(report["cli_help"]["ok"])
    report["ok"] = critical_ok

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
    else:
        print(f"Protenix distribution: {'ok' if report['distribution']['ok'] else 'missing'}")
        if report["distribution"]["ok"]:
            print(f"Version: {report['distribution'].get('version')}")
        core_ok = report["imports"]["protenix"]["ok"] and report["imports"]["runner.batch_inference"]["ok"]
        print(f"Core imports: {'ok' if core_ok else 'problem'}")
        print(f"Torch: {report['torch'].get('version', 'missing')} CUDA available={report['torch'].get('cuda_available')}")
        if "cli_help" in report:
            print(f"CLI help: {'ok' if report['cli_help']['ok'] else report['cli_help'].get('error', 'problem')}")
        missing_tools = [name for name, present in report["external_tools"].items() if not present]
        if missing_tools:
            print("Missing optional external tools: " + ", ".join(missing_tools))
    return 0 if report["ok"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
