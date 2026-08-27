#!/usr/bin/env python3
"""Cross-platform smoke helper for the FunASR OpenAI-compatible API.

The helper always checks /health and /v1/models. If --audio-path is supplied,
it also posts that local file to /v1/audio/transcriptions.
"""

from __future__ import annotations

import argparse
import json
import mimetypes
import os
from pathlib import Path
import sys
import urllib.error
import urllib.request
import uuid


def request_json(url: str, timeout: float) -> object:
    request = urllib.request.Request(url, headers={"Accept": "application/json"})
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def build_multipart_body(audio_path: Path, model: str, response_format: str) -> tuple[bytes, str]:
    boundary = f"----funasr-smoke-{uuid.uuid4().hex}"
    content_type = mimetypes.guess_type(str(audio_path))[0] or "application/octet-stream"
    parts: list[bytes] = []

    def add_text(name: str, value: str) -> None:
        parts.append(
            (
                f"--{boundary}\r\n"
                f"Content-Disposition: form-data; name=\"{name}\"\r\n\r\n"
                f"{value}\r\n"
            ).encode("utf-8")
        )

    parts.append(
        (
            f"--{boundary}\r\n"
            f"Content-Disposition: form-data; name=\"file\"; filename=\"{audio_path.name}\"\r\n"
            f"Content-Type: {content_type}\r\n\r\n"
        ).encode("utf-8")
    )
    parts.append(audio_path.read_bytes())
    parts.append(b"\r\n")
    add_text("model", model)
    add_text("response_format", response_format)
    parts.append(f"--{boundary}--\r\n".encode("utf-8"))
    return b"".join(parts), boundary


def transcribe(base_url: str, audio_path: Path, model: str, response_format: str, timeout: float) -> object:
    body, boundary = build_multipart_body(audio_path, model, response_format)
    request = urllib.request.Request(
        f"{base_url}/v1/audio/transcriptions",
        data=body,
        method="POST",
        headers={
            "Accept": "application/json",
            "Content-Type": f"multipart/form-data; boundary={boundary}",
            "Content-Length": str(len(body)),
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return json.loads(response.read().decode("utf-8"))


def print_payload(title: str, payload: object) -> None:
    print(f"\n== {title} ==")
    if isinstance(payload, str):
        print(payload)
    else:
        print(json.dumps(payload, ensure_ascii=False, indent=2))


def main() -> int:
    parser = argparse.ArgumentParser(description="Smoke test the FunASR OpenAI-compatible API")
    parser.add_argument(
        "--base-url",
        default=os.getenv("BASE_URL", "http://localhost:8000"),
        help="FunASR API base URL",
    )
    parser.add_argument(
        "--model",
        default=os.getenv("MODEL", "sensevoice"),
        help="Model alias to use for the optional transcription request",
    )
    parser.add_argument(
        "--response-format",
        default=os.getenv("RESPONSE_FORMAT", "verbose_json"),
        choices=["json", "verbose_json", "text"],
        help="Transcription response format",
    )
    parser.add_argument(
        "--audio-path",
        default=os.getenv("AUDIO_PATH"),
        help="Optional local audio file to transcribe after the health checks",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=float(os.getenv("TIMEOUT", "120")),
        help="HTTP timeout in seconds",
    )
    args = parser.parse_args()

    base_url = args.base_url.rstrip("/")

    try:
        print_payload("health", request_json(f"{base_url}/health", args.timeout))
        print_payload("models", request_json(f"{base_url}/v1/models", args.timeout))

        if args.audio_path:
            audio_path = Path(args.audio_path).expanduser()
            if not audio_path.is_file():
                raise FileNotFoundError(f"audio file not found: {audio_path}")
            print(
                f"\nTranscribing {audio_path} with model={args.model}, "
                f"response_format={args.response_format}"
            )
            print_payload(
                "transcription",
                transcribe(base_url, audio_path, args.model, args.response_format, args.timeout),
            )
        else:
            print("\nNo --audio-path supplied; skipped the transcription POST.")
    except urllib.error.HTTPError as error:
        detail = error.read().decode("utf-8", errors="replace")
        print(f"HTTP {error.code} from {error.url}: {detail}", file=sys.stderr)
        return 1
    except Exception as error:
        print(f"Smoke test failed: {error}", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
