#!/usr/bin/env python3
"""Create a tiny Petastorm dataset and confirm the write-side contract.

Run:
    python scripts/smoke_make_minimal_dataset.py

Optional flag:
    --master local[1]

The helper only writes to a temporary directory and does not require any external data.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.types import FloatType, IntegerType

from petastorm.codecs import NdarrayCodec, ScalarCodec
from petastorm.etl.dataset_metadata import materialize_dataset, get_schema_from_dataset_url
from petastorm import make_reader
from petastorm.unischema import Unischema, UnischemaField, dict_to_spark_row


TINY_SCHEMA = Unischema(
    "TinyCreateSmokeSchema",
    [
        UnischemaField("id", np.int32, (), ScalarCodec(IntegerType()), False),
        UnischemaField("score", np.float32, (), ScalarCodec(FloatType()), False),
        UnischemaField("vector", np.float32, (2,), NdarrayCodec(), False),
    ],
)


def _row(x: int) -> dict:
    return {
        "id": x,
        "score": np.float32(x) + np.float32(0.5),
        "vector": np.asarray([x, x + 1], dtype=np.float32),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", default="local[1]", help="Spark master for the smoke session")
    parser.add_argument("--rows", type=int, default=4, help="Number of tiny rows to write")
    args = parser.parse_args()

    spark = None
    try:
        with tempfile.TemporaryDirectory(prefix="petastorm-create-smoke-") as tmpdir:
            output_path = Path(tmpdir)
            output_url = f"file://{output_path.as_posix()}"
            spark = SparkSession.builder.master(args.master).appName("petastorm-create-smoke").getOrCreate()
            with materialize_dataset(spark, output_url, TINY_SCHEMA, row_group_size_mb=1):
                rdd = spark.sparkContext.parallelize(range(args.rows), 1).map(_row).map(lambda row: dict_to_spark_row(TINY_SCHEMA, row))
                spark.createDataFrame(rdd, TINY_SCHEMA.as_spark_schema()).coalesce(1).write.mode("overwrite").parquet(output_url)

            inferred = get_schema_from_dataset_url(output_url)
            if list(inferred.fields) != list(TINY_SCHEMA.fields):
                raise AssertionError(f"schema mismatch: {list(inferred.fields)} != {list(TINY_SCHEMA.fields)}")

            with make_reader(output_url, reader_pool_type="dummy", num_epochs=1) as reader:
                ids = [row.id for row in reader]
            expected = list(range(args.rows))
            if ids != expected:
                raise AssertionError(f"reader ids mismatch: {ids} != {expected}")

            if not (output_path / "_common_metadata").exists():
                raise AssertionError("expected _common_metadata to exist")

            print(f"create_smoke_ok: {expected}")
            return 0
    except Exception as exc:  # pragma: no cover - environment-specific smoke helper
        print(f"create_smoke_failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
