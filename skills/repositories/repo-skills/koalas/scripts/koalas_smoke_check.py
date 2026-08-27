#!/usr/bin/env python3
"""Safe Koalas import, options, and tiny DataFrame smoke checks.

This helper uses only in-memory toy data. It may start a local Spark session, but
it does not download data, contact external services, or write persistent files.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path
import sys
from typing import Any, Iterable, Optional, Tuple


def configure_local_environment() -> None:
    """Set local-safe defaults before importing Koalas/PySpark."""
    os.environ.setdefault("SPARK_LOCAL_IP", "127.0.0.1")
    os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")
    os.environ.setdefault("PYARROW_IGNORE_TIMEZONE", "1")
    os.environ.setdefault("PYSPARK_PYTHON", sys.executable)
    os.environ.setdefault("PYSPARK_DRIVER_PYTHON", sys.executable)


def scrub(message: str) -> str:
    """Avoid echoing common private local path prefixes in diagnostics."""
    for value in (os.getcwd(), str(Path.home())):
        if value:
            message = message.replace(value, "<local-path>")
    return message


def explain_failure(phase: str, exc: BaseException) -> None:
    text = scrub(str(exc).strip() or repr(exc))
    lowered = text.lower()
    print(f"[{phase}] FAILED: {exc.__class__.__name__}: {text}", file=sys.stderr)
    print("Recovery hints:", file=sys.stderr)
    if "java" in lowered or "gateway" in lowered or "unsupportedclassversion" in lowered:
        print("- Verify Java/JAVA_HOME is compatible with the active PySpark version.", file=sys.stderr)
    if "different version" in lowered and "python" in lowered:
        print("- Set PYSPARK_PYTHON and PYSPARK_DRIVER_PYTHON to the same Python before Spark starts.", file=sys.stderr)
    if "unknownhost" in lowered or "bind" in lowered or "connection" in lowered:
        print("- For local smoke checks set SPARK_LOCAL_IP=127.0.0.1 before launching Python.", file=sys.stderr)
    if "pyarrow" in lowered or "timezone" in lowered or "arrow" in lowered:
        print("- Set PYARROW_IGNORE_TIMEZONE=1 before importing Koalas/starting Spark.", file=sys.stderr)
    if "no module" in lowered or "import" in lowered:
        print("- Install Koalas with compatible pandas, numpy, pyarrow, and pyspark dependencies.", file=sys.stderr)
    print("- See the Koalas skill troubleshooting references for workflow-specific recovery.", file=sys.stderr)


def import_packages() -> Tuple[Any, Any, Any]:
    configure_local_environment()
    import pandas as pd  # noqa: WPS433 - deliberate runtime diagnostic import
    import pyspark  # noqa: WPS433
    import databricks.koalas as ks  # noqa: WPS433

    return ks, pd, pyspark


def check_import() -> bool:
    try:
        ks, pd, pyspark = import_packages()
        print(
            "import ok: "
            f"koalas={getattr(ks, '__version__', 'unknown')}; "
            f"pandas={pd.__version__}; pyspark={pyspark.__version__}"
        )
        return True
    except Exception as exc:  # pragma: no cover - diagnostic path
        explain_failure("import", exc)
        return False


def check_options() -> bool:
    try:
        ks, _, _ = import_packages()
        original = ks.get_option("display.max_rows")
        with ks.option_context("display.max_rows", 7, "compute.default_index_type", "distributed"):
            assert ks.get_option("display.max_rows") == 7
            assert ks.get_option("compute.default_index_type") == "distributed"
        assert ks.get_option("display.max_rows") == original
        assert ks.get_option("compute.default_index_type") in {
            "sequence",
            "distributed",
            "distributed-sequence",
        }
        print("options ok: get_option, option_context, and reset-on-exit behavior passed")
        return True
    except Exception as exc:  # pragma: no cover - diagnostic path
        explain_failure("options", exc)
        return False


def check_dataframe() -> bool:
    try:
        ks, pd, _ = import_packages()
        pdf = pd.DataFrame(
            {"row_id": [1, 2, 3], "city": ["London", "New York", "Helsinki"], "value": [10, 20, 30]}
        ).set_index("row_id")
        kdf = ks.from_pandas(pdf)
        kdf["city_lower"] = kdf["city"].str.lower()
        kdf["double"] = kdf["value"] * 2
        actual = kdf.loc[kdf["value"] >= 20, ["city_lower", "double"]].sort_index().to_pandas()
        expected = pd.DataFrame(
            {"city_lower": ["new york", "helsinki"], "double": [40, 60]},
            index=pd.Index([2, 3], name="row_id"),
        )
        pd.testing.assert_frame_equal(actual, expected)
        sdf = kdf.to_spark(index_col="row_id")
        assert "row_id" in sdf.columns
        assert int(ks.range(0, 4)["id"].sum()) == 6
        print("dataframe ok: from_pandas, indexing, string operations, Spark index_col, and range passed")
        return True
    except Exception as exc:  # pragma: no cover - diagnostic path
        explain_failure("dataframe", exc)
        return False


def parse_args(argv: Optional[Iterable[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run safe Koalas setup smoke checks on tiny data.")
    parser.add_argument(
        "--mode",
        choices=("import", "options", "dataframe", "all"),
        default="all",
        help="Which smoke check to run. Default: all.",
    )
    return parser.parse_args(list(argv) if argv is not None else None)


def main(argv: Optional[Iterable[str]] = None) -> int:
    args = parse_args(argv)
    if args.mode == "import":
        return 0 if check_import() else 1
    if args.mode == "options":
        return 0 if check_options() else 1
    if args.mode == "dataframe":
        return 0 if check_dataframe() else 1

    results = [check_import(), check_options(), check_dataframe()]
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
