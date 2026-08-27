#!/usr/bin/env python3
"""Inspect a Fugue installation and run tiny smoke checks.

This script stays safe for read-only use: it prints package metadata, key
signatures, and optional smoke checks for core workflow and FugueSQL helpers.
"""
import argparse
import inspect
from importlib import import_module
from importlib.metadata import PackageNotFoundError, entry_points, version
from typing import Any, Iterable, Sequence


def _get_version(name: str) -> str:
    try:
        return version(name)
    except PackageNotFoundError:
        return "missing"
    except Exception as exc:  # pragma: no cover
        return f"error:{exc}"


def _print_versions() -> None:
    packages = [
        "fugue",
        "triad",
        "adagio",
        "pandas",
        "duckdb",
        "fugue-sql-antlr",
        "sqlglot",
        "dask",
        "distributed",
        "pyspark",
        "ray",
        "ibis-framework",
        "polars",
        "notebook",
        "jupyterlab",
        "flask",
        "matplotlib",
        "seaborn",
    ]
    for name in packages:
        print(f"{name}: {_get_version(name)}")


def _print_entry_points() -> None:
    groups = ["fugue.plugins", "pytest11"]
    for group in groups:
        try:
            eps = sorted(ep.name for ep in entry_points(group=group))
        except Exception as exc:  # pragma: no cover
            print(f"{group}: error:{exc}")
            continue
        print(f"{group}: {', '.join(eps) if eps else '<none>'}")


def _print_signatures() -> None:
    import fugue
    import fugue.api as fa
    from fugue.execution.factory import make_execution_engine

    items = [
        ("fugue.__version__", fugue.__version__),
        ("fa.transform", fa.transform),
        ("fa.out_transform", fa.out_transform),
        ("fa.fugue_sql", fa.fugue_sql),
        ("fa.fugue_sql_flow", fa.fugue_sql_flow),
        ("fa.raw_sql", fa.raw_sql),
        ("make_execution_engine", make_execution_engine),
    ]
    for name, obj in items:
        try:
            sig = inspect.signature(obj) if callable(obj) else obj
        except Exception as exc:  # pragma: no cover
            sig = f"error:{exc}"
        print(f"{name}: {sig}")


def _run_workflow_smoke() -> None:
    import pandas as pd

    import fugue.api as fa

    pdf = pd.DataFrame({"a": [0, 1], "b": [2, 3]})

    def plus(df: pd.DataFrame, inc: int = 1) -> pd.DataFrame:
        return df.assign(c=df.a + inc)

    out = fa.transform(pdf, plus, schema="*,c:int", params={"inc": 3}, as_fugue=True)
    print(f"workflow_transform: {out.as_array()}")


def _run_sql_smoke(engine: str) -> None:
    import pandas as pd

    import fugue.api as fa

    pdf = pd.DataFrame({"a": [0, 1], "b": [2, 3]})
    try:
        res = fa.fugue_sql(
            "SELECT a, b FROM pdf WHERE a < {{limit}}",
            pdf=pdf,
            limit=1,
            engine=engine,
            as_fugue=True,
        )
        print(f"fugue_sql[{engine}]: {res.as_array()}")
    except Exception as exc:
        print(f"fugue_sql[{engine}]: error:{exc}")
        raise

    flow = fa.fugue_sql_flow(
        """
        CREATE [[0], [1]] SCHEMA a:int
        YIELD DATAFRAME AS result
        """
    )
    result = flow.run(engine)
    print(f"fugue_sql_flow[{engine}]: {result['result'].as_array()}")


def _run_backend_imports() -> None:
    modules = [
        "fugue_duckdb",
        "fugue_dask",
        "fugue_spark",
        "fugue_ray",
        "fugue_ibis",
        "fugue_polars",
        "fugue_notebook",
        "fugue_contrib.viz",
        "fugue_contrib.seaborn",
    ]
    for name in modules:
        try:
            import_module(name)
            print(f"import:{name}:ok")
        except Exception as exc:
            print(f"import:{name}:error:{exc}")


def _run_notebook_smoke() -> None:
    try:
        import fugue_notebook
        from fugue_notebook import NotebookSetup, setup
    except Exception as exc:
        print(f"notebook-import:error:{exc}")
        raise
    print(f"fugue_notebook.setup: {inspect.signature(setup)}")
    print(f"NotebookSetup: {inspect.signature(NotebookSetup)}")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--check-sql",
        action="store_true",
        help="Run tiny FugueSQL smoke checks if the SQL dependencies are installed.",
    )
    parser.add_argument(
        "--sql-engine",
        default="duckdb",
        help="Engine name to use for the SQL smoke check (default: duckdb).",
    )
    parser.add_argument(
        "--check-backends",
        action="store_true",
        help="Import the known backend packages and print their registration state.",
    )
    parser.add_argument(
        "--check-notebook",
        action="store_true",
        help="Print notebook extension signatures and import status.",
    )
    parser.add_argument(
        "--check-workflow",
        action="store_true",
        help="Run the tiny core workflow smoke check.",
    )
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    _print_versions()
    _print_entry_points()
    _print_signatures()

    if args.check_workflow:
        _run_workflow_smoke()

    if args.check_backends:
        _run_backend_imports()

    if args.check_notebook:
        _run_notebook_smoke()

    if args.check_sql:
        _run_sql_smoke(args.sql_engine)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
