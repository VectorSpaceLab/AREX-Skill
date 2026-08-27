#!/usr/bin/env python3
"""Create a tiny Petastorm dataset and verify the TensorFlow read adapters.

Run:
    python scripts/smoke_read_tensorflow.py

Optional flag:
    --master local[1]

The script is safe to run locally and only writes to temporary directories.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
from pyspark.sql import SparkSession
from pyspark.sql.types import FloatType, IntegerType

from petastorm import make_reader
from petastorm.codecs import ScalarCodec
from petastorm.etl.dataset_metadata import materialize_dataset
from petastorm.unischema import Unischema, UnischemaField, dict_to_spark_row

TINY_SCHEMA = Unischema(
    "TinyTensorflowSmokeSchema",
    [
        UnischemaField("id", np.int32, (), ScalarCodec(IntegerType()), False),
        UnischemaField("score", np.float32, (), ScalarCodec(FloatType()), False),
    ],
)


def _row(x: int) -> dict:
    return {"id": x, "score": np.float32(x) + np.float32(0.25)}


def _write_dataset(spark: SparkSession, output_url: str, rows: int) -> None:
    with materialize_dataset(spark, output_url, TINY_SCHEMA, row_group_size_mb=1):
        rdd = spark.sparkContext.parallelize(range(rows), 1).map(_row).map(lambda row: dict_to_spark_row(TINY_SCHEMA, row))
        spark.createDataFrame(rdd, TINY_SCHEMA.as_spark_schema()).coalesce(1).write.mode("overwrite").parquet(output_url)


def _collect_tf_tensors(dataset_url: str, rows: int) -> list[int]:
    try:
        import tensorflow.compat.v1 as tf  # pylint: disable=import-error
    except Exception as exc:
        raise RuntimeError(f"tensorflow_missing: {type(exc).__name__}: {exc}") from exc

    tf.disable_v2_behavior()
    from petastorm.tf_utils import tf_tensors

    with make_reader(dataset_url, reader_pool_type="dummy", num_epochs=1, schema_fields=["^id$", "^score$"]) as reader:
        tensors = tf_tensors(reader)
        with tf.Session() as sess:
            ids = []
            for _ in range(rows):
                ids.append(int(sess.run(tensors).id))
            return ids


def _collect_tf_dataset(dataset_url: str, rows: int) -> list[int]:
    try:
        import tensorflow.compat.v1 as tf  # pylint: disable=import-error
    except Exception as exc:
        raise RuntimeError(f"tensorflow_missing: {type(exc).__name__}: {exc}") from exc

    tf.disable_v2_behavior()
    from petastorm.tf_utils import make_petastorm_dataset

    with make_reader(dataset_url, reader_pool_type="dummy", num_epochs=1, schema_fields=["^id$", "^score$"]) as reader:
        dataset = make_petastorm_dataset(reader)
        iterator = dataset.make_one_shot_iterator()
        next_item = iterator.get_next()
        with tf.Session() as sess:
            ids = []
            while True:
                try:
                    ids.append(int(sess.run(next_item).id))
                except tf.errors.OutOfRangeError:
                    break
            if len(ids) != rows:
                raise AssertionError(f"dataset produced {len(ids)} rows, expected {rows}")
            return ids


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", default="local[1]", help="Spark master for the smoke session")
    parser.add_argument("--rows", type=int, default=4, help="Number of tiny rows to write")
    args = parser.parse_args()

    spark = None
    try:
        with tempfile.TemporaryDirectory(prefix="petastorm-tf-smoke-") as tmpdir:
            output_url = f"file://{Path(tmpdir).as_posix()}"
            spark = SparkSession.builder.master(args.master).appName("petastorm-tensorflow-smoke").getOrCreate()
            _write_dataset(spark, output_url, args.rows)
            spark.stop()
            spark = None

            tf_ids = _collect_tf_tensors(output_url, args.rows)
            dataset_ids = _collect_tf_dataset(output_url, args.rows)
            expected = list(range(args.rows))
            if tf_ids != expected:
                raise AssertionError(f"tf_tensors ids mismatch: {tf_ids} != {expected}")
            if dataset_ids != expected:
                raise AssertionError(f"tf.data ids mismatch: {dataset_ids} != {expected}")
            print(f"tensorflow_smoke_ok: {expected}")
            return 0
    except RuntimeError as exc:
        print(f"tensorflow_smoke_failed: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - environment-specific smoke helper
        print(f"tensorflow_smoke_failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
