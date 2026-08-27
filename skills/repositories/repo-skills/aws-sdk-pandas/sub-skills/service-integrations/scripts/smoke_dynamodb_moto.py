#!/usr/bin/env python3
"""Moto-backed DynamoDB smoke check for awswrangler.dynamodb."""

from __future__ import annotations

import argparse
import json

import boto3
from moto import mock_aws

import awswrangler as wr


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--table", default="aws_sdk_pandas_dynamodb_smoke", help="Mock DynamoDB table name.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    items = [{"pk": "a", "value": 1}, {"pk": "b", "value": 2}]

    with mock_aws():
        session = boto3.Session(region_name="us-east-1")
        dynamodb = session.client("dynamodb")
        dynamodb.create_table(
            TableName=args.table,
            KeySchema=[{"AttributeName": "pk", "KeyType": "HASH"}],
            AttributeDefinitions=[{"AttributeName": "pk", "AttributeType": "S"}],
            BillingMode="PAY_PER_REQUEST",
        )

        wr.dynamodb.put_items(items=items, table_name=args.table, boto3_session=session)
        table = wr.dynamodb.get_table(table_name=args.table, boto3_session=session)
        item_count_before_delete = table.item_count
        read_back = wr.dynamodb.read_items(table_name=args.table, allow_full_scan=True, boto3_session=session)
        read_rows = len(read_back.index)
        wr.dynamodb.delete_items(items=items, table_name=args.table, boto3_session=session)
        table_after_delete = wr.dynamodb.get_table(table_name=args.table, boto3_session=session)
        item_count_after_delete = table_after_delete.item_count

    assert item_count_before_delete == len(items)
    assert read_rows == len(items)
    assert item_count_after_delete == 0

    print(
        json.dumps(
            {
                "table": args.table,
                "item_count_before_delete": item_count_before_delete,
                "read_rows": read_rows,
                "item_count_after_delete": item_count_after_delete,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
