#!/usr/bin/env python3
"""Safe Koalas core DataFrame quickstart.

Runs tiny local checks only. It does not download data, open network resources, or
write output files. Some checks may start a local Spark session through Koalas.
"""

import argparse
import os
from pathlib import Path
import sys
from typing import Any, Tuple


def configure_local_environment() -> None:
    """Set conservative local defaults before importing Spark/Koalas."""
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
    os.environ.setdefault("PYARROW_IGNORE_TIMEZONE", "1")
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)


def safe_message(exc: BaseException) -> str:
    """Return an exception message without echoing common private path prefixes."""
    message = str(exc).strip() or repr(exc)
    for value in (os.getcwd(), str(Path.home())):
        if value:
            message = message.replace(value, "<local-path>")
    return message


def print_failure(phase: str, exc: BaseException) -> None:
    print(f"[{phase}] FAILED: {exc.__class__.__name__}: {safe_message(exc)}", file=sys.stderr)
    lowered = safe_message(exc).lower()
    print("\nFriendly recovery hints:", file=sys.stderr)
    if "java" in lowered or "gateway" in lowered or "spark" in lowered:
        print("- Koalas uses PySpark under the hood; verify Java and a local Spark/PySpark setup.", file=sys.stderr)
        print("- If a Spark session already exists, ensure it is compatible with Koalas 1.x.", file=sys.stderr)
    if "pyspark" in lowered or "databricks.koalas" in lowered or "no module" in lowered:
        print("- Install a Koalas-compatible Python environment with pandas, pyarrow, and pyspark.", file=sys.stderr)
    if "arrow" in lowered or "timezone" in lowered:
        print("- Set PYARROW_IGNORE_TIMEZONE=1 before starting Spark, then retry.", file=sys.stderr)
    print("- This helper uses only tiny in-memory data; failures are usually environment/setup issues.", file=sys.stderr)


def import_koalas() -> Tuple[Any, Any]:
    configure_local_environment()
    import pandas as pd  # noqa: WPS433 - runtime check import
    import databricks.koalas as ks  # noqa: WPS433 - runtime check import

    return ks, pd


def check_import() -> bool:
    try:
        ks, pd = import_koalas()
        version = getattr(ks, "__version__", "unknown")
        print(f"import ok: databricks.koalas version={version}; pandas version={pd.__version__}")
        return True
    except Exception as exc:  # pragma: no cover - diagnostic path
        print_failure("import", exc)
        return False


def check_dataframe() -> bool:
    try:
        ks, pd = import_koalas()

        pdf = pd.DataFrame(
            {
                "id": [1, 2, 3],
                "city": ["London", "New York", "Helsinki"],
                "value": [1.5, None, 3.0],
            },
            index=pd.Index([10, 11, 12], name="row_id"),
        )
        kdf = ks.from_pandas(pdf)
        kdf["city_lower"] = kdf["city"].str.lower()
        kdf["value_filled"] = kdf["value"].fillna(0.0).astype("float64")

        selected = kdf.loc[kdf["id"] >= 2, ["city_lower", "value_filled"]].sort_index()
        actual = selected.to_pandas()
        expected = pd.DataFrame(
            {
                "city_lower": ["new york", "helsinki"],
                "value_filled": [0.0, 3.0],
            },
            index=pd.Index([11, 12], name="row_id"),
        )
        pd.testing.assert_frame_equal(actual, expected)

        rng = ks.range(0, 3)
        assert int(rng["id"].sum()) == 3

        parsed = ks.to_datetime(ks.Series(["2021-01-01", "2021-01-02"]), format="%Y-%m-%d")
        assert parsed.dt.year.to_pandas().tolist() == [2021, 2021]

        unsafe_pdf = pd.DataFrame([[1, 2, 3]], columns=["a", "A", "__column__"])
        unsafe = [
            column
            for column in unsafe_pdf.columns
            if str(column).startswith("__") and str(column).endswith("__")
        ]
        assert unsafe == ["__column__"]

        spark_columns = kdf.to_spark(index_col="row_id").columns
        assert "row_id" in spark_columns

        print("dataframe ok: constructors, from_pandas, indexing, string/datetime, range, and index-preserving to_spark passed")
        return True
    except Exception as exc:  # pragma: no cover - diagnostic path
        print_failure("dataframe", exc)
        return False


def parse_args(argv: Any = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run safe tiny Koalas DataFrame/Series/Index quickstart checks.",
    )
    parser.add_argument(
        "--check",
        choices=("import", "dataframe", "all"),
        default="all",
        help="Which check to run. 'dataframe' includes an import check implicitly.",
    )
    return parser.parse_args(argv)


def main(argv: Any = None) -> int:
    args = parse_args(argv)
    if args.check == "import":
        return 0 if check_import() else 1
    if args.check == "dataframe":
        return 0 if check_dataframe() else 1

    ok_import = check_import()
    ok_dataframe = check_dataframe() if ok_import else False
    return 0 if ok_import and ok_dataframe else 1


if __name__ == "__main__":
    raise SystemExit(main())
