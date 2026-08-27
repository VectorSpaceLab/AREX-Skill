#!/usr/bin/env python3
"""Import Fugue backend packages and print their registration state."""
import argparse
import inspect
from importlib import import_module
from importlib.metadata import entry_points
from typing import Dict, Sequence

BACKENDS: Dict[str, str] = {
    "duckdb": "fugue_duckdb",
    "dask": "fugue_dask",
    "spark": "fugue_spark",
    "ray": "fugue_ray",
    "ibis": "fugue_ibis",
    "polars": "fugue_polars",
    "notebook": "fugue_notebook",
    "viz": "fugue_contrib.viz",
    "seaborn": "fugue_contrib.seaborn",
}

CLASS_NAMES: Dict[str, Sequence[str]] = {
    "fugue_duckdb": ("DuckExecutionEngine", "DuckDBEngine"),
    "fugue_dask": ("DaskExecutionEngine", "DaskDataFrame"),
    "fugue_spark": ("SparkExecutionEngine", "SparkDataFrame"),
    "fugue_ray": ("RayExecutionEngine", "RayDataFrame"),
    "fugue_ibis": ("IbisExecutionEngine", "IbisDataFrame"),
    "fugue_polars": ("PolarsDataFrame",),
    "fugue_notebook": ("NotebookSetup", "setup"),
}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--require",
        nargs="*",
        default=[],
        help="Backend names that must import successfully (default: check all known backends and report status).",
    )
    return parser


def _print_entry_points() -> None:
    try:
        names = sorted(ep.name for ep in entry_points(group="fugue.plugins"))
    except Exception as exc:  # pragma: no cover
        print(f"entry_points:error:{exc}")
        return
    print(f"fugue.plugins: {', '.join(names) if names else '<none>'}")


def _print_classes(module_name: str) -> None:
    module = import_module(module_name)
    for cls_name in CLASS_NAMES.get(module_name, ()):
        obj = getattr(module, cls_name, None)
        if obj is None:
            print(f"{module_name}.{cls_name}: missing")
            continue
        try:
            sig = inspect.signature(obj)
        except Exception as exc:  # pragma: no cover
            sig = f"error:{exc}"
        print(f"{module_name}.{cls_name}: {sig}")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    required = set(args.require)
    failures = []

    _print_entry_points()

    for backend_name, module_name in BACKENDS.items():
        try:
            import_module(module_name)
            status = "ok"
        except Exception as exc:
            status = f"error:{exc}"
            if backend_name in required:
                failures.append((backend_name, str(exc)))
        print(f"import:{backend_name}:{status}")
        if status == "ok":
            _print_classes(module_name)

    if failures:
        print("required backend failures:")
        for backend_name, message in failures:
            print(f"- {backend_name}: {message}")
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
