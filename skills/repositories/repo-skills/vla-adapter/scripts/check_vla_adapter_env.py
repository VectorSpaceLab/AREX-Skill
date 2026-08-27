#!/usr/bin/env python3
"""Check a VLA-Adapter Python environment without running models or robots.

Example:
  python check_vla_adapter_env.py --check-optional --require-cuda
"""

from __future__ import annotations

import argparse
import importlib
import os
import sys
from importlib import metadata
from typing import Iterable, Mapping, Sequence


BASE_REQUIRED_IMPORTS: Sequence[str] = (
    "prismatic",
    "torch",
    "transformers",
    "timm",
    "tensorflow",
    "tensorflow_datasets",
    "dlimp",
    "json_numpy",
    "fastapi",
    "uvicorn",
)

STACK_IMPORTS: Mapping[str, Sequence[str]] = {
    "libero": (
        "libero",
        "robosuite",
        "bddl",
        "easydict",
        "imageio",
        "imageio_ffmpeg",
        "cloudpickle",
        "gym",
    ),
    "calvin": ("calvin_agent", "calvin_env", "moviepy", "termcolor"),
    "aloha": ("msgpack", "msgpack_numpy"),
}

STACK_ENTRYPOINTS: Mapping[str, Sequence[str]] = {
    "libero": ("experiments/robot/libero/run_libero_eval.py",),
    "calvin": ("vla-scripts/evaluate_calvin.py",),
    "aloha": (
        "experiments/robot/server_deploy/deploy.py",
        "experiments/robot/aloha/run_cobot_client.py",
        "experiments/robot/aloha/run_fake_cobot_client.py",
    ),
}


def probe_import(name: str) -> tuple[bool, str]:
    try:
        mod = importlib.import_module(name)
        version = getattr(mod, "__version__", None)
        if version is None:
            try:
                version = metadata.version(name.replace("_", "-"))
            except metadata.PackageNotFoundError:
                version = "unknown-version"
        return True, str(version)
    except Exception as exc:  # noqa: BLE001 - diagnostic UI
        return False, f"{type(exc).__name__}: {exc}"


def print_probe(label: str, imports: Iterable[str], required: bool) -> int:
    failures = 0
    for name in imports:
        ok, detail = probe_import(name)
        status = "PASS" if ok else ("FAIL" if required else "WARN")
        print(f"{status}: import {name}: {detail}")
        if required and not ok:
            failures += 1
    return failures


def check_entrypoints(repo_root: str, stack: str) -> int:
    failures = 0
    for relative_path in STACK_ENTRYPOINTS.get(stack, ()):
        path = os.path.join(repo_root, relative_path)
        if os.path.isfile(path):
            print(f"PASS: {stack} entrypoint present: {relative_path}")
        else:
            print(f"FAIL: {stack} entrypoint missing: {relative_path}")
            failures += 1
    return failures


def main() -> int:
    parser = argparse.ArgumentParser(description="Check a VLA-Adapter external checkout environment safely.")
    parser.add_argument("--repo-root", required=True, help="Absolute VLA-Adapter source checkout root (not this skill directory).")
    parser.add_argument("--stack", choices=("base", "libero", "calvin", "aloha"), default="base", help="Dependency and entrypoint stack to require (default: base).")
    parser.add_argument("--require-cuda", action="store_true", help="Fail if PyTorch CUDA is unavailable.")
    parser.add_argument("--check-optional", action="store_true", help="Probe legacy optional LIBERO/CALVIN/ROS imports as warnings.")
    args = parser.parse_args()

    if not os.path.isabs(args.repo_root):
        parser.error("--repo-root must be an absolute source checkout path")
    missing = [name for name in ("pyproject.toml", "prismatic", "vla-scripts", "experiments") if not os.path.exists(os.path.join(args.repo_root, name))]
    if missing:
        print(f"FAIL: source checkout root is missing: {', '.join(missing)}")
        return 1

    # Probe the checkout's source package even when this helper is invoked by
    # absolute path from outside the native repository.
    repo_root = os.path.abspath(args.repo_root)
    if repo_root not in sys.path:
        sys.path.insert(0, repo_root)

    failures = check_entrypoints(repo_root, args.stack) if args.stack != "base" else 0
    print(f"Python: {sys.version.split()[0]}")
    try:
        print(f"vla-adapter distribution: {metadata.version('vla-adapter')}")
    except metadata.PackageNotFoundError:
        print("WARN: vla-adapter distribution metadata not found; editable source may not be installed.")

    required = list(BASE_REQUIRED_IMPORTS) + list(STACK_IMPORTS.get(args.stack, ()))
    failures += print_probe("required", required, required=True)

    torch_ok, _ = probe_import("torch")
    if torch_ok:
        import torch

        cuda_ok = bool(torch.cuda.is_available())
        print(f"{'PASS' if cuda_ok else 'WARN'}: torch.cuda.is_available()={cuda_ok}")
        if cuda_ok:
            try:
                x = torch.tensor([1.0], device="cuda")
                print(f"PASS: CUDA tensor allocation on {torch.cuda.get_device_name(0)} value={float(x.cpu()[0])}")
            except Exception as exc:  # noqa: BLE001
                print(f"FAIL: CUDA tensor allocation failed: {type(exc).__name__}: {exc}")
                failures += 1
        elif args.require_cuda:
            failures += 1

    if args.check_optional and args.stack == "base":
        optional = ["libero", "calvin_agent", "rospy", "cv_bridge", "robosuite", "bddl"]
        print_probe("optional", optional, required=False)

    if failures:
        print(f"Result: FAIL ({failures} required check(s) failed)")
        return 1
    print("Result: PASS")
    return 0




if __name__ == "__main__":
    raise SystemExit(main())
