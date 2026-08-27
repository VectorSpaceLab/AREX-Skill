#!/usr/bin/env python3
"""Check an Apache TVM installation or source-build import path."""
from __future__ import annotations

import argparse
import json
import os
import sys
from importlib import metadata
from pathlib import Path


def _version(name: str):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--repo-root", type=Path, help="TVM checkout to inspect")
    p.add_argument("--tvm-library-path", type=Path, help="Directory containing built TVM libraries")
    p.add_argument("--expect-backend", action="append", default=[], help="Backend such as llvm or cuda")
    p.add_argument("--json", action="store_true", help="Emit JSON")
    args = p.parse_args(argv)

    if args.repo_root:
        for candidate in (args.repo_root / "python", args.repo_root / ".local" / "python"):
            if candidate.is_dir():
                sys.path.insert(0, str(candidate.resolve()))
    if args.tvm_library_path:
        os.environ["TVM_LIBRARY_PATH"] = str(args.tvm_library_path.resolve())

    try:
        import tvm
    except Exception as exc:
        print(f"TVM_IMPORT_ERROR: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    result = {
        "python": sys.executable,
        "tvm_file": str(getattr(tvm, "__file__", "")),
        "tvm_version": getattr(tvm, "__version__", None),
        "apache_tvm_distribution": _version("apache-tvm"),
        "apache_tvm_ffi_distribution": _version("apache-tvm-ffi"),
        "backends": {},
    }
    for name in ("llvm", "cuda", "rocm", "opencl", "vulkan", "metal"):
        try:
            enabled = bool(tvm.runtime.enabled(name))
        except Exception:
            enabled = False
        device_exists = None
        try:
            device_exists = bool(getattr(tvm, name)().exist)
        except Exception:
            pass
        result["backends"][name] = {"enabled": enabled, "device_exists": device_exists}
    try:
        result["libinfo"] = tvm.support.libinfo()
    except Exception as exc:
        result["libinfo_error"] = f"{type(exc).__name__}: {exc}"
    try:
        result["loaded_libs"] = {k: str(v) for k, v in tvm.base._LOADED_LIBS.items()}
    except Exception as exc:
        result["loaded_libs_error"] = f"{type(exc).__name__}: {exc}"

    result["expected"] = {}
    for name in args.expect_backend:
        key = name.lower()
        result["expected"][key] = result["backends"].get(key, "unknown-backend")

    if args.json:
        print(json.dumps(result, indent=2, sort_keys=True, default=str))
    else:
        for key in ("python", "tvm_file", "tvm_version", "apache_tvm_distribution", "apache_tvm_ffi_distribution"):
            print(f"{key}: {result[key]}")
        for name, facts in result["backends"].items():
            print(f"{name}: enabled={facts['enabled']} device_exists={facts['device_exists']}")
        if "libinfo" in result:
            for key in ("GIT_COMMIT_HASH", "USE_LLVM", "LLVM_VERSION", "USE_CUDA", "USE_RPC"):
                print(f"libinfo.{key}: {result['libinfo'].get(key)}")
        if args.expect_backend:
            print("expected:")
            for name, value in result["expected"].items():
                print(f"  {name}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
