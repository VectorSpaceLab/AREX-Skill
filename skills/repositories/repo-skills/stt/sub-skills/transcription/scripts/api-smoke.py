#!/usr/bin/env python3
"""Smoke-test STT transcription HTTP endpoints with an explicit input file."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from urllib.parse import urljoin

import requests


def endpoint_url(base_url: str, endpoint: str) -> str:
    base = base_url.rstrip("/") + "/"
    if endpoint in {"legacy", "/api"}:
        return urljoin(base, "api")
    if endpoint in {"openai", "/v1/audio/transcriptions"}:
        return urljoin(base, "v1/audio/transcriptions")
    raise ValueError(endpoint)


def print_response(response: requests.Response) -> int:
    content_type = response.headers.get("content-type", "")
    if "json" in content_type.lower():
        try:
            payload = response.json()
        except Exception:
            print(response.text)
            return 1 if response.status_code >= 400 else 0
        print(json.dumps(payload, ensure_ascii=False, indent=2))
        if isinstance(payload, dict) and payload.get("code", 0) not in (0, None):
            return 2
        return 1 if response.status_code >= 400 else 0
    print(response.text)
    return 1 if response.status_code >= 400 else 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Send a file to an STT transcription endpoint.")
    parser.add_argument("--endpoint", choices=["legacy", "openai", "/api", "/v1/audio/transcriptions"], default="legacy", help="Endpoint family or path to call.")
    parser.add_argument("--base-url", default="http://127.0.0.1:9977", help="Base server URL.")
    parser.add_argument("--file", required=True, help="Audio/video file to upload.")
    parser.add_argument("--model", default="tiny", help="Model name to request.")
    parser.add_argument("--language", default="auto", help="Language code or auto.")
    parser.add_argument("--response-format", choices=["text", "json", "srt"], default="json", help="Requested response format.")
    parser.add_argument("--prompt", default=None, help="Optional initial prompt for the OpenAI-compatible endpoint.")
    parser.add_argument("--timeout", type=float, default=600.0, help="HTTP request timeout in seconds.")
    args = parser.parse_args()

    media_path = Path(args.file).expanduser().resolve()
    if not media_path.is_file():
        print(f"error: file does not exist: {media_path}", file=sys.stderr)
        return 1

    url = endpoint_url(args.base_url, args.endpoint)
    data = {
        "model": args.model,
        "language": args.language,
        "response_format": args.response_format,
    }
    if args.endpoint in {"openai", "/v1/audio/transcriptions"} and args.prompt:
        data["prompt"] = args.prompt

    print(f"POST {url}")
    print(f"file={media_path.name} model={args.model} language={args.language} response_format={args.response_format}")

    with media_path.open("rb") as handle:
        files = {"file": (media_path.name, handle)}
        try:
            response = requests.post(url, data=data, files=files, timeout=args.timeout)
        except requests.RequestException as exc:
            print(f"request failed: {exc}", file=sys.stderr)
            return 1

    print(f"HTTP {response.status_code}")
    return print_response(response)


if __name__ == "__main__":
    raise SystemExit(main())
