#!/usr/bin/env python3
from __future__ import annotations
import argparse


def b(value: bool) -> str:
    return "true" if value else "false"


def main() -> int:
    parser = argparse.ArgumentParser(description="Render SYFT_ENCLAVE_* environment lines")
    parser.add_argument("--email", required=True)
    parser.add_argument("--data-owner", action="append", required=True)
    parser.add_argument("--token-path", default="/run/syft-enclave/token.json")
    parser.add_argument("--poll-interval", type=int, default=1)
    parser.add_argument("--require-tee", action="store_true")
    parser.add_argument("--log-level", default="INFO", choices=["DEBUG", "INFO", "WARNING", "ERROR"])
    parser.add_argument("--fresh-state", action=argparse.BooleanOptionalAction, default=True)
    parser.add_argument("--use-encryption", action=argparse.BooleanOptionalAction, default=True)
    args = parser.parse_args()
    lines = {
        "SYFT_ENCLAVE_EMAIL": args.email,
        "SYFT_ENCLAVE_DATA_OWNERS": ",".join(args.data_owner),
        "SYFT_ENCLAVE_TOKEN_PATH": args.token_path,
        "SYFT_ENCLAVE_POLL_INTERVAL": str(args.poll_interval),
        "SYFT_ENCLAVE_REQUIRE_TEE": b(args.require_tee),
        "SYFT_ENCLAVE_LOG_LEVEL": args.log_level,
        "SYFT_ENCLAVE_FRESH_STATE": b(args.fresh_state),
        "SYFT_ENCLAVE_USE_ENCRYPTION": b(args.use_encryption),
    }
    for key, value in lines.items():
        print(f"{key}={value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
