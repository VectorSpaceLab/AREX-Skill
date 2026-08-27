#!/usr/bin/env python3
"""Small explicit client for an already-running Marker server.

The script never starts Marker. Provide --base-url plus exactly one of --path
(server-visible filepath mode) or --file (multipart upload mode).
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
import sys
import urllib.error
import urllib.request
import uuid
from pathlib import Path
from typing import Any

OUTPUT_FORMATS = ("markdown", "json", "html", "chunks")


def endpoint(base_url: str, path: str) -> str:
    return base_url.rstrip("/") + path


def request_json(url: str, payload: dict[str, Any], timeout: float) -> tuple[int, str]:
    body = json.dumps(payload).encode("utf-8")
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json", "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - user supplies explicit URL.
        return response.status, response.read().decode("utf-8", errors="replace")


def add_form_field(parts: list[bytes], boundary: str, name: str, value: Any) -> None:
    if value is None:
        return
    parts.append(f"--{boundary}\r\n".encode("utf-8"))
    parts.append(f'Content-Disposition: form-data; name="{name}"\r\n\r\n'.encode("utf-8"))
    parts.append(str(value).encode("utf-8"))
    parts.append(b"\r\n")


def build_multipart(file_path: Path, fields: dict[str, Any]) -> tuple[bytes, str]:
    boundary = f"----marker-{uuid.uuid4().hex}"
    parts: list[bytes] = []
    for name, value in fields.items():
        add_form_field(parts, boundary, name, value)

    content_type = mimetypes.guess_type(file_path.name)[0] or "application/octet-stream"
    parts.append(f"--{boundary}\r\n".encode("utf-8"))
    parts.append(
        (
            f'Content-Disposition: form-data; name="file"; filename="{file_path.name}"\r\n'
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8")
    )
    parts.append(file_path.read_bytes())
    parts.append(b"\r\n")
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), f"multipart/form-data; boundary={boundary}"


def request_upload(url: str, file_path: Path, fields: dict[str, Any], timeout: float) -> tuple[int, str]:
    body, content_type = build_multipart(file_path, fields)
    request = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": content_type, "Accept": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:  # noqa: S310 - user supplies explicit URL.
        return response.status, response.read().decode("utf-8", errors="replace")


def print_response(status: int, text: str, save_response: str | None) -> None:
    print(f"HTTP {status}")
    try:
        parsed = json.loads(text)
    except json.JSONDecodeError:
        print(text)
        content = text
    else:
        content = json.dumps(parsed, indent=2, ensure_ascii=False)
        print(content)

    if save_response:
        Path(save_response).write_text(content + "\n", encoding="utf-8")
        print(f"saved response to {save_response}")


def bool_form(value: bool) -> str:
    return "true" if value else "false"


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Send an explicit request to an already-running Marker FastAPI server.",
        epilog=(
            "Examples:\n"
            "  python marker_server_client_template.py --base-url http://127.0.0.1:8000 --path /documents/input.pdf\n"
            "  python marker_server_client_template.py --base-url http://127.0.0.1:8000 --file ./input.pdf --output-format html"
        ),
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument("--base-url", required=True, help="Base URL of an already-running Marker server.")
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--path", help="File path visible to the server process; sends POST /marker JSON.")
    mode.add_argument("--file", help="Local file to upload; sends POST /marker/upload multipart form data.")
    parser.add_argument("--page-range", help="Optional page range such as 0,5-10,20.")
    parser.add_argument("--force-ocr", action="store_true", help="Force OCR on all pages.")
    parser.add_argument("--paginate-output", action="store_true", help="Request page separators in output.")
    parser.add_argument("--output-format", choices=OUTPUT_FORMATS, default="markdown", help="Output format.")
    parser.add_argument("--timeout", type=float, default=120.0, help="Request timeout in seconds; default: 120.")
    parser.add_argument("--dry-run", action="store_true", help="Print request details without contacting the server.")
    parser.add_argument("--save-response", help="Optional path to write the JSON/text response.")
    args = parser.parse_args(argv)

    common = {
        "page_range": args.page_range,
        "force_ocr": args.force_ocr,
        "paginate_output": args.paginate_output,
        "output_format": args.output_format,
    }

    try:
        if args.path:
            url = endpoint(args.base_url, "/marker")
            payload = {"filepath": args.path, **common}
            if args.dry_run:
                print(json.dumps({"method": "POST", "url": url, "json": payload}, indent=2))
                return 0
            status, text = request_json(url, payload, args.timeout)
        else:
            file_path = Path(os.path.expanduser(args.file)).resolve()
            if not file_path.is_file():
                print(f"File does not exist: {file_path}", file=sys.stderr)
                return 2
            url = endpoint(args.base_url, "/marker/upload")
            fields = {
                "page_range": args.page_range,
                "force_ocr": bool_form(args.force_ocr),
                "paginate_output": bool_form(args.paginate_output),
                "output_format": args.output_format,
            }
            if args.dry_run:
                printable_fields = {name: value for name, value in fields.items() if value is not None}
                print(json.dumps({"method": "POST", "url": url, "multipart_fields": printable_fields, "file": str(file_path)}, indent=2))
                return 0
            status, text = request_upload(url, file_path, fields, args.timeout)
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        print_response(exc.code, body, args.save_response)
        return 1
    except urllib.error.URLError as exc:
        print(f"Request failed: {exc}", file=sys.stderr)
        return 1

    print_response(status, text, args.save_response)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
