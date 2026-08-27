#!/usr/bin/env python3
"""Probe a TVM installation or source checkout.

This script is a safe diagnostic helper for the generated Apache TVM repo skill.
It prints import, version, library, and backend facts without starting services
or running native examples. Use `--repo-root` when probing a source checkout and
`--tvm-library-path` when the built shared libraries live outside the default
runtime search path.
"""

from __future__ import annotations

import argparse
import json
import os
import sys
from importlib import metadata
from pathlib import Path


def _add_repo_paths(repo_root: Path) -> None:
    python_dir = repo_root / "python"
    local_python = repo_root / ".local" / "python"
    for path in (python_dir, local_python):
        if path.exists():
            sys.path.insert(0, str(path))


def _load_tvm():
    try:
        import tvm  # type: ignore
    except Exception as exc:  # pragma: no cover - diagnostic path
        print(f"IMPORT_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return None
    return tvm


def _safe_version(dist_name: str) -> str | None:
    try:
        return metadata.version(dist_name)
    except metadata.PackageNotFoundError:
        return None


def _enabled(tvm, kind: str) -> bool:
    try:
        return bool(tvm.runtime.enabled(kind))
    except Exception:
        return False


def _device_exists(tvm, name: str) -> bool | None:
    try:
        dev = getattr(tvm, name)()
        return bool(getattr(dev, "exist", False))
    except Exception:
        return None


def _backend_snapshot(tvm) -> dict[str, object]:
    snapshot: dict[str, object] = {
        "llvm_enabled": _enabled(tvm, "llvm"),
        "cuda_enabled": _enabled(tvm, "cuda"),
        "rocm_enabled": _enabled(tvm, "rocm"),
        "opencl_enabled": _enabled(tvm, "opencl"),
        "vulkan_enabled": _enabled(tvm, "vulkan"),
        "metal_enabled": _enabled(tvm, "metal"),
        "cuda_device_exists": _device_exists(tvm, "cuda"),
        "rocm_device_exists": _device_exists(tvm, "rocm"),
        "opencl_device_exists": _device_exists(tvm, "opencl"),
        "vulkan_device_exists": _device_exists(tvm, "vulkan"),
        "metal_device_exists": _device_exists(tvm, "metal"),
    }
    try:
        snapshot["libinfo"] = tvm.support.libinfo()
    except Exception as exc:  # pragma: no cover - diagnostic path
        snapshot["libinfo_error"] = f"{type(exc).__name__}: {exc}"
    try:
        snapshot["loaded_libs"] = {
            key: str(value) for key, value in getattr(tvm.base, "_LOADED_LIBS", {}).items()
        }
    except Exception as exc:  # pragma: no cover - diagnostic path
        snapshot["loaded_libs_error"] = f"{type(exc).__name__}: {exc}"
    return snapshot


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Probe TVM import and backend readiness")
    parser.add_argument("--repo-root", type=Path, help="Optional Apache TVM checkout root")
    parser.add_argument(
        "--tvm-library-path",
        type=Path,
        help="Optional directory containing libtvm/libtvm_runtime artifacts",
    )
    parser.add_argument(
        "--expect-backend",
        action="append",
        default=[],
        help="Backend name to report/check, e.g. llvm, cuda, opencl, vulkan, metal, rocm",
    )
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    args = parser.parse_args(argv)

    if args.repo_root is not None:
        _add_repo_paths(args.repo_root.resolve())
    if args.tvm_library_path is not None:
        os.environ["TVM_LIBRARY_PATH"] = str(args.tvm_library_path.resolve())

    tvm = _load_tvm()
    if tvm is None:
        return 1

    payload: dict[str, object] = {
        "python": {
            "executable": sys.executable,
            "version": sys.version,
            "prefix": sys.prefix,
        },
        "distributions": {
            "apache-tvm": _safe_version("apache-tvm"),
            "apache-tvm-ffi": _safe_version("apache-tvm-ffi"),
        },
        "imports": {
            "tvm_file": getattr(tvm, "__file__", None),
            "tvm_version": getattr(tvm, "__version__", None),
        },
        "backends": _backend_snapshot(tvm),
    }

    if args.expect_backend:
        checks: dict[str, object] = {}
        for backend in args.expect_backend:
            backend = backend.lower()
            if backend == "llvm":
                checks[backend] = payload["backends"]["llvm_enabled"]
            elif backend == "cuda":
                checks[backend] = {
                    "enabled": payload["backends"]["cuda_enabled"],
                    "device_exists": payload["backends"]["cuda_device_exists"],
                }
            elif backend == "rocm":
                checks[backend] = {
                    "enabled": payload["backends"]["rocm_enabled"],
                    "device_exists": payload["backends"]["rocm_device_exists"],
                }
            elif backend == "vulkan":
                checks[backend] = {
                    "enabled": payload["backends"]["vulkan_enabled"],
                    "device_exists": payload["backends"]["vulkan_device_exists"],
                }
            elif backend == "metal":
                checks[backend] = {
                    "enabled": payload["backends"]["metal_enabled"],
                    "device_exists": payload["backends"]["metal_device_exists"],
                }
            elif backend == "opencl":
                checks[backend] = {
                    "enabled": payload["backends"]["opencl_enabled"],
                    "device_exists": payload["backends"]["opencl_device_exists"],
                }
            else:
                checks[backend] = "unknown-backend-name"
        payload["expected_backends"] = checks

    if args.json:
        print(json.dumps(payload, indent=2, sort_keys=True, default=str))
    else:
        print(f"python: {payload['python']['version'].splitlines()[0]}")
        print(f"python_executable: {payload['python']['executable']}")
        print(f"tvm_file: {payload['imports']['tvm_file']}")
        print(f"tvm_version: {payload['imports']['tvm_version']}")
        print(f"apache-tvm metadata: {payload['distributions']['apache-tvm']}")
        print(f"apache-tvm-ffi metadata: {payload['distributions']['apache-tvm-ffi']}")
        backends = payload["backends"]
        for key in [
            "llvm_enabled",
            "cuda_enabled",
            "rocm_enabled",
            "opencl_enabled",
            "vulkan_enabled",
            "metal_enabled",
            "cuda_device_exists",
            "rocm_device_exists",
            "opencl_device_exists",
            "vulkan_device_exists",
            "metal_device_exists",
        ]:
            print(f"{key}: {backends.get(key)}")
        libinfo = backends.get("libinfo")
        if isinstance(libinfo, dict):
            for key in ["GIT_COMMIT_HASH", "USE_LLVM", "LLVM_VERSION", "USE_CUDA", "USE_RPC"]:
                print(f"libinfo.{key}: {libinfo.get(key)}")
        if args.expect_backend:
            print("expected_backends:")
            for key, value in payload["expected_backends"].items():
                print(f"  {key}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
