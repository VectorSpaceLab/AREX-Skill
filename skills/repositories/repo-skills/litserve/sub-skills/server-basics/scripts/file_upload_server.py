#!/usr/bin/env python3
"""LitServe file-upload and form-data example.

Run:
    python file_upload_server.py --host 127.0.0.1 --port 8000 --max-payload-size 10485760

Multipart file request:
    printf 'hello litserve' > sample.txt
    curl -X POST http://127.0.0.1:8000/predict -F 'input=@sample.txt'

URL-encoded form request:
    curl -X POST http://127.0.0.1:8000/predict \
      -H 'Content-Type: application/x-www-form-urlencoded' \
      -d 'input=hello+form'
"""

from __future__ import annotations

import argparse
from collections.abc import Mapping
from typing import Any

from fastapi import Request

import litserve as ls


class FileOrFormAPI(ls.LitAPI):
    """Accept multipart files, URL-encoded forms, or simple JSON text payloads."""

    def __init__(self, api_path: str) -> None:
        super().__init__(api_path=api_path)

    def setup(self, device):
        self.device = str(device)

    def decode_request(self, request: Request):
        if not isinstance(request, Mapping):
            raise ValueError("Expected a parsed JSON, form, or multipart mapping.")

        item: Any
        field_name = "input"
        if "input" in request:
            item = request["input"]
        elif "file" in request:
            field_name = "file"
            item = request["file"]
        elif "text" in request:
            field_name = "text"
            item = request["text"]
        else:
            raise ValueError("Expected one of the fields: input, file, or text.")

        filename = getattr(item, "filename", None)
        if hasattr(item, "file"):
            raw = item.file.read()
        elif isinstance(item, bytes):
            raw = item
        else:
            raw = str(item).encode("utf-8")

        text = raw.decode("utf-8", errors="replace")
        return {
            "field": field_name,
            "filename": filename,
            "size_bytes": len(raw),
            "text": text,
        }

    def predict(self, payload):
        text = payload["text"]
        words = [word for word in text.split() if word]
        return {
            **payload,
            "characters": len(text),
            "words": len(words),
            "uppercase_preview": text[:120].upper(),
        }

    def encode_response(self, output):
        return {"device": self.device, **output}


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Run a LitServe file/form upload example server.")
    parser.add_argument("--host", default="127.0.0.1", choices=["127.0.0.1", "0.0.0.0", "::"])
    parser.add_argument("--port", default=8000, type=int)
    parser.add_argument("--api-path", default="/predict", help="POST endpoint path; must start with '/'.")
    parser.add_argument("--max-payload-size", default=None, type=int, help="Optional byte limit for request bodies.")
    parser.add_argument("--workers-per-device", default=1, type=int)
    parser.add_argument("--timeout", default=30.0, type=float)
    parser.add_argument(
        "--generate-client",
        action="store_true",
        help="Write client.py in the current working directory if it does not already exist.",
    )
    return parser


def main() -> None:
    args = build_parser().parse_args()
    server = ls.LitServer(
        FileOrFormAPI(api_path=args.api_path),
        accelerator="cpu",
        devices=1,
        workers_per_device=args.workers_per_device,
        timeout=args.timeout,
        max_payload_size=args.max_payload_size,
        model_metadata={"name": "file-or-form-example", "kind": "payload-demo"},
    )
    server.run(
        host=args.host,
        port=args.port,
        generate_client_file=args.generate_client,
    )


if __name__ == "__main__":
    main()
