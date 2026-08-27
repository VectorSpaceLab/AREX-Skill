#!/usr/bin/env python3
"""Read-only ExecuTorch setup/build diagnostic.

Examples:
  python scripts/check_executorch_env.py
  python scripts/check_executorch_env.py --repo-root /path/to/executorch
"""
from __future__ import annotations
import argparse
import json
import os
from pathlib import Path
import platform
import shutil
import subprocess
import sys


def run(cmd: list[str]) -> dict:
    try:
        cp = subprocess.run(cmd, text=True, capture_output=True, timeout=10)
        return {"cmd": cmd, "returncode": cp.returncode, "stdout": cp.stdout.strip(), "stderr": cp.stderr.strip()}
    except Exception as exc:
        return {"cmd": cmd, "error": f"{type(exc).__name__}: {exc}"}


def repo_checks(root: Path) -> dict:
    files = ["pyproject.toml", "setup.py", "CMakeLists.txt", "CMakePresets.json", "install_executorch.sh", "Makefile"]
    sentinels = {
        "flatbuffers": "third-party/flatbuffers/CMakeLists.txt",
        "xnnpack": "backends/xnnpack/third-party/XNNPACK/CMakeLists.txt",
        "vulkan_headers": "backends/vulkan/third-party/Vulkan-Headers/include/vulkan/vulkan.h",
    }
    return {
        "root": str(root),
        "exists": root.exists(),
        "files": {name: (root / name).exists() for name in files},
        "submodule_sentinels": {name: (root / rel).exists() for name, rel in sentinels.items()},
    }


def main() -> int:
    ap = argparse.ArgumentParser(description="Check Python, tools, imports, and optional ExecuTorch source checkout files.")
    ap.add_argument("--repo-root", type=Path, help="Optional ExecuTorch source checkout to inspect read-only.")
    args = ap.parse_args()
    report = {
        "python": {"executable": sys.executable, "version": sys.version, "platform": platform.platform()},
        "tools": {name: shutil.which(name) for name in ["git", "cmake", "ninja", "make", "conda", "uv"]},
        "tool_versions": {"cmake": run(["cmake", "--version"]) if shutil.which("cmake") else None},
        "env_flags": {k: os.environ.get(k) for k in ["CMAKE_ARGS", "CMAKE_PREFIX_PATH", "QNN_SDK_ROOT", "ANDROID_NDK", "ANDROID_NDK_ROOT"] if os.environ.get(k)},
        "repo": repo_checks(args.repo_root.resolve()) if args.repo_root else None,
    }
    print(json.dumps(report, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

