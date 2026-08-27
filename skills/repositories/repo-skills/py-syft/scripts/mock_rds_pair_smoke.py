#!/usr/bin/env python3
"""Build a no-credential PySyft RDS mock-drive DO/DS pair."""
from __future__ import annotations
import argparse


def main() -> int:
    argparse.ArgumentParser(description="Build a no-credential PySyft RDS mock-drive DO/DS pair").parse_args()
    from syft_rds.client import SyftRDSClient

    ds_client, do_client = SyftRDSClient.pair_with_mock_drive_service_connection()
    print("DS", ds_client.email, ds_client.has_ds_role, type(ds_client.datasets).__name__)
    print("DO", do_client.email, do_client.has_do_role, type(do_client.jobs).__name__)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
