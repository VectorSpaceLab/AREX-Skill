#!/usr/bin/env python3
"""Mocked smoke check for awswrangler.s3 vector helpers.

The script patches the internal boto3 client factory so the public vector APIs can
be exercised without the live S3 Vectors service.
"""

from __future__ import annotations

import argparse
import json
from collections.abc import Callable
from contextlib import contextmanager
from typing import Any
from unittest.mock import MagicMock, patch

import numpy as np
import pandas as pd

import awswrangler as wr


@contextmanager
def patched_client(client: MagicMock):
    with patch("awswrangler._utils.client", return_value=client):
        yield


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--vector-bucket", default="mock-bucket", help="Mock vector bucket name.")
    parser.add_argument("--index", default="mock-index", help="Mock vector index name.")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    client = MagicMock()
    client.create_vector_bucket.return_value = {"vectorBucketArn": f"arn:aws:s3vectors:::bucket/{args.vector_bucket}"}
    client.create_index.return_value = {"indexArn": f"arn:aws:s3vectors:::bucket/{args.vector_bucket}/index/{args.index}"}
    client.put_vectors.return_value = {}
    client.get_vectors.return_value = {
        "vectors": [
            {"key": "k1", "data": {"float32": [0.1, 0.2]}, "metadata": {"label": "x"}},
        ]
    }
    client.list_vectors.side_effect = [
        {"vectors": [{"key": "k1"}], "nextToken": "next"},
        {"vectors": [{"key": "k2"}]},
    ]
    client.query_vectors.return_value = {
        "vectors": [{"key": "k1", "distance": 0.01, "metadata": {"label": "x"}}],
        "distanceMetric": "cosine",
    }

    df = pd.DataFrame({"key": ["k1", "k2"], "embedding": [[0.1, 0.2], [0.3, 0.4]], "label": ["x", "y"]})

    with patched_client(client):
        bucket_arn = wr.s3.create_vector_bucket(args.vector_bucket, sse_type="aws:kms")
        index_arn = wr.s3.create_vector_index(
            name=args.index,
            dimension=2,
            vector_bucket=args.vector_bucket,
            distance_metric="cosine",
        )
        wr.s3.put_vectors_from_df(
            df=df,
            key_column="key",
            vector_column="embedding",
            metadata_columns=["label"],
            vector_bucket=args.vector_bucket,
            index=args.index,
            use_threads=False,
        )
        by_key = wr.s3.get_vectors(
            keys=["k1"],
            return_data=True,
            return_metadata=True,
            vector_bucket=args.vector_bucket,
            index=args.index,
            use_threads=False,
        )
        listed = wr.s3.list_vectors(vector_bucket=args.vector_bucket, index=args.index, use_threads=False)
        queried = wr.s3.query_vectors(
            query_vector=np.array([0.1, 0.2], dtype=np.float32),
            top_k=1,
            vector_bucket=args.vector_bucket,
            index=args.index,
        )

    assert bucket_arn.endswith(args.vector_bucket)
    assert index_arn.endswith(f"index/{args.index}")
    assert len(by_key.index) == 1 and by_key.iloc[0]["key"] == "k1"
    assert len(listed.index) == 2
    assert listed.iloc[0]["key"] == "k1"
    assert queried.attrs.get("distance_metric") == "cosine"
    assert queried.iloc[0]["key"] == "k1"
    assert queried.iloc[0]["distance"] == 0.01

    print(
        json.dumps(
            {
                "bucket_arn": bucket_arn,
                "index_arn": index_arn,
                "get_vectors_rows": len(by_key.index),
                "list_vectors_rows": len(listed.index),
                "query_rows": len(queried.index),
            },
            indent=2,
            sort_keys=True,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
