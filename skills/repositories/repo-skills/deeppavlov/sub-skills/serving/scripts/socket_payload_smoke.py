#!/usr/bin/env python3
"""Inspect a DeepPavlov socket payload frame without starting a server.

This helper is intentionally local and offline:
- it does not open sockets
- it does not contact a model server
- it does not download weights or datasets

It serializes a JSON payload with the same 4-byte little-endian header
used by DeepPavlov socket clients, checks the header, and decodes the
frame back to JSON.
"""

from __future__ import annotations

import argparse
import json
from pathlib import Path
from struct import pack, unpack

HEADER_FORMAT = "<I"

DEFAULT_PAYLOAD = {"x": ["hello"]}


def encode(data):
    bytes_data = json.dumps(data).encode("utf-8")
    return pack(HEADER_FORMAT, len(bytes_data)) + bytes_data


def load_payload(payload_json: str | None, payload_file: Path | None):
    if payload_json and payload_file:
        raise SystemExit("Provide only one of --payload-json or --payload-file.")
    if payload_file is not None:
        return json.loads(payload_file.read_text(encoding="utf-8"))
    if payload_json is not None:
        return json.loads(payload_json)
    return DEFAULT_PAYLOAD


def describe_payload(payload):
    if isinstance(payload, dict):
        return list(payload.keys())
    return type(payload).__name__


def main() -> None:
    parser = argparse.ArgumentParser(
        description="Show the DeepPavlov socket frame format for a local JSON payload."
    )
    parser.add_argument(
        "--payload-json",
        default=None,
        help="JSON string to encode. Defaults to a small generic one-argument payload.",
    )
    parser.add_argument(
        "--payload-file",
        type=Path,
        default=None,
        help="Path to a local JSON file with the payload object.",
    )
    parser.add_argument(
        "--show-hex",
        action="store_true",
        help="Print the full encoded frame as hex after the summary.",
    )
    args = parser.parse_args()

    payload = load_payload(args.payload_json, args.payload_file)
    frame = encode(payload)
    header = frame[:4]
    body = frame[4:]
    body_len = unpack("<I", header)[0]

    if body_len != len(body):
        raise SystemExit(
            f"Header/body length mismatch: header={body_len}, body={len(body)}"
        )

    decoded = json.loads(body.decode("utf-8"))

    print(f"payload_type: {type(payload).__name__}")
    print(f"payload_keys: {describe_payload(payload)}")
    print(f"header_bytes: {list(header)}")
    print(f"body_length: {body_len}")
    print("decoded_payload:")
    print(json.dumps(decoded, ensure_ascii=False, indent=2, sort_keys=True))

    if args.show_hex:
        print(f"frame_hex: {frame.hex()}")


if __name__ == "__main__":
    main()
