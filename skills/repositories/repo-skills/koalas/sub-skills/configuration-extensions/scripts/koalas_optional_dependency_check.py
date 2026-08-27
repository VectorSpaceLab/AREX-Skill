#!/usr/bin/env python
"""Check optional Koalas plotting and MLflow dependencies without installing them."""

from __future__ import print_function

import argparse
import importlib
import sys

try:
    from importlib import metadata as importlib_metadata
except ImportError:  # pragma: no cover - for older Python runtimes
    try:
        import importlib_metadata  # type: ignore
    except ImportError:  # pragma: no cover
        importlib_metadata = None  # type: ignore


MODULES = {
    "plotly": {
        "distribution": "plotly",
        "extra": "koalas[plotly]",
        "purpose": "Koalas default plotting backend. Required when plotting.backend is 'plotly'.",
        "missing": (
            "Plotly is not installed. Koalas plot calls using the 'plotly' backend will fail. "
            "If dependency changes are allowed, install the Plotly optional extra or the plotly "
            "package only; do not install unrelated extras."
        ),
    },
    "matplotlib": {
        "distribution": "matplotlib",
        "extra": "koalas[matplotlib]",
        "purpose": "Alternative Koalas plotting backend. Useful for Matplotlib Axes output and static rendering.",
        "missing": (
            "Matplotlib is not installed. Koalas plot calls using the 'matplotlib' backend will fail. "
            "If dependency changes are allowed, install the Matplotlib optional extra or the matplotlib "
            "package only. In headless environments, configure a non-interactive backend such as Agg."
        ),
    },
    "mlflow": {
        "distribution": "mlflow",
        "extra": "koalas[mlflow]",
        "purpose": "Koalas MLflow pyfunc wrapper exposed through databricks.koalas.mlflow.load_model.",
        "missing": (
            "MLflow is not installed. Importing databricks.koalas.mlflow and using load_model will fail. "
            "If dependency changes are allowed, install the MLflow optional extra or the mlflow package only."
        ),
    },
}


def version_for(distribution):
    if importlib_metadata is None:
        return "unknown (importlib.metadata unavailable)"
    try:
        return importlib_metadata.version(distribution)
    except Exception:
        return "unknown"


def check_module(name):
    meta = MODULES[name]
    print("== {0} ==".format(name))
    print("Purpose: {0}".format(meta["purpose"]))
    try:
        module = importlib.import_module(name)
    except ImportError as exc:
        print("Status: MISSING")
        print("Import error: {0}".format(exc))
        print("Explanation: {0}".format(meta["missing"]))
        print("Narrow install target, if permitted: {0}".format(meta["extra"]))
        return "missing"
    except Exception as exc:
        print("Status: IMPORT ERROR")
        print("Imported package name was found, but importing it raised {0}: {1}".format(type(exc).__name__, exc))
        print("Fix the package/runtime issue for this module before using the related Koalas feature.")
        return "error"

    version = getattr(module, "__version__", None) or version_for(meta["distribution"])
    print("Status: available")
    print("Version: {0}".format(version))
    print("Module: {0}".format(getattr(module, "__name__", name)))
    return "ok"


def parse_args(argv):
    parser = argparse.ArgumentParser(
        description=(
            "Check optional Koalas dependencies for plotting and MLflow without installing anything. "
            "Use --module for one dependency or repeat it; use --all to check every known optional dependency."
        )
    )
    parser.add_argument(
        "--module",
        action="append",
        choices=sorted(MODULES.keys()),
        help="Optional dependency module to check. May be supplied more than once.",
    )
    parser.add_argument(
        "--all",
        action="store_true",
        help="Check plotly, matplotlib, and mlflow.",
    )
    args = parser.parse_args(argv)
    if not args.all and not args.module:
        parser.error("choose --all or at least one --module")
    return args


def main(argv=None):
    args = parse_args(sys.argv[1:] if argv is None else argv)
    if args.all:
        requested = sorted(MODULES.keys())
    else:
        requested = []
        for item in args.module:
            if item not in requested:
                requested.append(item)

    statuses = []
    for index, name in enumerate(requested):
        if index:
            print("")
        statuses.append(check_module(name))

    if any(status == "error" for status in statuses):
        return 2
    if any(status == "missing" for status in statuses):
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
