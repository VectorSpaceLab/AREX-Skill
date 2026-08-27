#!/usr/bin/env python3
"""Check a Python environment for safe nnU-Net v2 setup facts."""

from __future__ import annotations

import argparse
import importlib
import os
import shutil
import subprocess
import sys
from importlib import metadata

CORE_COMMANDS = [
    "nnUNetv2_plan_and_preprocess",
    "nnUNetv2_extract_fingerprint",
    "nnUNetv2_plan_experiment",
    "nnUNetv2_preprocess",
    "nnUNetv2_train",
    "nnUNetv2_predict",
    "nnUNetv2_predict_from_modelfolder",
    "nnUNetv2_find_best_configuration",
    "nnUNetv2_ensemble",
    "nnUNetv2_apply_postprocessing",
    "nnUNetv2_evaluate_folder",
    "nnUNetv2_evaluate_simple",
]


def check_import(module_name: str) -> bool:
    try:
        importlib.import_module(module_name)
    except Exception as error:
        print(f"FAIL import {module_name}: {type(error).__name__}: {error}")
        return False
    print(f"OK import {module_name}")
    return True


def check_version() -> bool:
    try:
        version = metadata.version("nnunetv2")
    except Exception as error:
        print(f"FAIL distribution nnunetv2: {type(error).__name__}: {error}")
        return False
    print(f"OK distribution nnunetv2 {version}")
    return True


def check_commands(commands: list[str]) -> bool:
    ok = True
    for command in commands:
        executable = shutil.which(command)
        if executable is None:
            print(f"FAIL command {command}: not on PATH")
            ok = False
            continue
        result = subprocess.run([executable, "-h"], stdout=subprocess.DEVNULL, stderr=subprocess.PIPE, text=True)
        if result.returncode != 0:
            print(f"FAIL command {command}: -h exited {result.returncode}")
            if result.stderr:
                print(result.stderr.strip().splitlines()[-1])
            ok = False
        else:
            print(f"OK command {command}")
    return ok


def check_env_vars(names: list[str]) -> bool:
    ok = True
    for name in names:
        value = os.environ.get(name)
        if value:
            print(f"OK env {name} is set")
        else:
            print(f"FAIL env {name}: not set")
            ok = False
    return ok


def check_torch() -> bool:
    try:
        import torch
    except Exception as error:
        print(f"FAIL import torch: {type(error).__name__}: {error}")
        return False
    print(f"OK torch {torch.__version__}")
    cuda_version = getattr(torch.version, "cuda", None)
    print(f"torch CUDA runtime: {cuda_version if cuda_version else 'not a CUDA build'}")
    print(f"torch.cuda.is_available: {torch.cuda.is_available()}")
    if torch.cuda.is_available():
        print(f"torch.cuda.device_count: {torch.cuda.device_count()}")
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description="Check nnU-Net v2 imports, commands, env vars, and optional Torch backend.")
    parser.add_argument("--require-commands", action="store_true", help="Require core nnUNetv2_* commands and run -h checks.")
    parser.add_argument("--commands", nargs="*", default=None, help="Specific commands to check instead of the core set.")
    parser.add_argument("--require-env", nargs="*", default=[], help="Environment variables that must be set.")
    parser.add_argument("--check-torch", action="store_true", help="Print PyTorch backend facts.")
    args = parser.parse_args()

    ok = True
    ok &= check_import("nnunetv2")
    ok &= check_import("nnunetv2.paths")
    ok &= check_version()

    commands = args.commands if args.commands is not None else (CORE_COMMANDS if args.require_commands else [])
    if commands:
        ok &= check_commands(commands)
    if args.require_env:
        ok &= check_env_vars(args.require_env)
    if args.check_torch:
        ok &= check_torch()

    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
