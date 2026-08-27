#!/usr/bin/env python3
"""Report the supported Python, package, CUDA, and Isaac Gym environment.

This is an advisory probe by default. It does not install packages, change
files, start a simulator, or require a gamepad. Use --strict for a gate in a
workflow, and --require-isaacgym when the RL/simulation backend is in scope.
"""
from __future__ import print_function

import argparse
import importlib
import importlib.metadata
import subprocess
import sys
from pathlib import Path

EXPECTED = {
    "torch": "1.10.0",
    "numpy": "1.20",
    "scipy": "1.5",
    "hydra": "1.1",
    "omegaconf": "2.1",
    "inputs": "0.5",
    "rsl_rl": None,
    "MPC_Controller": None,
    "RL_Environment": None,
    "mpc_osqp": None,
}
DISTRIBUTIONS = {
    "torch": "torch",
    "numpy": "numpy",
    "scipy": "scipy",
    "hydra": "hydra-core",
    "omegaconf": "omegaconf",
    "inputs": "inputs",
    "rsl_rl": "rsl-rl",
    "MPC_Controller": "rl_mpc_locomotion",
    "RL_Environment": "rl_mpc_locomotion",
    "mpc_osqp": "rl_mpc_locomotion",
}
OPTIONAL = ("osqp", "cvxopt", "mosek", "tensorboard", "torchvision")
SOURCE_ONLY = ("MPC_Controller", "RL_Environment")
MARKERS = ("setup.py", "environment.yml", "MPC_Controller", "RL_Environment")


def find_root(value):
    if value:
        root = Path(value).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("--repo-root is not a directory: %s" % value)
        return root
    for candidate in (Path.cwd(),) + tuple(Path.cwd().parents):
        if all((candidate / marker).exists() for marker in MARKERS):
            return candidate
    return None


def short_error(error):
    text = str(error).splitlines()[0] if str(error) else error.__class__.__name__
    return text[:220]


def version_for(distribution):
    try:
        return importlib.metadata.version(distribution)
    except importlib.metadata.PackageNotFoundError:
        return None


def compatible(actual, expected):
    if expected is None or actual is None:
        return True
    return actual == expected or actual.startswith(expected + ".")


def emit(label, state, detail):
    print("[%s] %-18s %s" % (state, label, detail))


def probe_torch():
    try:
        torch = importlib.import_module("torch")
    except Exception as error:
        emit("torch device", "FAIL", "import failed: %s" % short_error(error))
        return False
    cuda_version = getattr(getattr(torch, "version", None), "cuda", None)
    available = False
    try:
        available = bool(torch.cuda.is_available())
    except Exception as error:
        emit("CUDA", "FAIL", "probe failed: %s" % short_error(error))
        return False
    detail = "torch=%s, CUDA build=%s, available=%s" % (
        getattr(torch, "__version__", "unknown"), cuda_version or "none", available
    )
    if available:
        try:
            names = [torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())]
            detail += ", devices=%s" % "; ".join(names)
        except Exception as error:
            detail += ", device-name probe failed: %s" % short_error(error)
    emit("CUDA", "PASS" if available else "BLOCKED", detail)
    return available


def main():
    parser = argparse.ArgumentParser(
        description="Safely inspect this project's Python packages and CUDA backend."
    )
    parser.add_argument("--repo-root", help="project root; otherwise discover it from the current directory")
    parser.add_argument("--strict", action="store_true", help="return 2 for any failed or blocked probe")
    parser.add_argument("--require-isaacgym", action="store_true", help="treat missing Isaac Gym as a blocking failure")
    parser.add_argument("--pip-check", action="store_true", help="run python -m pip check without changing the environment")
    parser.add_argument("--no-device", action="store_true", help="skip the torch CUDA device probe")
    args = parser.parse_args()

    try:
        root = find_root(args.repo_root)
    except ValueError as error:
        emit("repository root", "FAIL", str(error))
        return 2
    emit("Python", "PASS" if sys.version_info[:2] == (3, 8) else "WARN",
         "%s.%s.%s (project targets 3.8-era Python)" % sys.version_info[:3])
    if root:
        emit("repository root", "PASS", "project markers found")
        # Make source-side probes independent of the caller's current directory.
        sys.path.insert(0, str(root))
        rsl_source = root / "extern" / "rsl_rl"
        if rsl_source.is_dir():
            sys.path.insert(0, str(rsl_source))
    else:
        emit("repository root", "WARN", "not found; package-only checks continue")

    failures = 0
    isaac_missing = False
    for module_name, expected in EXPECTED.items():
        if root is None and module_name in SOURCE_ONLY:
            emit(module_name, "INFO", "current project copy not supplied; pass --repo-root for source-import and layout checks")
            continue
        try:
            module = importlib.import_module(module_name)
            actual = getattr(module, "__version__", None) or version_for(DISTRIBUTIONS[module_name])
            state = "PASS" if compatible(actual, expected) else "WARN"
            detail = "imported"
            if actual:
                detail += "; version=%s" % actual
            if expected and not compatible(actual, expected):
                detail += "; expected %s-era" % expected
            emit(module_name, state, detail)
        except Exception as error:
            if module_name == "isaacgym":
                isaac_missing = True
                continue
            failures += 1
            emit(module_name, "FAIL", "import failed: %s" % short_error(error))

    try:
        isaacgym = importlib.import_module("isaacgym")
        emit("isaacgym", "PASS", "imported; external SDK is available")
    except Exception as error:
        isaac_missing = True
        state = "FAIL" if args.require_isaacgym else "BLOCKED"
        emit("isaacgym", state, "required external backend unavailable: %s" % short_error(error))
        if args.require_isaacgym:
            failures += 1

    for module_name in OPTIONAL:
        try:
            module = importlib.import_module(module_name)
            emit(module_name, "PASS", "optional package imported; version=%s" % (
                getattr(module, "__version__", None) or version_for(module_name) or "unknown"))
        except Exception as error:
            emit(module_name, "INFO", "optional and unavailable: %s" % short_error(error))

    if not args.no_device:
        cuda_ok = probe_torch()
        if args.strict and not cuda_ok:
            failures += 1

    if args.pip_check:
        try:
            result = subprocess.run(
                [sys.executable, "-m", "pip", "check"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                timeout=60,
            )
            output = result.stdout.strip().replace("\n", " | ") or "no broken requirements"
            emit("pip check", "PASS" if result.returncode == 0 else "FAIL", output[:500])
            if result.returncode:
                failures += 1
        except Exception as error:
            failures += 1
            emit("pip check", "FAIL", short_error(error))

    if args.strict and isaac_missing and not args.require_isaacgym:
        failures += 1
    if failures and (args.strict or args.require_isaacgym):
        print("Environment gate: FAILED (%d blocking probe(s)); see remediation in troubleshooting.md." % failures)
        return 2
    if isaac_missing:
        print("Environment gate: PARTIAL; CPU/MPC checks may proceed, RL/simulation remains blocked on Isaac Gym.")
    elif failures:
        print("Environment gate: ADVISORY findings reported; use --strict for a gate.")
    else:
        print("Environment gate: READY for the probes requested.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
