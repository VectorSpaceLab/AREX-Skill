#!/usr/bin/env python3
"""Moto-backed Glue Catalog smoke check for awswrangler.catalog.

This script creates a tiny Glue database and parquet table, registers partitions,
and verifies the catalog state without talking to real AWS resources.
"""

from __future__ import annotations

import argparse
import json

import boto3
import pandas as pd
from moto import mock_aws

import awswrangler as wr


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--bucket", default="aws-sdk-pandas-catalog-smoke", help="Mock S3 bucket name.")
    parser.add_argument("--database", default="smoke_db", help="Glue database name to create.")
    parser.add_argument("--table", default="smoke_table", help="Glue table name to create.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    df = pd.DataFrame({"id": [1, 2], "dt": ["2026-01-01", "2026-01-02"], "value": [10.0, 11.0]})
    path = f"s3://{args.bucket}/datasets/{args.table}/"
    partitions = {f"{path}dt=2026-01-01/": ["2026-01-01"], f"{path}dt=2026-01-02/": ["2026-01-02"]}

    with mock_aws():
        session = boto3.Session(region_name="us-east-1")
        s3 = session.client("s3")
        s3.create_bucket(Bucket=args.bucket)

        wr.catalog.create_database(name=args.database, boto3_session=session)
        wr.catalog.create_parquet_table(
            database=args.database,
            table=args.table,
            path=path,
            columns_types={"id": "bigint", "dt": "date", "value": "double"},
            partitions_types={"dt": "date"},
            boto3_session=session,
        )
        wr.catalog.add_parquet_partitions(
            database=args.database,
            table=args.table,
            partitions_values=partitions,
            boto3_session=session,
        )

        dbs = list(wr.catalog.get_databases(boto3_session=session))
        tables = list(wr.catalog.get_tables(database=args.database, boto3_session=session))
        part_map = wr.catalog.get_partitions(database=args.database, table=args.table, boto3_session=session)
        exists = wr.catalog.does_table_exist(database=args.database, table=args.table, boto3_session=session)

    assert exists is True
    assert len(dbs) >= 1
    assert len(tables) >= 1
    assert part_map == partitions
    assert list(df.columns) == ["id", "dt", "value"]

    print(
        json.dumps(
            {
                "database": args.database,
                "table": args.table,
                "database_count": len(dbs),
                "table_count": len(tables),
                "partition_count": len(part_map),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
