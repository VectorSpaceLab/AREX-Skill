#!/usr/bin/env python3
"""Plan or run the DINO MultiScaleDeformableAttention build.

This wrapper keeps the source extension build explicit and reviewable. It does
not install compilers/packages or delete build outputs. Use --launch only after
checking the active CUDA/PyTorch/compiler combination.
"""
from __future__ import annotations

import argparse
import os
import shlex
import subprocess
import sys
from pathlib import Path


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Plan or launch the DINO CUDA operator build and optional test.")
    p.add_argument("--project-root", type=Path, required=True, help="DINO project root")
    p.add_argument("--cuda-home", help="CUDA toolkit root; exported only for the child build")
    p.add_argument("--cc", help="host C compiler executable")
    p.add_argument("--cxx", help="host C++ compiler executable")
    p.add_argument("--arch", default=None, help="TORCH_CUDA_ARCH_LIST value, for example 8.0")
    p.add_argument("--cccl-include", help="optional CCCL include directory")
    p.add_argument("--run-test", action="store_true", help="run the operator test after a successful build")
    p.add_argument("--launch", action="store_true", help="perform the build; otherwise print the command")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    root = args.project_root.expanduser().resolve()
    setup = root / "models" / "dino" / "ops" / "setup.py"
    test = root / "models" / "dino" / "ops" / "test.py"
    if not setup.is_file() or not test.is_file():
        parser().error("--project-root must contain models/dino/ops/setup.py and test.py")
    command = [sys.executable, str(setup), "build", "install"]
    env = os.environ.copy()
    if args.cuda_home:
        env["CUDA_HOME"] = str(Path(args.cuda_home).expanduser().resolve())
    if args.cc:
        env["CC"] = args.cc
    if args.cxx:
        env["CXX"] = args.cxx
        env["CUDAHOSTCXX"] = args.cxx
    if args.arch:
        env["TORCH_CUDA_ARCH_LIST"] = args.arch
    if args.cccl_include:
        include = str(Path(args.cccl_include).expanduser().resolve())
        env["CPATH"] = include + (os.pathsep + env["CPATH"] if env.get("CPATH") else "")
        env["CPLUS_INCLUDE_PATH"] = include + (os.pathsep + env["CPLUS_INCLUDE_PATH"] if env.get("CPLUS_INCLUDE_PATH") else "")
    print("BUILD (not launched unless --launch):")
    print(" ".join(shlex.quote(item) for item in command))
    print("working directory:", root / "models" / "dino" / "ops")
    if not args.launch:
        return 0
    result = subprocess.run(command, cwd=root / "models" / "dino" / "ops", env=env, check=False)
    if result.returncode != 0 or not args.run_test:
        return result.returncode
    return subprocess.run([sys.executable, str(test)], cwd=root / "models" / "dino" / "ops", env=env, check=False).returncode


if __name__ == "__main__":
    raise SystemExit(main())
