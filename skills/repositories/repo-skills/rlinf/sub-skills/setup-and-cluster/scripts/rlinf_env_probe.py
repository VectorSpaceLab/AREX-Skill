#!/usr/bin/env python3
"""Safe RLinf environment probe.

The probe is read-only: it imports packages, checks versions, inspects selected
environment variables, queries Torch CUDA state, and optionally runs `ray status`
with a timeout. It does not start Ray, install packages, or mutate files.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.metadata as metadata
import json
import os
import platform
import shutil
import subprocess
import sys
import time
from pathlib import Path
from typing import Any


IMPORT_TARGETS = [
    ("rlinf", "rlinf"),
    ("ray", "ray"),
    ("torch", "torch"),
    ("hydra", "hydra-core"),
    ("omegaconf", "omegaconf"),
    ("sglang", "sglang"),
    ("vllm", "vllm"),
    ("megatron.bridge", "rlinf-megatron-bridge"),
    ("transformer_engine", "transformer-engine"),
    ("flash_attn", "flash-attn"),
]

ENV_KEYS = [
    "RLINF_NODE_RANK",
    "RLINF_COMM_NET_DEVICES",
    "RLINF_CODE_WORKING_DIR",
    "RLINF_LOG_LEVEL",
    "RLINF_PATH_ENV_MERGE_MODE",
    "RAY_ADDRESS",
    "CUDA_VISIBLE_DEVICES",
    "NVIDIA_VISIBLE_DEVICES",
    "HIP_VISIBLE_DEVICES",
    "ASCEND_VISIBLE_DEVICES",
    "MUSA_VISIBLE_DEVICES",
    "MASTER_ADDR",
    "MASTER_PORT",
]


def _add_repo_root(repo_root: str | None) -> str | None:
    if not repo_root:
        return None
    path = Path(repo_root).expanduser().resolve()
    if not path.exists():
        raise SystemExit(f"--repo-root does not exist: {path}")
    sys.path.insert(0, str(path))
    return str(path)


def _dist_version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None
    except Exception as exc:  # pragma: no cover - defensive metadata edge case
        return f"error: {exc}"


def _probe_import(module_name: str, dist_name: str) -> dict[str, Any]:
    start = time.perf_counter()
    result: dict[str, Any] = {
        "module": module_name,
        "distribution": dist_name,
        "version": _dist_version(dist_name),
        "importable": False,
        "import_ms": None,
        "file": None,
        "error": None,
    }
    try:
        module = importlib.import_module(module_name)
        result["importable"] = True
        result["file"] = getattr(module, "__file__", None)
    except Exception as exc:  # intentionally broad for diagnostic probes
        result["error"] = f"{type(exc).__name__}: {exc}"
    finally:
        result["import_ms"] = round((time.perf_counter() - start) * 1000, 3)
    return result


def _run_command(cmd: list[str], timeout: float) -> dict[str, Any]:
    result: dict[str, Any] = {
        "command": cmd,
        "available": shutil.which(cmd[0]) is not None,
        "returncode": None,
        "stdout": "",
        "stderr": "",
        "timed_out": False,
    }
    if not result["available"]:
        return result
    try:
        completed = subprocess.run(
            cmd,
            check=False,
            capture_output=True,
            text=True,
            timeout=timeout,
        )
        result.update(
            {
                "returncode": completed.returncode,
                "stdout": completed.stdout.strip(),
                "stderr": completed.stderr.strip(),
            }
        )
    except subprocess.TimeoutExpired as exc:
        result.update(
            {
                "timed_out": True,
                "stdout": (exc.stdout or "").strip() if isinstance(exc.stdout, str) else "",
                "stderr": (exc.stderr or "").strip() if isinstance(exc.stderr, str) else "",
            }
        )
    except Exception as exc:  # pragma: no cover - command execution edge case
        result["stderr"] = f"{type(exc).__name__}: {exc}"
    return result


def _probe_torch() -> dict[str, Any]:
    result: dict[str, Any] = {"importable": False, "error": None}
    try:
        import torch  # type: ignore

        result.update(
            {
                "importable": True,
                "version": getattr(torch, "__version__", None),
                "cuda_version": getattr(torch.version, "cuda", None),
                "hip_version": getattr(torch.version, "hip", None),
                "cuda_available": bool(torch.cuda.is_available()),
                "cuda_device_count": int(torch.cuda.device_count()),
                "mps_available": bool(
                    getattr(getattr(torch.backends, "mps", None), "is_available", lambda: False)()
                ),
            }
        )
        devices = []
        if result["cuda_available"]:
            for idx in range(result["cuda_device_count"]):
                try:
                    devices.append(
                        {
                            "index": idx,
                            "name": torch.cuda.get_device_name(idx),
                            "capability": list(torch.cuda.get_device_capability(idx)),
                            "total_memory_bytes": torch.cuda.get_device_properties(idx).total_memory,
                        }
                    )
                except Exception as exc:  # pragma: no cover - driver edge case
                    devices.append({"index": idx, "error": f"{type(exc).__name__}: {exc}"})
        result["cuda_devices"] = devices
    except Exception as exc:
        result["error"] = f"{type(exc).__name__}: {exc}"
    return result


def build_probe(args: argparse.Namespace) -> dict[str, Any]:
    added_repo_root = _add_repo_root(args.repo_root)
    imports = {
        module_name: _probe_import(module_name, dist_name)
        for module_name, dist_name in IMPORT_TARGETS
    }
    ray_version_cmd = _run_command(["ray", "--version"], args.timeout)
    ray_status_cmd = None
    if args.ray_status:
        ray_status_cmd = _run_command(["ray", "status"], args.timeout)

    return {
        "python": {
            "executable": sys.executable,
            "version": sys.version.split()[0],
            "platform": platform.platform(),
            "cwd": os.getcwd(),
            "sys_path_prefix": sys.path[:5],
            "repo_root_prepended": added_repo_root,
        },
        "environment": {key: os.environ.get(key) for key in ENV_KEYS},
        "imports": imports,
        "torch": _probe_torch(),
        "ray_cli": {
            "ray_version": ray_version_cmd,
            "ray_status": ray_status_cmd,
        },
    }


def _format_command_result(result: dict[str, Any] | None) -> list[str]:
    if result is None:
        return ["not requested"]
    if not result.get("available"):
        return ["command not found"]
    lines = [f"returncode={result.get('returncode')} timed_out={result.get('timed_out')}"]
    stdout = result.get("stdout") or ""
    stderr = result.get("stderr") or ""
    if stdout:
        lines.append("stdout: " + stdout.splitlines()[0][:240])
    if stderr:
        lines.append("stderr: " + stderr.splitlines()[0][:240])
    return lines


def print_text_report(data: dict[str, Any]) -> None:
    print("RLinf environment probe")
    print("=" * 24)
    py = data["python"]
    print(f"Python: {py['version']} ({py['executable']})")
    print(f"Platform: {py['platform']}")
    if py.get("repo_root_prepended"):
        print(f"Prepended repo root for this process: {py['repo_root_prepended']}")

    print("\nEnvironment variables:")
    for key, value in data["environment"].items():
        print(f"  {key}={value if value is not None else '<unset>'}")

    print("\nPackage imports:")
    for name, result in data["imports"].items():
        status = "ok" if result["importable"] else "missing/error"
        version = result.get("version") or "unknown"
        print(f"  {name:<22} {status:<13} version={version}")
        if result.get("error"):
            print(f"    error: {result['error']}")

    torch = data["torch"]
    print("\nTorch/CUDA:")
    if not torch.get("importable"):
        print(f"  torch import failed: {torch.get('error')}")
    else:
        print(f"  torch={torch.get('version')} cuda_runtime={torch.get('cuda_version')} hip={torch.get('hip_version')}")
        print(f"  cuda_available={torch.get('cuda_available')} cuda_device_count={torch.get('cuda_device_count')} mps_available={torch.get('mps_available')}")
        for device in torch.get("cuda_devices", []):
            if "error" in device:
                print(f"  cuda:{device['index']} error={device['error']}")
            else:
                mem_gib = device["total_memory_bytes"] / (1024 ** 3)
                print(f"  cuda:{device['index']} {device['name']} cc={device['capability']} mem={mem_gib:.1f}GiB")

    print("\nRay CLI:")
    for line in _format_command_result(data["ray_cli"]["ray_version"]):
        print(f"  ray --version: {line}")
    for line in _format_command_result(data["ray_cli"].get("ray_status")):
        print(f"  ray status: {line}")


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Safely probe RLinf/Ray/Torch/CUDA readiness without starting services or installing packages."
    )
    parser.add_argument(
        "--repo-root",
        help="Optional RLinf source/package root to prepend to sys.path for this probe only.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit machine-readable JSON instead of a text report.",
    )
    parser.add_argument(
        "--ray-status",
        action="store_true",
        help="Also run `ray status` with the configured timeout. This is read-only but may fail if Ray is not running.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        help="Timeout in seconds for each Ray CLI command (default: 5).",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    data = build_probe(args)
    if args.json:
        print(json.dumps(data, indent=2, sort_keys=True))
    else:
        print_text_report(data)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
