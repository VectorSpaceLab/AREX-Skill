#!/usr/bin/env python3
"""Smoke-check a Dagster Definitions object or run a tiny in-memory asset materialization.

This helper is intentionally self-contained: it depends only on Python and the
installed `dagster` package. It imports either a module name or a Python file,
looks for a `dagster.Definitions` object, and performs lightweight resolution
checks. With no target it validates that Dagster can materialize a tiny asset
snippet in memory.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import sys
from pathlib import Path
from types import ModuleType
from typing import Any


def _load_dagster() -> ModuleType:
    try:
        import dagster as dg
    except Exception as exc:  # pragma: no cover - depends on caller environment
        raise SystemExit(f"Could not import dagster: {exc}") from exc
    return dg


def _import_module(module_name: str) -> ModuleType:
    try:
        return importlib.import_module(module_name)
    except Exception as exc:
        raise SystemExit(f"Could not import module {module_name!r}: {exc}") from exc


def _import_file(file_path: Path) -> ModuleType:
    if not file_path.exists():
        raise SystemExit(f"Python file does not exist: {file_path}")
    if file_path.suffix != ".py":
        raise SystemExit(f"Expected a .py file, got: {file_path}")

    module_name = f"_dagster_defs_smoke_{file_path.stem}"
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    if spec is None or spec.loader is None:
        raise SystemExit(f"Could not create import spec for: {file_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    parent = str(file_path.resolve().parent)
    sys.path.insert(0, parent)
    try:
        spec.loader.exec_module(module)
    except Exception as exc:
        raise SystemExit(f"Could not execute Python file {file_path}: {exc}") from exc
    finally:
        if sys.path and sys.path[0] == parent:
            sys.path.pop(0)
    return module


def _find_definitions(module: ModuleType, dg: ModuleType, attr_name: str | None) -> Any:
    definitions_type = dg.Definitions
    if attr_name:
        candidate = getattr(module, attr_name, None)
        if isinstance(candidate, definitions_type):
            return candidate
        raise SystemExit(f"Attribute {attr_name!r} is not a dagster.Definitions object")

    for common_name in ("defs", "definitions"):
        candidate = getattr(module, common_name, None)
        if isinstance(candidate, definitions_type):
            return candidate

    matches = [value for value in vars(module).values() if isinstance(value, definitions_type)]
    if len(matches) == 1:
        return matches[0]
    if len(matches) > 1:
        raise SystemExit(
            "Found multiple dagster.Definitions objects; rerun with --attribute NAME"
        )
    raise SystemExit("No dagster.Definitions object found")


def _describe_defs(defs: Any) -> list[str]:
    lines: list[str] = []
    asset_specs = defs.resolve_all_asset_specs()
    lines.append(f"Resolved {len(asset_specs)} asset spec(s)")
    if asset_specs:
        keys = sorted(str(spec.key) for spec in asset_specs)
        lines.append("Asset keys: " + ", ".join(keys[:20]))
        if len(keys) > 20:
            lines.append(f"...and {len(keys) - 20} more")
    return lines


def _run_tiny_materialization(dg: ModuleType) -> list[str]:
    @dg.asset
    def smoke_upstream() -> int:
        return 1

    @dg.asset
    def smoke_downstream(smoke_upstream: int) -> int:
        return smoke_upstream + 1

    result = dg.materialize_to_memory([smoke_upstream, smoke_downstream])
    if not result.success:
        raise SystemExit("Tiny materialization did not report success")
    value = result.output_for_node("smoke_downstream")
    if value != 2:
        raise SystemExit(f"Unexpected smoke_downstream output: {value!r}")
    return ["Dagster import OK", "Tiny in-memory materialization OK"]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Smoke-check a Dagster Definitions object from a module/file, or run "
            "a tiny in-memory materialization when no target is provided."
        )
    )
    source = parser.add_mutually_exclusive_group()
    source.add_argument("--module", help="Import path of a Python module that defines Definitions")
    source.add_argument("--file", type=Path, help="Path to a Python file that defines Definitions")
    parser.add_argument(
        "--attribute",
        help="Specific attribute name containing a dagster.Definitions object",
    )
    parser.add_argument(
        "--resolve-job",
        help="Optional job name to resolve with Definitions.resolve_job_def",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    dg = _load_dagster()

    if args.module is None and args.file is None:
        for line in _run_tiny_materialization(dg):
            print(line)
        return 0

    module = _import_module(args.module) if args.module else _import_file(args.file)
    defs = _find_definitions(module, dg, args.attribute)

    for line in _describe_defs(defs):
        print(line)

    if args.resolve_job:
        job_def = defs.resolve_job_def(args.resolve_job)
        print(f"Resolved job: {job_def.name}")

    print("Definitions smoke check OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
