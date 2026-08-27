#!/usr/bin/env python3
"""Check the editable package, native source layout, and mpc_osqp bindings.

No build is attempted unless --build is explicitly supplied. The build mode
only invokes the public editable-install command and never removes files or
runs system package-manager commands.
"""
from __future__ import print_function

import argparse
import importlib
import importlib.metadata
import subprocess
import sys
from pathlib import Path

EXPECTED_SUBMODULES = {
    "extern/rsl_rl": "2ad79cf0caa85b91721abfe358105f869a784121",
    "extern/pybind11": "ffa346860b306c9bbfb341aed9c14c067751feb8",
    "extern/eigen3": "02f420012a169ed9267a8a78083aaa588e713353",
    "extern/qpoases": "268b2f2659604df27c82aa6e32aeddb8c1d5cc7f",
}
REQUIRED_LAYOUT = (
    "setup.py",
    "MPC_Controller/convex_MPC/mpc_osqp.cc",
    "extern/osqp/include",
    "extern/osqp/src",
    "extern/qpoases/include",
    "extern/pybind11/include",
    "extern/eigen3/Eigen",
)
SYMBOLS = ("ConvexMpc", "OSQP", "QPOASES", "QPSolverName", "TEST")


def emit(label, state, detail):
    print("[%s] %-20s %s" % (state, label, detail))


def find_root(value):
    if value:
        root = Path(value).expanduser().resolve()
        if not root.is_dir():
            raise ValueError("--repo-root is not a directory: %s" % value)
        return root
    for candidate in (Path.cwd(),) + tuple(Path.cwd().parents):
        if (candidate / "setup.py").is_file() and (candidate / "MPC_Controller").is_dir():
            return candidate
    return None


def short_error(error):
    text = str(error).splitlines()[0] if str(error) else error.__class__.__name__
    return text[:220]


def check_layout(root):
    failures = 0
    if root is None:
        emit("source layout", "INFO", "current project copy not supplied; pass --repo-root for optional layout integrity checks")
        return failures
    for relative in REQUIRED_LAYOUT:
        path = root / relative
        if path.exists():
            emit(relative, "PASS", "present")
        else:
            failures += 1
            emit(relative, "FAIL", "missing; initialize the declared submodules or restore source files")
    return failures


def check_submodules(root):
    failures = 0
    if root is None:
        emit("submodule commits", "INFO", "skipped; pass --repo-root /path/to/current/project-copy to verify recorded revisions")
        return failures
    for relative, expected in EXPECTED_SUBMODULES.items():
        path = root / relative
        try:
            result = subprocess.run(
                ["git", "-C", str(path), "rev-parse", "HEAD"],
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                universal_newlines=True,
                timeout=10,
            )
            actual = result.stdout.strip()
            if result.returncode != 0:
                raise RuntimeError(result.stderr.strip() or "git rev-parse failed")
            if actual == expected:
                emit(relative, "PASS", "expected commit %s" % expected[:12])
            else:
                failures += 1
                emit(relative, "FAIL", "commit %s; expected %s" % (actual[:12], expected[:12]))
        except Exception as error:
            failures += 1
            emit(relative, "FAIL", "cannot verify commit: %s" % short_error(error))
    return failures


def check_import(root):
    if root is not None:
        # Probe a checkout directly when called from an arbitrary directory.
        sys.path.insert(0, str(root))
    try:
        module = importlib.import_module("mpc_osqp")
    except Exception as error:
        emit("mpc_osqp import", "FAIL", short_error(error))
        return 1
    emit("mpc_osqp import", "PASS", "loaded from installed/editable package")
    failures = 0
    for symbol in SYMBOLS:
        if hasattr(module, symbol):
            emit("mpc_osqp.%s" % symbol, "PASS", "binding is exposed")
        else:
            failures += 1
            emit("mpc_osqp.%s" % symbol, "FAIL", "binding is missing from the extension")
    return failures


def build(root):
    if root is None:
        emit("editable build", "FAIL", "--build requires a discovered project root")
        return 1
    emit("editable build", "INFO", "running python -m pip install -e .")
    try:
        result = subprocess.run(
            [sys.executable, "-m", "pip", "install", "-e", "."],
            cwd=str(root),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            universal_newlines=True,
            timeout=900,
        )
    except Exception as error:
        emit("editable build", "FAIL", short_error(error))
        return 1
    if result.returncode:
        lines = [line.strip() for line in result.stdout.splitlines() if line.strip()]
        emit("editable build", "FAIL", (lines[-1] if lines else "pip returned a failure")[:500])
        return 1
    emit("editable build", "PASS", "pip completed; rerun without --build to inspect the import")
    return 0


def main():
    parser = argparse.ArgumentParser(description="Check the mpc_osqp extension and its public build prerequisites.")
    parser.add_argument("--repo-root", help="project root; otherwise discover it from the current directory")
    parser.add_argument("--build", action="store_true", help="explicitly run the editable install before checking")
    parser.add_argument("--check-submodules", action="store_true", help="verify the recorded submodule commits")
    parser.add_argument("--strict", action="store_true", help="return 2 if any layout, commit, build, or import check fails")
    args = parser.parse_args()
    try:
        root = find_root(args.repo_root)
    except ValueError as error:
        emit("repository root", "FAIL", str(error))
        return 2

    failures = 0
    failures += build(root) if args.build else 0
    failures += check_layout(root)
    if args.check_submodules:
        failures += check_submodules(root)
    failures += check_import(root)

    try:
        version = importlib.metadata.version("rl_mpc_locomotion")
        emit("distribution", "PASS", "rl_mpc_locomotion %s" % version)
    except importlib.metadata.PackageNotFoundError:
        failures += 1
        emit("distribution", "FAIL", "editable package metadata is not installed")

    if failures and args.strict:
        print("MPC extension gate: FAILED (%d issue(s))." % failures)
        return 2
    if failures:
        print("MPC extension gate: ADVISORY failures reported; see installation.md and troubleshooting.md.")
        return 0
    print("MPC extension gate: PASSED.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
