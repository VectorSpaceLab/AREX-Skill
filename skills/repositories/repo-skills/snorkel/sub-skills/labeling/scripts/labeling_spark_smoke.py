#!/usr/bin/env python3
"""Tiny local Spark smoke for Snorkel labeling.

Java and PySpark are optional dependencies. If they are unavailable, this script
prints a skip message and exits cleanly.
"""

from __future__ import annotations

import os
import warnings
from types import SimpleNamespace
from typing import Any


def _spark_square(x: Any) -> Any:
    return SimpleNamespace(num=x.num, text=x.text, num_squared=x.num**2)


def _spark_is_big(x: Any) -> int:
    return 1 if x.num > 10 else -1


def _spark_mentions_cat(x: Any) -> int:
    return 0 if "cat" in str(x.text).lower() else -1


def _spark_square_big(x: Any) -> int:
    return 1 if x.num_squared > 100 else -1


def main() -> int:
    try:
        import numpy as np
        from pyspark.sql import SparkSession
        from snorkel.labeling import labeling_function
        from snorkel.labeling.apply.spark import SparkLFApplier
        from snorkel.preprocess import preprocessor
    except Exception as exc:  # pragma: no cover - dependency gate
        print(f"SKIP: Spark smoke not run ({exc}). Java and PySpark are optional.")
        return 0

    warnings.filterwarnings("ignore", category=FutureWarning)
    os.environ.setdefault("SPARK_LOCAL_HOSTNAME", "localhost")

    square = preprocessor()(_spark_square)
    is_big = labeling_function()(_spark_is_big)
    mentions_cat = labeling_function()(_spark_mentions_cat)
    square_big = labeling_function(pre=[square])(_spark_square_big)

    spark = None
    try:
        spark = (
            SparkSession.builder.master("local[1]")
            .appName("snorkel_labeling_spark_smoke")
            .config("spark.ui.showConsoleProgress", "false")
            .getOrCreate()
        )
        spark.sparkContext.setLogLevel("ERROR")

        rows = [
            {"num": 5, "text": "cat"},
            {"num": 20, "text": "small"},
            {"num": 3, "text": "dog"},
            {"num": 11, "text": "cat nap"},
        ]
        rdd = spark.createDataFrame(rows).rdd
        L = SparkLFApplier([is_big, mentions_cat, square_big]).apply(rdd)

        expected = np.array(
            [
                [-1, 0, -1],
                [1, -1, 1],
                [-1, -1, -1],
                [1, 0, 1],
            ]
        )
        np.testing.assert_array_equal(L, expected)

        print("SPARK_LOCAL_HOSTNAME:", os.environ.get("SPARK_LOCAL_HOSTNAME"))
        print("L shape:", L.shape)
        print("L matrix:", L.tolist())
        print("matches expected:", np.array_equal(L, expected))
        return 0
    except Exception as exc:  # pragma: no cover - environment gate
        print(f"SKIP: Spark smoke could not start locally ({exc}). Java and PySpark are optional.")
        return 0
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
