#!/usr/bin/env python3
"""Probe quip-miner package and optional backend availability.

This helper is side-effect-light: it imports modules, checks the console command,
and optionally performs a tiny CUDA allocation when CuPy and a device are
available. It does not connect to validators, read credentials, or run mining.
"""
from __future__ import annotations

import argparse
import json
import shutil
import subprocess
import sys
from importlib import metadata
from pathlib import Path
from typing import Any


def _try_import(name: str) -> tuple[bool, str | None]:
    try:
        __import__(name)
    except Exception as exc:  # noqa: BLE001 - report import reason to operator
        return False, f"{type(exc).__name__}: {exc}"
    return True, None


def _cli_help() -> dict[str, Any]:
    exe = shutil.which("quip-miner")
    if not exe:
        companion = Path(sys.executable).with_name("quip-miner")
        exe = str(companion) if companion.exists() else None
    if not exe:
        return {"available": False, "error": "quip-miner not found on PATH or next to sys.executable"}
    try:
        proc = subprocess.run(
            [exe, "--help"],
            text=True,
            capture_output=True,
            timeout=15,
            check=False,
        )
    except Exception as exc:  # noqa: BLE001
        return {"available": False, "path": exe, "error": f"{type(exc).__name__}: {exc}"}
    return {
        "available": proc.returncode == 0,
        "path": exe,
        "returncode": proc.returncode,
        "mentions_commands": all(cmd in proc.stdout for cmd in ("bootstrap", "cpu", "gpu", "qpu", "keygen")),
        "stderr": proc.stderr.strip(),
    }


def _cuda_probe(allocate: bool) -> dict[str, Any]:
    ok, err = _try_import("cupy")
    result: dict[str, Any] = {"import": ok}
    if not ok:
        result["error"] = err
        return result
    import cupy as cp  # type: ignore[import-not-found]

    result["cupy_version"] = getattr(cp, "__version__", None)
    try:
        count = int(cp.cuda.runtime.getDeviceCount())
        result["device_count"] = count
    except Exception as exc:  # noqa: BLE001
        result["device_count_error"] = f"{type(exc).__name__}: {exc}"
        return result
    if allocate and result.get("device_count", 0) > 0:
        try:
            cp.zeros(1)
            result["tiny_allocation"] = True
        except Exception as exc:  # noqa: BLE001
            result["tiny_allocation"] = False
            result["allocation_error"] = f"{type(exc).__name__}: {exc}"
    return result


def collect(allocate_cuda: bool = True) -> dict[str, Any]:
    try:
        dist_version = metadata.version("quip-protocol")
    except metadata.PackageNotFoundError:
        dist_version = None
    imports = {
        name: _try_import(name)
        for name in (
            "quip_cli",
            "shared.miner_config",
            "shared.keystore_hybrid",
            "substrate.telemetry_process",
            "CPU.sa_stream",
            "GPU.cuda_stream",
            "GPU.metal_stream",
            "GPU.modal_sampler",
            "QPU.dwave_miner",
        )
    }
    modal_available = None
    if imports["GPU.modal_sampler"][0]:
        try:
            from GPU.modal_sampler import GPU_AVAILABLE  # type: ignore[import-not-found]
            modal_available = bool(GPU_AVAILABLE)
        except Exception:  # noqa: BLE001
            modal_available = None
    return {
        "python": sys.version.split()[0],
        "distribution": {"name": "quip-protocol", "version": dist_version},
        "imports": {k: {"ok": v[0], "error": v[1]} for k, v in imports.items()},
        "cli": _cli_help(),
        "cuda": _cuda_probe(allocate=allocate_cuda),
        "modal_available": modal_available,
        "notes": [
            "This probe does not connect to validators or provider APIs.",
            "D-Wave, Modal, and Metal live execution require separate credentials/hardware checks.",
        ],
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="Print machine-readable JSON.")
    parser.add_argument("--no-cuda-allocation", action="store_true", help="Skip the tiny cp.zeros(1) allocation.")
    args = parser.parse_args()
    result = collect(allocate_cuda=not args.no_cuda_allocation)
    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True))
    else:
        print(f"Python: {result['python']}")
        print(f"quip-protocol: {result['distribution']['version'] or 'not installed'}")
        print(f"quip-miner CLI: {'ok' if result['cli'].get('available') else 'missing'}")
        for name, info in result["imports"].items():
            print(f"{name}: {'ok' if info['ok'] else 'FAIL ' + str(info['error'])}")
        print(f"CUDA: {result['cuda']}")
    failures = [k for k, v in result["imports"].items() if not v["ok"] and k in {"quip_cli", "shared.miner_config"}]
    return 1 if failures or not result["cli"].get("available") else 0


if __name__ == "__main__":
    raise SystemExit(main())
