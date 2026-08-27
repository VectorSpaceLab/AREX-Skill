#!/usr/bin/env python3
"""Side-effect-light backend availability probe for quip-miner."""
from __future__ import annotations

import argparse
import json
import platform
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any


def _run(cmd: list[str], timeout: float = 5.0) -> dict[str, Any]:
    try:
        p = subprocess.run(cmd, text=True, capture_output=True, timeout=timeout, check=False)
    except Exception as exc:  # noqa: BLE001
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    return {"ok": p.returncode == 0, "returncode": p.returncode, "stdout": p.stdout.strip(), "stderr": p.stderr.strip()}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true")
    parser.add_argument("--skip-cuda-allocation", action="store_true")
    args = parser.parse_args()
    out: dict[str, Any] = {"platform": platform.platform(), "machine": platform.machine()}
    exe = shutil.which("quip-miner")
    if not exe:
        companion = Path(sys.executable).with_name("quip-miner")
        exe = str(companion) if companion.exists() else None
    out["quip_miner_help"] = _run([exe, "--help"], timeout=15) if exe else {"ok": False, "error": "not on PATH or next to sys.executable"}
    out["nvidia_smi"] = _run(["nvidia-smi", "--query-gpu=index,name,driver_version", "--format=csv,noheader"], timeout=5) if shutil.which("nvidia-smi") else {"ok": False, "error": "nvidia-smi not found"}
    try:
        import cupy as cp  # type: ignore[import-not-found]
        cuda: dict[str, Any] = {"import": True, "cupy_version": cp.__version__}
        cuda["device_count"] = int(cp.cuda.runtime.getDeviceCount())
        if not args.skip_cuda_allocation and cuda["device_count"]:
            cp.zeros(1)
            cuda["tiny_allocation"] = True
    except Exception as exc:  # noqa: BLE001
        cuda = {"import": False, "error": f"{type(exc).__name__}: {exc}"}
    out["cuda"] = cuda
    out["metal_possible"] = platform.system() == "Darwin" and platform.machine().lower() in {"arm64", "aarch64"}
    try:
        from GPU.modal_sampler import GPU_AVAILABLE  # type: ignore[import-not-found]
        out["modal_available"] = bool(GPU_AVAILABLE)
    except Exception as exc:  # noqa: BLE001
        out["modal_available"] = False
        out["modal_error"] = f"{type(exc).__name__}: {exc}"
    try:
        from QPU.qpu_time_manager import parse_duration
        out["qpu_duration_parser"] = parse_duration("30s")
    except Exception as exc:  # noqa: BLE001
        out["qpu_duration_parser_error"] = f"{type(exc).__name__}: {exc}"
    if args.json:
        print(json.dumps(out, indent=2, sort_keys=True))
    else:
        for key, value in out.items():
            print(f"{key}: {value}")
    return 0 if out["quip_miner_help"].get("ok") else 1


if __name__ == "__main__":
    raise SystemExit(main())
