#!/usr/bin/env python3
"""Probe source-build prerequisites without compiling the whole repository."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from pathlib import Path
from typing import Any, Dict


def which(name: str) -> str | None:
    return shutil.which(name)


def main() -> int:
    parser = argparse.ArgumentParser(description="Probe Torch-TensorRT source-build prerequisites.")
    parser.add_argument("--repo-root", type=Path, default=Path.cwd(), help="Torch-TensorRT checkout root")
    parser.add_argument("--json", action="store_true", help="print JSON output")
    args = parser.parse_args()

    root = args.repo_root
    report: Dict[str, Any] = {
        "repo_root": str(root),
        "python": sys.version,
        "platform": sys.platform,
        "env": {k: os.environ.get(k) for k in ["PYTHON_ONLY", "NO_TORCHSCRIPT", "USE_TRT_RTX", "CU_VERSION", "TORCHTRT_TARGET_PLATFORM", "JETPACK_BUILD"]},
        "tools": {name: which(name) for name in ["bazel", "bazelisk", "git", "ninja", "cmake", "python"]},
        "files": {name: (root / name).exists() for name in ["pyproject.toml", "setup.py", "dev_dep_versions.yml", ".bazelversion", "justfile", "tests/ci/suites.py"]},
        "ok": False,
    }
    report["ok"] = bool(report["files"]["pyproject.toml"] and report["files"]["setup.py"] and (report["tools"]["python"] is not None))

    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True, default=str))
    else:
        for key, value in report.items():
            print(f"{key}: {value}")
    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
