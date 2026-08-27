#!/usr/bin/env python3
"""Minimal ASRT HTTP client without importing ASRT.

This client uses only Python standard-library modules. It reads WAV files with
wave, encodes raw sample frames as URL-safe base64 JSON text, and sends requests
with urllib.
"""

from __future__ import annotations

import argparse
import base64
import json
import sys
import time
import urllib.error
import urllib.request
import wave
from pathlib import Path
from typing import Any, Dict, Iterable, List, Tuple

AUDIO_COMMANDS = {"speech": "/speech", "all": "/all"}
LANGUAGE_COMMANDS = {"language": "/language"}
ROOT_POST_COMMANDS = {"post-root": "/"}
GET_COMMANDS = {"health": "/"}


def read_wav_payload(path: Path) -> Dict[str, Any]:
    """Read raw sample-frame bytes and header metadata from a WAV file."""
    try:
        with wave.open(str(path), "rb") as wav_file:
            frames = wav_file.readframes(wav_file.getnframes())
            sample_rate = wav_file.getframerate()
            channels = wav_file.getnchannels()
            byte_width = wav_file.getsampwidth()
    except wave.Error as exc:
        raise SystemExit(f"error: {path} is not a readable WAV file: {exc}") from exc
    except OSError as exc:
        raise SystemExit(f"error: cannot read {path}: {exc}") from exc

    return {
        "samples": base64.urlsafe_b64encode(frames).decode("ascii"),
        "sample_rate": sample_rate,
        "channels": channels,
        "byte_width": byte_width,
    }


def normalize_pinyins(values: Iterable[str] | None) -> List[str]:
    if values is None:
        return []
    pinyins: List[str] = []
    for value in values:
        for item in value.split(","):
            item = item.strip()
            if item:
                pinyins.append(item)
    return pinyins


def join_url(base_url: str, endpoint: str) -> str:
    return base_url.rstrip("/") + endpoint


def build_payload(args: argparse.Namespace) -> Tuple[str, Dict[str, Any] | None]:
    command = args.command
    if command in GET_COMMANDS:
        return GET_COMMANDS[command], None
    if command in ROOT_POST_COMMANDS:
        return ROOT_POST_COMMANDS[command], {}
    if command in AUDIO_COMMANDS:
        if args.wav is None:
            raise SystemExit(f"error: --wav is required for {command}")
        return AUDIO_COMMANDS[command], read_wav_payload(args.wav)
    if command in LANGUAGE_COMMANDS:
        pinyins = normalize_pinyins(args.sequence_pinyin)
        if not pinyins:
            raise SystemExit("error: --sequence-pinyin is required for language")
        return LANGUAGE_COMMANDS[command], {"sequence_pinyin": pinyins}
    raise SystemExit(f"error: unsupported command {command!r}")


def request_asrt(
    base_url: str,
    endpoint: str,
    payload: Dict[str, Any] | None,
    timeout: float,
) -> Tuple[int, Dict[str, str], bytes, float]:
    url = join_url(base_url, endpoint)
    headers = {"Accept": "application/json, text/html;q=0.8"}
    data = None
    method = "GET"
    if payload is not None:
        data = json.dumps(payload, ensure_ascii=False).encode("utf-8")
        headers["Content-Type"] = "application/json"
        method = "POST"

    request = urllib.request.Request(url=url, data=data, headers=headers, method=method)
    started = time.time()
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            body = response.read()
            elapsed = time.time() - started
            return response.getcode(), dict(response.headers.items()), body, elapsed
    except urllib.error.HTTPError as exc:
        body = exc.read()
        elapsed = time.time() - started
        return exc.code, dict(exc.headers.items()), body, elapsed
    except urllib.error.URLError as exc:
        raise SystemExit(f"error: request to {url} failed: {exc}") from exc


def decode_body(body: bytes, encoding: str = "utf-8") -> Any:
    text = body.decode(encoding, errors="replace")
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        return text


def make_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Call ASRT HTTP endpoints using JSON payloads built without ASRT imports.",
        formatter_class=argparse.ArgumentDefaultsHelpFormatter,
    )
    parser.add_argument(
        "command",
        choices=["health", "post-root", "speech", "language", "all"],
        help="Endpoint to call: health=GET /, post-root=POST /, speech=POST /speech, language=POST /language, all=POST /all.",
    )
    parser.add_argument(
        "--base-url",
        default="http://127.0.0.1:20001",
        help="ASRT HTTP service base URL.",
    )
    parser.add_argument(
        "--wav",
        type=Path,
        help="WAV file for speech/all. Raw sample frames are encoded, not the WAV container.",
    )
    parser.add_argument(
        "--sequence-pinyin",
        nargs="*",
        metavar="PINYIN",
        help="Pinyin syllables for language. Values may also contain comma-separated syllables.",
    )
    parser.add_argument("--timeout", type=float, default=30.0, help="Request timeout in seconds.")
    parser.add_argument("--pretty", action="store_true", help="Pretty-print the response wrapper.")
    parser.add_argument(
        "--show-request",
        action="store_true",
        help="Include endpoint and JSON payload metadata in the printed output.",
    )
    return parser


def main(argv: List[str] | None = None) -> int:
    parser = make_parser()
    args = parser.parse_args(argv)
    endpoint, payload = build_payload(args)
    status, headers, body, elapsed = request_asrt(args.base_url, endpoint, payload, args.timeout)
    content_type = headers.get("Content-Type") or headers.get("content-type") or ""
    encoding = "utf-8"
    if "charset=" in content_type:
        encoding = content_type.rsplit("charset=", 1)[-1].split(";", 1)[0].strip() or "utf-8"

    output: Dict[str, Any] = {
        "http_status": status,
        "elapsed_seconds": elapsed,
        "content_type": content_type,
        "body": decode_body(body, encoding=encoding),
    }
    if args.show_request:
        output["request"] = {
            "url": join_url(args.base_url, endpoint),
            "method": "GET" if payload is None else "POST",
            "payload_fields": sorted(payload.keys()) if payload else [],
        }

    indent = 2 if args.pretty else None
    sys.stdout.write(json.dumps(output, ensure_ascii=False, indent=indent))
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
