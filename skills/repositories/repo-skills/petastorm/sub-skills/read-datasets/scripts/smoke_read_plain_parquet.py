#!/usr/bin/env python3
"""Create a tiny plain Parquet store and verify the batch-reader path.

Run:
    python scripts/smoke_read_plain_parquet.py

Optional flag:
    --master local[1]

The script writes only to a temporary directory and does not require Petastorm metadata.
"""
from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from pyspark.sql import SparkSession

from petastorm import make_batch_reader


def _build_rows(rows: int):
    for x in range(rows):
        yield {"id": x, "value1": x + 10, "value2": x + 20}


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--master", default="local[1]", help="Spark master for the smoke session")
    parser.add_argument("--rows", type=int, default=4, help="Number of tiny rows to write")
    args = parser.parse_args()

    spark = None
    try:
        with tempfile.TemporaryDirectory(prefix="petastorm-plain-parquet-smoke-") as tmpdir:
            output_path = Path(tmpdir)
            output_url = f"file://{output_path.as_posix()}"
            spark = SparkSession.builder.master(args.master).appName("petastorm-plain-parquet-smoke").getOrCreate()
            rows_df = spark.createDataFrame(list(_build_rows(args.rows)))
            rows_df.write.mode("overwrite").parquet(str(output_path))
            spark.stop()
            spark = None

            with make_batch_reader(output_url, reader_pool_type="dummy", num_epochs=1, schema_fields=["^id$", "^value1$", "^value2$"]) as reader:
                rows = []
                for batch in reader:
                    rows.extend(batch.id.tolist())

            expected = list(range(args.rows))
            if rows != expected:
                raise AssertionError(f"batch reader ids mismatch: {rows} != {expected}")
            print(f"plain_parquet_smoke_ok: {expected}")
            return 0
    except Exception as exc:  # pragma: no cover - environment-specific smoke helper
        print(f"plain_parquet_smoke_failed: {type(exc).__name__}: {exc}")
        return 1
    finally:
        if spark is not None:
            spark.stop()


if __name__ == "__main__":
    raise SystemExit(main())
