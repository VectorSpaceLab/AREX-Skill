#!/usr/bin/env python3
"""Minimal speech-to-speech Realtime WebSocket endpoint probe.

The probe checks only the protocol handshake and an optional session.update
acknowledgement. It sends no audio, starts no model, and avoids printing
credentials or payload contents.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from typing import Any
from urllib.parse import urlparse, urlunparse

try:
    import websockets
except ImportError as exc:  # pragma: no cover - user environment issue
    raise SystemExit("Install websockets to use this probe: pip install websockets") from exc


def normalize_url(url: str) -> str:
    parsed = urlparse(url)
    if parsed.query or parsed.fragment:
        raise ValueError("Realtime URL must not contain a query string or fragment")
    if not parsed.scheme:
        parsed = urlparse("ws://" + url)
    if parsed.scheme in {"http", "https"}:
        scheme = "wss" if parsed.scheme == "https" else "ws"
    elif parsed.scheme in {"ws", "wss"}:
        scheme = parsed.scheme
    else:
        raise ValueError("Realtime URL scheme must be ws, wss, http, or https")
    path = parsed.path.rstrip("/")
    if not path.endswith("/v1/realtime"):
        path = path + "/v1/realtime" if path else "/v1/realtime"
    return urlunparse((scheme, parsed.netloc, path, "", "", ""))


def compact_event(event: dict[str, Any]) -> str:
    event_type = event.get("type", "<missing-type>")
    if event_type == "error":
        err = event.get("error") or {}
        code = err.get("code") or err.get("type") or "error"
        message = err.get("message") or ""
        return f"error:{code}:{message[:160]}"
    if event_type in {"session.created", "session.updated"}:
        session = event.get("session") or {}
        return f"{event_type}:id={session.get('id', '<unknown>')}"
    return str(event_type)


async def _connect(url: str, api_key: str | None):
    headers = None
    if api_key:
        headers = {"Authorization": f"Bearer {api_key}"}
    try:
        return await websockets.connect(url, additional_headers=headers, open_timeout=10)
    except TypeError:
        # websockets < 14 used extra_headers.
        return await websockets.connect(url, extra_headers=headers, open_timeout=10)


async def run(args: argparse.Namespace) -> int:
    url = normalize_url(args.url)
    async with await _connect(url, args.api_key) as ws:
        first = json.loads(await asyncio.wait_for(ws.recv(), timeout=args.timeout))
        print(compact_event(first))
        if first.get("type") != "session.created":
            return 2

        if args.send_session_update:
            update: dict[str, Any] = {
                "type": "session.update",
                "session": {
                    "instructions": args.instructions,
                    "output_modalities": ["text", "audio"],
                },
            }
            if args.voice:
                update["session"]["audio"] = {"output": {"voice": args.voice}}
            await ws.send(json.dumps(update))
            ack = json.loads(await asyncio.wait_for(ws.recv(), timeout=args.timeout))
            print(compact_event(ack))
            if ack.get("type") != "session.updated":
                return 3
    print(f"Realtime endpoint probe passed for {url}")
    return 0


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="ws://127.0.0.1:8765/v1/realtime", help="Realtime endpoint URL")
    parser.add_argument("--api-key", default=None, help="Optional bearer token; never printed")
    parser.add_argument("--timeout", type=float, default=10.0, help="Seconds to wait for each server event")
    parser.add_argument("--send-session-update", action="store_true", help="Also send a minimal session.update")
    parser.add_argument("--instructions", default="You are a concise voice assistant.", help="Instructions for the optional session.update")
    parser.add_argument("--voice", default=None, help="Optional output voice for the optional session.update")
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    try:
        args = parse_args(argv)
        return asyncio.run(run(args))
    except Exception as exc:  # pragma: no cover - command-line diagnostics
        print(f"Realtime endpoint probe failed: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
