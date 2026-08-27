#!/usr/bin/env python3
"""Create a tiny Petastorm dataset and verify the PyTorch read adapters.

Run:
    python scripts/smoke_read_torch.py

Optional flag:
    --master local[1]

The helper imports pyarrow before torch, matching the repository troubleshooting guidance.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

import numpy as np
import pyarrow  # noqa: F401  # keep this import before torch
from pyspark.sql import SparkSession
from pyspark.sql.types import FloatType, IntegerType

from petastorm import make_reader
from petastorm.codecs import ScalarCodec
from petastorm.etl.dataset_metadata import materialize_dataset
from petastorm.unischema import Unischema, UnischemaField, dict_to_spark_row


TINY_SCHEMA = Unischema(
    "TinyTorchSmokeSchema",
    [
        UnischemaField("id", np.int32, (), ScalarCodec(IntegerType()), False),
        UnischemaField("score", np.float32, (), ScalarCodec(FloatType()), False),
    ],
)


def _row(x: int) -> dict:
    return {"id": x, "score": np.float32(x) + np.float32(0.75)}


def _write_dataset(spark: SparkSession, output_url: str, rows: int) -> None:
    with materialize_dataset(spark, output_url, TINY_SCHEMA, row_group_size_mb=1):
        rdd = spark.sparkContext.parallelize(range(rows), 1).map(_row).map(lambda row: dict_to_spark_row(TINY_SCHEMA, row))
        spark.createDataFrame(rdd, TINY_SCHEMA.as_spark_schema()).coalesce(1).write.mode("overwrite").parquet(output_url)


def _collect_ids(loader) -> list[int]:
    ids = []
    for batch in loader:
        ids.extend(int(v) for v in batch["id"].tolist())
    return ids


def _make_reader(dataset_url: str):
    return make_reader(dataset_url, reader_pool_type="dummy", num_epochs=1, schema_fields=["^id$", "^score$"])


def _load_torch_loaders():
    try:
        from petastorm.pytorch import BatchedDataLoader, DataLoader
    except Exception as exc:
        raise RuntimeError(f"torch_missing: {type(exc).__name__}: {exc}") from exc
    return DataLoader, BatchedDataLoader


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", default="local[1]", help="Spark master for the smoke session")
    parser.add_argument("--rows", type=int, default=4, help="Number of tiny rows to write")
    args = parser.parse_args()

    spark = None
    try:
        with tempfile.TemporaryDirectory(prefix="petastorm-torch-smoke-") as tmpdir:
            output_url = f"file://{Path(tmpdir).as_posix()}"
            spark = SparkSession.builder.master(args.master).appName("petastorm-torch-smoke").getOrCreate()
            _write_dataset(spark, output_url, args.rows)
            spark.stop()
            spark = None

            DataLoader, BatchedDataLoader = _load_torch_loaders()
            with DataLoader(_make_reader(output_url), batch_size=2) as loader:
                loader_ids = _collect_ids(loader)

            with BatchedDataLoader(_make_reader(output_url), batch_size=2) as loader:
                batched_ids = _collect_ids(loader)

            expected = list(range(args.rows))
            if loader_ids != expected:
                raise AssertionError(f"DataLoader ids mismatch: {loader_ids} != {expected}")
            if batched_ids != expected:
                raise AssertionError(f"BatchedDataLoader ids mismatch: {batched_ids} != {expected}")
            print(f"torch_smoke_ok: {expected}")
            return 0
    except RuntimeError as exc:
        print(f"torch_smoke_failed: {exc}")
        return 1
    except Exception as exc:  # pragma: no cover - environment-specific smoke helper
        print(f"torch_smoke_failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
