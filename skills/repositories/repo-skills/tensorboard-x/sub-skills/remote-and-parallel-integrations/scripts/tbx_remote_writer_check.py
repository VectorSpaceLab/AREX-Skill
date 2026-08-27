#!/usr/bin/env python3
"""Safe dependency and mock checks for remote writer integrations."""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import tempfile
from pathlib import Path


def module_available(name: str) -> bool:
    try:
        return importlib.util.find_spec(name) is not None
    except (ImportError, ModuleNotFoundError, ValueError):
        return False


def local_fallback_smoke() -> None:
    from tensorboardX.record_writer import RecordWriter

    with tempfile.TemporaryDirectory(prefix="tbx-remote-check-") as tmpdir:
        target = Path(tmpdir) / "local" / "records.out"
        target.parent.mkdir(parents=True, exist_ok=True)
        writer = RecordWriter(str(target))
        writer.write(b"tbx-remote-check")
        writer.close()
        size = target.stat().st_size
        print(f"local fallback wrote {size} bytes to {target.name}")


def dependency_snapshot() -> None:
    from tensorboardX.comet_utils import CometLogger
    from tensorboardX.record_writer import GCS_ENABLED, REGISTERED_FACTORIES, S3_ENABLED

    snapshot = {
        "REGISTERED_FACTORIES": sorted(REGISTERED_FACTORIES),
        "S3_ENABLED": S3_ENABLED,
        "GCS_ENABLED": GCS_ENABLED,
        "boto3": module_available("boto3"),
        "google.cloud.storage": module_available("google.cloud.storage"),
        "comet_ml": module_available("comet_ml"),
        "PIL": module_available("PIL"),
        "moto": module_available("moto"),
        "nvidia_smi": module_available("nvidia_smi"),
    }
    print(json.dumps(snapshot, indent=2, sort_keys=True))

    comet_logger = CometLogger({"disabled": True})
    if comet_logger._logging is not False:
        raise SystemExit("CometLogger default disabled mode did not stay disabled")
    print("CometLogger default disabled mode: ok")


def mock_s3_smoke() -> None:
    if not module_available("boto3") or not module_available("moto"):
        print("mock S3 skipped: boto3 and/or moto unavailable")
        return

    from tensorboardX.record_writer import RecordWriter

    import boto3
    try:
        from moto import mock_s3
    except ImportError:
        print("mock S3 skipped: moto is installed but does not expose mock_s3")
        return

    os.environ.setdefault("AWS_ACCESS_KEY_ID", "tbx_mock_key")
    os.environ.setdefault("AWS_SECRET_ACCESS_KEY", "tbx_mock_secret")
    os.environ.setdefault("AWS_DEFAULT_REGION", "us-east-1")

    with mock_s3():
        client = boto3.client("s3", region_name="us-east-1")
        bucket = "tbx-remote-check"
        client.create_bucket(Bucket=bucket)

        writer = RecordWriter(f"s3://{bucket}/runs/records.out")
        writer.write(b"tbx-remote-check-s3")
        writer.close()

        response = client.get_object(Bucket=bucket, Key="runs/records.out")
        payload = response["Body"].read()
        print(f"mock S3 wrote {len(payload)} bytes to s3://{bucket}/runs/records.out")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Check remote writer dependencies and run safe local or mock checks without real cloud uploads."
    )
    parser.add_argument(
        "--check-deps",
        action="store_true",
        help="Print a dependency snapshot and Comet default-state check.",
    )
    parser.add_argument(
        "--mock-s3",
        action="store_true",
        help="Run the safe moto-backed S3 path check when boto3 and moto are available.",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    local_fallback_smoke()
    if args.check_deps:
        dependency_snapshot()
    if args.mock_s3:
        mock_s3_smoke()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
