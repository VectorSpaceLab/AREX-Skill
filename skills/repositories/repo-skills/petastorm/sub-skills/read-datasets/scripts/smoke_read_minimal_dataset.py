#!/usr/bin/env python3
"""Create a tiny Petastorm dataset and verify core read paths.

Run:
    python scripts/smoke_read_minimal_dataset.py

Optional flag:
    --master local[1]

The script is read-only from the perspective of the repository and writes only to a temporary directory.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.types import FloatType, IntegerType

from petastorm import make_batch_reader, make_reader
from petastorm.codecs import NdarrayCodec, ScalarCodec
from petastorm.etl.dataset_metadata import materialize_dataset
from petastorm.unischema import Unischema, UnischemaField, dict_to_spark_row


TINY_SCHEMA = Unischema(
    "TinyReadSmokeSchema",
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


def _write_dataset(spark: SparkSession, output_url: str, rows: int) -> None:
    with materialize_dataset(spark, output_url, TINY_SCHEMA, row_group_size_mb=1):
        rdd = spark.sparkContext.parallelize(range(rows), 1).map(_row).map(lambda row: dict_to_spark_row(TINY_SCHEMA, row))
        spark.createDataFrame(rdd, TINY_SCHEMA.as_spark_schema()).coalesce(1).write.mode("overwrite").parquet(output_url)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", default="local[1]", help="Spark master for the smoke session")
    parser.add_argument("--rows", type=int, default=4, help="Number of tiny rows to write")
    args = parser.parse_args()

    spark = None
    try:
        with tempfile.TemporaryDirectory(prefix="petastorm-read-smoke-") as tmpdir:
            output_url = f"file://{Path(tmpdir).as_posix()}"
            spark = SparkSession.builder.master(args.master).appName("petastorm-read-smoke").getOrCreate()
            _write_dataset(spark, output_url, args.rows)
            spark.stop()
            spark = None

            with make_reader(output_url, reader_pool_type="dummy", num_epochs=1) as reader:
                row_ids = [row.id for row in reader]

            with make_batch_reader(output_url, reader_pool_type="dummy", num_epochs=1) as reader:
                batch_ids = []
                for batch in reader:
                    batch_ids.extend(batch.id.tolist())

            expected = list(range(args.rows))
            if row_ids != expected:
                raise AssertionError(f"reader ids mismatch: {row_ids} != {expected}")
            if batch_ids != expected:
                raise AssertionError(f"batch reader ids mismatch: {batch_ids} != {expected}")
            print(f"read_smoke_ok: {expected}")
            return 0
    except Exception as exc:  # pragma: no cover - environment-specific smoke helper
        print(f"read_smoke_failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
