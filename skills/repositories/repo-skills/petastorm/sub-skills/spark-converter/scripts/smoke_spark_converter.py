#!/usr/bin/env python3
"""Create a tiny Spark DataFrame, materialize a converter, and verify the loaders.

Run:
    python scripts/smoke_spark_converter.py

Optional flag:
    --master local[1]

The helper uses a local Spark cache path, verifies converter cleanup, and only tries TensorFlow or PyTorch if the extras are installed.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path
from urllib.parse import urlparse

import pyarrow  # noqa: F401  # imported early so later torch imports follow the repository rule
from pyspark.sql import SparkSession

from petastorm.spark import SparkDatasetConverter, make_spark_converter


def _build_dataframe(spark: SparkSession, rows: int):
    return spark.range(rows).selectExpr("cast(id as int) as feature", "cast(id % 2 as int) as label")


def _check_tf(converter) -> None:
    try:
        import tensorflow.compat.v1 as tf  # pylint: disable=import-error
    except Exception as exc:
        print(f"tf_missing: {type(exc).__name__}: {exc}")
        return

    tf.disable_v2_behavior()
    with tf.Graph().as_default():
        with converter.make_tf_dataset(batch_size=2, num_epochs=1) as dataset:
            iterator = dataset.make_one_shot_iterator()
            next_item = iterator.get_next()
            with tf.Session() as sess:
                batch = sess.run(next_item)
                print(f"tf_batch_rows: {len(batch.feature)}")


def _check_torch(converter) -> None:
    try:
        import torch
    except Exception as exc:
        print(f"torch_missing: {type(exc).__name__}: {exc}")
        return

    with converter.make_torch_dataloader(batch_size=2, num_epochs=1) as loader:
        batch = next(iter(loader))
        print(f"torch_batch_rows: {len(batch['feature'])}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", default="local[1]", help="Spark master for the smoke session")
    parser.add_argument("--rows", type=int, default=4, help="Number of DataFrame rows to materialize")
    args = parser.parse_args()

    spark = None
    try:
        with tempfile.TemporaryDirectory(prefix="petastorm-converter-smoke-") as tmpdir:
            cache_url = f"file://{Path(tmpdir).as_posix()}"
            spark = SparkSession.builder.master(args.master).appName("petastorm-converter-smoke").getOrCreate()
            spark.conf.set(SparkDatasetConverter.PARENT_CACHE_DIR_URL_CONF, cache_url)
            df = _build_dataframe(spark, args.rows)
            converter = make_spark_converter(df)

            if len(converter) != args.rows:
                raise AssertionError(f"converter length mismatch: {len(converter)} != {args.rows}")
            if not converter.file_urls:
                raise AssertionError("converter did not expose cached file URLs")

            _check_tf(converter)
            _check_torch(converter)

            cache_path = Path(urlparse(converter.cache_dir_url).path)
            converter.delete()
            if cache_path.exists():
                raise AssertionError("converter cache still exists after delete()")

            print(f"spark_converter_smoke_ok: rows={args.rows}")
            return 0
    except Exception as exc:  # pragma: no cover - environment-specific smoke helper
        print(f"spark_converter_smoke_failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
