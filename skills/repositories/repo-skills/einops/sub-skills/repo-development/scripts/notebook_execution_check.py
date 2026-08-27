#!/usr/bin/env python3
"""Dependency checker and optional executor for einops tutorial notebooks.

Default mode is non-mutating and does not execute notebooks. Use --execute for a
single selected notebook after dependencies and time budget are approved.
"""

from __future__ import annotations

import argparse
import importlib.util
import sys
from pathlib import Path

REQUIREMENTS = ["nbformat", "nbconvert", "jupyter", "PIL", "numpy", "tensorflow", "torch"]


def dependency_status() -> dict[str, bool]:
    return {name: importlib.util.find_spec(name) is not None for name in REQUIREMENTS}


def list_notebooks(base: Path) -> list[Path]:
    candidates = []
    for pattern in ["docs/*.ipynb", "*.ipynb"]:
        candidates.extend(base.glob(pattern))
    return sorted(set(candidates))


def execute_notebook(path: Path, timeout: int) -> None:
    try:
        import nbformat  # type: ignore
        from nbconvert.preprocessors import ExecutePreprocessor  # type: ignore
    except ModuleNotFoundError as exc:
        raise SystemExit(f"Missing notebook execution dependency {exc.name!r}.") from exc
    nb = nbformat.read(path, nbformat.NO_CONVERT)
    ep = ExecutePreprocessor(timeout=timeout, kernel_name="python3")
    ep.preprocess(nb, {"metadata": {"path": str(path.parent.resolve())}})


def parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Check or execute einops tutorial notebook prerequisites.")
    p.add_argument("--base", default=".", help="Project base used for notebook discovery (default: current directory).")
    p.add_argument("--notebook", help="Notebook path to plan/execute, e.g. docs/1-einops-basics.ipynb.")
    p.add_argument("--list", action="store_true", help="List dependency status and discovered notebooks.")
    p.add_argument("--execute", action="store_true", help="Execute the selected notebook. Default is dry-run only.")
    p.add_argument("--timeout", type=int, default=120, help="Per-cell execution timeout in seconds.")
    return p


def main(argv: list[str] | None = None) -> int:
    args = parser().parse_args(argv)
    base = Path(args.base)
    status = dependency_status()
    print("Dependency status:")
    for name, ok in status.items():
        print(f"  {name}: {'ok' if ok else 'missing'}")

    notebooks = list_notebooks(base)
    if args.list or not args.notebook:
        print("Discovered notebooks:")
        for nb in notebooks:
            print(f"  {nb}")

    if not args.notebook:
        if not args.execute:
            print("Dry-run only. Pass --notebook and --execute to run one notebook.")
            return 0
        raise SystemExit("--execute requires --notebook to avoid running all notebooks accidentally.")

    notebook = Path(args.notebook)
    if not notebook.exists():
        raise SystemExit(f"Notebook not found: {notebook}")
    print(f"Selected notebook: {notebook}")
    print(f"Timeout: {args.timeout}s per cell")
    if not args.execute:
        print("Dry-run only. Add --execute to execute the selected notebook.")
        return 0
    missing = [name for name, ok in status.items() if not ok]
    if missing:
        raise SystemExit(f"Missing dependencies for notebook execution: {missing}")
    execute_notebook(notebook, args.timeout)
    print(f"Executed notebook successfully: {notebook}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
