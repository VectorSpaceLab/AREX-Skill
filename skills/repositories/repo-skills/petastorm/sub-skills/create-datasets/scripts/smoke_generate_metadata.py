#!/usr/bin/env python3
"""Create a tiny dataset and exercise metadata regeneration.

Run:
    python scripts/smoke_generate_metadata.py

Optional flag:
    --master local[1]
    --use-summary-metadata

The helper writes to a temporary directory and uses the package metadata regeneration entry point.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType

from petastorm import make_reader
from petastorm.codecs import ScalarCodec
from petastorm.etl.dataset_metadata import materialize_dataset
from petastorm.etl import petastorm_generate_metadata
from petastorm.unischema import Unischema, UnischemaField, dict_to_spark_row


TINY_SCHEMA = Unischema(
    "TinyMetadataSmokeSchema",
    [
        UnischemaField("id", np.int32, (), ScalarCodec(IntegerType()), False),
        UnischemaField("value", np.int32, (), ScalarCodec(IntegerType()), False),
    ],
)


def _row(x: int) -> dict:
    return {"id": x, "value": x * 10}


def _write_dataset(spark: SparkSession, output_url: str, rows: int) -> None:
    with materialize_dataset(spark, output_url, TINY_SCHEMA, row_group_size_mb=1):
        rdd = spark.sparkContext.parallelize(range(rows), 1).map(_row).map(lambda row: dict_to_spark_row(TINY_SCHEMA, row))
        spark.createDataFrame(rdd, TINY_SCHEMA.as_spark_schema()).coalesce(1).write.mode("overwrite").parquet(output_url)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", default="local[1]", help="Spark master for the smoke session")
    parser.add_argument("--rows", type=int, default=4, help="Number of tiny rows to write")
    parser.add_argument("--use-summary-metadata", action="store_true", help="Rebuild summary metadata as well")
    args = parser.parse_args()

    spark = None
    try:
        with tempfile.TemporaryDirectory(prefix="petastorm-metadata-smoke-") as tmpdir:
            output_url = f"file://{Path(tmpdir).as_posix()}"
            spark = SparkSession.builder.master(args.master).appName("petastorm-metadata-smoke").getOrCreate()
            _write_dataset(spark, output_url, args.rows)
            spark.stop()
            spark = None

            cli_args = ["--dataset_url", output_url, "--master", args.master]
            if args.use_summary_metadata:
                cli_args.append("--use-summary-metadata")
            petastorm_generate_metadata._main(cli_args)

            with make_reader(output_url, reader_pool_type="dummy", num_epochs=1) as reader:
                ids = [row.id for row in reader]

            expected = list(range(args.rows))
            if ids != expected:
                raise AssertionError(f"metadata smoke ids mismatch: {ids} != {expected}")
            if not (Path(tmpdir) / "_common_metadata").exists():
                raise AssertionError("expected _common_metadata to exist")
            print(f"metadata_smoke_ok: {expected}")
            return 0
    except Exception as exc:  # pragma: no cover - environment-specific smoke helper
        print(f"metadata_smoke_failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
