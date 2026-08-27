#!/usr/bin/env python3
"""Moto-backed S3 smoke check for awswrangler.s3.

This script exercises a tiny parquet dataset round-trip and a simple object cleanup
flow without talking to real AWS resources.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path

import boto3
import pandas as pd
from moto import mock_aws

import awswrangler as wr


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="aws-sdk-pandas-smoke", help="Mock S3 bucket name to use.")
    parser.add_argument("--prefix", default="s3-smoke/", help="Prefix used for the temporary dataset.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    df = pd.DataFrame({"id": [1, 2, 3], "group": ["a", "a", "b"], "value": [10.0, 11.0, 12.0]})
    path = f"s3://{args.bucket}/{args.prefix}dataset/"

    with mock_aws():
        session = boto3.Session(region_name="us-east-1")
        s3 = session.client("s3")
        s3.create_bucket(Bucket=args.bucket)

        wr.s3.to_parquet(df=df, path=path, dataset=True, partition_cols=["group"], boto3_session=session)
        round_trip = wr.s3.read_parquet(path=path, dataset=True, boto3_session=session)
        keys = wr.s3.list_objects(path=path, boto3_session=session)

        # Clean up the dataset and ensure the prefix is empty afterwards.
        wr.s3.delete_objects(path=path, boto3_session=session)
        remaining = wr.s3.list_objects(path=path, boto3_session=session)

    assert len(round_trip.index) == len(df.index)
    assert set(round_trip.columns) == {"id", "group", "value"}
    assert len(keys) >= 1
    assert len(remaining) == 0

    print(
        json.dumps(
            {
                "bucket": args.bucket,
                "path": path,
                "rows": len(round_trip.index),
                "columns": list(round_trip.columns),
                "objects_before_delete": len(keys),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
