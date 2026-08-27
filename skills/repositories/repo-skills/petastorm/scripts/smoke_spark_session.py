#!/usr/bin/env python3
"""Start a local Spark session and run a minimal Petastorm-compatible Spark smoke check.

Run:
    python scripts/smoke_spark_session.py

Optional flag:
    --master local[1]

The script is read-only and only verifies that Spark can start and execute a tiny job.
"""
from __future__ import annotations

import argparse
import sys


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", default="local[1]", help="Spark master for the smoke session")
    args = parser.parse_args()

    try:
        from pyspark.sql import SparkSession
    except Exception as exc:  # pragma: no cover - environment-specific
        print(f"spark_unavailable: {type(exc).__name__}: {exc}")
        return 1

    spark = None
    try:
        spark = SparkSession.builder.master(args.master).appName("petastorm-spark-smoke").getOrCreate()
        count = spark.range(3).count()
        answer = spark.sql("select 1 as answer").collect()[0][0]
        print(f"spark_version: {spark.version}")
        print(f"range_count: {count}")
        print(f"sql_answer: {answer}")
        return 0
    except Exception as exc:  # pragma: no cover - environment-specific
        print(f"spark_smoke_failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    sys.exit(main())
