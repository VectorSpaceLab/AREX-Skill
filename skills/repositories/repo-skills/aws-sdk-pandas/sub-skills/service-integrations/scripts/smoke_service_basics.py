#!/usr/bin/env python3
"""Smoke check for STS, Secrets Manager, Chime validation, and Neptune helpers."""

from __future__ import annotations

import argparse
import json

import boto3
import pandas as pd
from moto import mock_aws

import awswrangler as wr


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--secret-name", default="aws-sdk-pandas-smoke-secret", help="Mock secret name.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    with mock_aws():
        session = boto3.Session(region_name="us-east-1")
        secrets = session.client("secretsmanager")
        secrets.create_secret(Name=args.secret_name, SecretString=json.dumps({"token": "abc", "env": "test"}))

        account_id = wr.sts.get_account_id(boto3_session=session)
        secret = wr.secretsmanager.get_secret_json(name=args.secret_name, boto3_session=session)

    flat = wr.neptune.flatten_nested_df(
        pd.DataFrame({"s": ["a"], "nested": [{"x": 1, "y": {"z": 2}}], "arr": [[1, 2]]})
    )

    try:
        wr.chime.post_message(webhook=None, message=None)
    except ValueError:
        chime_validation_ok = True
    else:
        chime_validation_ok = False

    assert len(account_id) == 12 and account_id.isdigit()
    assert secret == {"token": "abc", "env": "test"}
    assert len(flat.index) == 2
    assert "nested_x" in flat.columns and "nested_y_z" in flat.columns
    assert chime_validation_ok is True

    print(
        json.dumps(
            {
                "account_id": account_id,
                "secret_keys": sorted(secret.keys()),
                "flattened_rows": len(flat.index),
                "flattened_columns": list(flat.columns),
                "chime_validation_ok": chime_validation_ok,
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
