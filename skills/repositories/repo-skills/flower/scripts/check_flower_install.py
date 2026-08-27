#!/usr/bin/env python3
"""Check Flower runtime imports, CLI help/version, and tiny fixture behavior.

Use this from any working directory after installing `flwr` and/or
`flwr-datasets` into the active Python environment.

Examples
--------
python scripts/check_flower_install.py
python scripts/check_flower_install.py --check-cli
python scripts/check_flower_install.py --app-pyproject /path/to/app/pyproject.toml
python scripts/check_flower_install.py --dataset-smoke
"""

from __future__ import annotations

import argparse
import importlib
import inspect
import subprocess
import sys
import tomllib
from pathlib import Path
from shutil import which
from types import ModuleType


DEFAULT_CLI_COMMANDS = ["flwr", "flower-superlink", "flower-supernode", "flwr-datasets"]
DEFAULT_PACKAGES = ["flwr", "flwr_datasets"]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-cli",
        action="store_true",
        help="Run safe --help and --version checks for Flower CLI entry points.",
    )
    parser.add_argument(
        "--app-pyproject",
        action="append",
        default=[],
        metavar="PATH",
        help="Validate a Flower App pyproject.toml and import its declared components. May be repeated.",
    )
    parser.add_argument(
        "--dataset-smoke",
        action="store_true",
        help="Run a tiny in-memory Flower Datasets partitioner smoke.",
    )
    parser.add_argument(
        "--package",
        action="append",
        default=[],
        metavar="DIST",
        help="Additional distribution name to import and report. May be repeated.",
    )
    return parser.parse_args()


def ok(message: str) -> None:
    print(f"[ok] {message}")


def fail(message: str) -> None:
    raise SystemExit(f"[fail] {message}")


def import_and_report(dist_name: str) -> None:
    module_name = dist_name.replace("-", "_")
    module = importlib.import_module(module_name)
    try:
        from importlib.metadata import metadata, version

        dist_version = version(dist_name)
        dist_label = metadata(dist_name)["Name"]
    except Exception:
        dist_version = getattr(module, "__version__", "unknown")
        dist_label = dist_name
    ok(f"imported {module_name} ({dist_label} {dist_version})")
    print(f"    module={module.__name__}")


def run_cli_check(command: str) -> None:
    executable = which(command)
    if executable is None:
        fail(f"missing CLI executable: {command}")

    for flag in ("--help", "--version"):
        completed = subprocess.run(
            [executable, flag],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=20,
            check=False,
        )
        if completed.returncode != 0:
            print(completed.stdout)
            fail(f"{command} {flag} exited with {completed.returncode}")
        first_line = completed.stdout.strip().splitlines()[0] if completed.stdout.strip() else ""
        ok(f"{command} {flag} passed")
        if first_line:
            print(f"    {first_line}")


def import_component(spec: str, base_dir: Path) -> None:
    if ":" in spec:
        module_name, attr_name = spec.split(":", 1)
    else:
        module_name, attr_name = spec, None

    sys.path.insert(0, str(base_dir))
    try:
        module = importlib.import_module(module_name)
        if attr_name:
            getattr(module, attr_name)
        ok(f"imported app component {spec}")
    except Exception as exc:
        fail(f"failed to import app component {spec}: {exc}")
    finally:
        try:
            sys.path.remove(str(base_dir))
        except ValueError:
            pass


def check_app_pyproject(path: Path) -> None:
    if not path.exists():
        fail(f"missing app pyproject: {path}")

    data = tomllib.loads(path.read_text())
    tool = data.get("tool", {})
    flwr = tool.get("flwr", {})
    app = flwr.get("app", {})
    components = app.get("components", {})

    if "publisher" not in app:
        fail(f"{path}: missing [tool.flwr.app].publisher")
    if not isinstance(components, dict):
        fail(f"{path}: [tool.flwr.app].components must be a table")
    for key in ("serverapp", "clientapp"):
        if key not in components:
            fail(f"{path}: missing [tool.flwr.app].components.{key}")

    ok(f"parsed Flower App config {path}")
    base_dir = path.parent
    for key in ("serverapp", "clientapp"):
        import_component(str(components[key]), base_dir)

    if "config" in app:
        ok(f"found run config keys: {', '.join(sorted(app['config'].keys()))}")


def check_dataset_smoke() -> None:
    import numpy as np
    from datasets import Dataset
    from flwr_datasets.partitioner import IidPartitioner

    part = IidPartitioner(num_partitions=2)
    part.dataset = Dataset.from_dict({"x": [0, 1, 2, 3], "label": [0, 1, 0, 1]})
    partition = part.load_partition(0)
    if len(partition) != 2:
        fail(f"unexpected partition size: {len(partition)}")
    # Exercise NumPy importability through the same environment.
    arr = np.array([1.0, 2.0], dtype=np.float32)
    ok(f"Flower Datasets tiny smoke passed (partition size={len(partition)}, dtype={arr.dtype})")


def main() -> None:
    args = parse_args()

    for dist in DEFAULT_PACKAGES + args.package:
        import_and_report(dist)

    if args.check_cli:
        for command in DEFAULT_CLI_COMMANDS:
            run_cli_check(command)

    for pyproject in args.app_pyproject:
        check_app_pyproject(Path(pyproject))

    if args.dataset_smoke:
        check_dataset_smoke()

    if not (args.check_cli or args.app_pyproject or args.dataset_smoke):
        ok("import-only smoke completed; use --check-cli, --app-pyproject, or --dataset-smoke for deeper checks")


if __name__ == "__main__":
    main()
