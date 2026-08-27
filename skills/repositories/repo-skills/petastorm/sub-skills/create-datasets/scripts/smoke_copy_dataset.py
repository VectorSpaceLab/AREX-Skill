#!/usr/bin/env python3
"""Create a tiny dataset, copy it, and confirm filter behavior.

Run:
    python scripts/smoke_copy_dataset.py

Optional flag:
    --master local[1]

The helper writes only temporary files and validates the copied output with a Petastorm reader.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.types import IntegerType, StringType

from petastorm import make_reader
from petastorm.codecs import ScalarCodec
from petastorm.etl.dataset_metadata import materialize_dataset
from petastorm.tools.copy_dataset import copy_dataset
from petastorm.unischema import Unischema, UnischemaField, dict_to_spark_row


COPY_SCHEMA = Unischema(
    "TinyCopySmokeSchema",
    [
        UnischemaField("id", np.int32, (), ScalarCodec(IntegerType()), False),
        UnischemaField("label", np.int32, (), ScalarCodec(IntegerType()), False),
        UnischemaField("note", np.str_, (), ScalarCodec(StringType()), True),
    ],
)


def _row(x: int) -> dict:
    return {
        "id": x,
        "label": x % 2,
        "note": None if x == 1 else f"note-{x}",
    }


def _write_source_dataset(spark: SparkSession, output_url: str, rows: int) -> None:
    with materialize_dataset(spark, output_url, COPY_SCHEMA, row_group_size_mb=1):
        rdd = spark.sparkContext.parallelize(range(rows), 1).map(_row).map(lambda row: dict_to_spark_row(COPY_SCHEMA, row))
        spark.createDataFrame(rdd, COPY_SCHEMA.as_spark_schema()).coalesce(1).write.mode("overwrite").parquet(output_url)



def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", default="local[1]", help="Spark master for the smoke session")
    parser.add_argument("--rows", type=int, default=4, help="Number of tiny rows to write")
    args = parser.parse_args()

    spark = None
    try:
        with tempfile.TemporaryDirectory(prefix="petastorm-copy-smoke-") as tmpdir:
            base = Path(tmpdir)
            source_url = f"file://{(base / 'source').as_posix()}"
            target_url = f"file://{(base / 'target').as_posix()}"
            spark = SparkSession.builder.master(args.master).appName("petastorm-copy-smoke").getOrCreate()
            _write_source_dataset(spark, source_url, args.rows)
            copy_dataset(
                spark,
                source_url,
                target_url,
                field_regex=[r"^id$", r"^label$", r"^note$"],
                not_null_fields=["note"],
                overwrite_output=True,
                partitions_count=1,
                row_group_size_mb=1,
            )

            with make_reader(target_url, reader_pool_type="dummy", num_epochs=1) as reader:
                rows = list(reader)

            if not rows:
                raise AssertionError("copied dataset was empty")
            if any(row.note is None for row in rows):
                raise AssertionError("copied dataset still contains null note values")
            if set(rows[0]._fields) != {"id", "label", "note"}:
                raise AssertionError(f"unexpected copied schema fields: {list(rows[0]._fields)}")
            if len(rows) >= args.rows:
                raise AssertionError("null filtering did not reduce the row count")

            print(f"copy_smoke_ok: source={args.rows} copied={len(rows)}")
            return 0
    except Exception as exc:  # pragma: no cover - environment-specific smoke helper
        print(f"copy_smoke_failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
