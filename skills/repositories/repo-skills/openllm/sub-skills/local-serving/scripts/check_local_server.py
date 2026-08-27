#!/usr/bin/env python3
"""Probe a running OpenLLM local server for readiness and OpenAI-compatible routes.

Examples:
  python check_local_server.py --base-url http://localhost:3000
  python check_local_server.py --base-url http://localhost:3000 --check-chat

This helper only performs read-only HTTP probes against a user-supplied local
server. It does not start a model or make any cloud/network requests beyond the
provided base URL.
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, asdict
from urllib.parse import urljoin

import httpx


@dataclass
class ProbeResult:
    base_url: str
    ready: bool
    ready_status: int | None
    models_status: int | None
    chat_status: int | None
    notes: list[str]


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--base-url", default="http://localhost:3000", help="Base server URL.")
    parser.add_argument("--timeout", type=float, default=3.0, help="HTTP timeout in seconds.")
    parser.add_argument(
        "--check-chat",
        action="store_true",
        help="Also probe /chat with a HEAD request when available.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Render the probe result as JSON.",
    )
    return parser


def probe(base_url: str, timeout: float, check_chat: bool) -> ProbeResult:
    notes: list[str] = []
    ready_status: int | None = None
    models_status: int | None = None
    chat_status: int | None = None

    client = httpx.Client(timeout=timeout)
    try:
        for path, target in [("/readyz", "ready_status"), ("/v1/models", "models_status")]:
            try:
                resp = client.get(urljoin(base_url.rstrip("/") + "/", path.lstrip("/")))
            except httpx.HTTPError as exc:
                notes.append(f"{path}: {exc.__class__.__name__}: {exc}")
                continue
            if target == "ready_status":
                ready_status = resp.status_code
            else:
                models_status = resp.status_code
            if resp.status_code >= 400:
                notes.append(f"{path}: HTTP {resp.status_code}")

        if check_chat:
            try:
                resp = client.head(urljoin(base_url.rstrip("/") + "/", "chat"))
            except httpx.HTTPError as exc:
                notes.append(f"/chat: {exc.__class__.__name__}: {exc}")
            else:
                chat_status = resp.status_code
                if resp.status_code >= 400:
                    notes.append(f"/chat: HTTP {resp.status_code}")
    finally:
        client.close()

    ready = ready_status == 200
    if not ready and ready_status is None:
        notes.append("readyz endpoint could not be reached")
    return ProbeResult(
        base_url=base_url,
        ready=ready,
        ready_status=ready_status,
        models_status=models_status,
        chat_status=chat_status,
        notes=notes,
    )


def main() -> int:
    args = build_parser().parse_args()
    result = probe(args.base_url, args.timeout, args.check_chat)
    if args.json:
        print(json.dumps(asdict(result), indent=2, sort_keys=False))
    else:
        print(f"base_url: {result.base_url}")
        print(f"ready: {result.ready}")
        print(f"ready_status: {result.ready_status}")
        print(f"models_status: {result.models_status}")
        print(f"chat_status: {result.chat_status}")
        if result.notes:
            print("notes:")
            for note in result.notes:
                print(f"- {note}")
    return 0 if result.ready else 2


if __name__ == "__main__":
    raise SystemExit(main())
