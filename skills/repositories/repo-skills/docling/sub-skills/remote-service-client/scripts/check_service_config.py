#!/usr/bin/env python3
"""Validate Docling remote service configuration without uploading documents.

Default mode performs local-only checks: resolves flags/environment, validates URL
shape, and reports whether an API key is present. Pass --ping to make a single
GET /health request. No document content is uploaded by this script.
"""

from __future__ import annotations

import argparse
import os
import sys
from dataclasses import dataclass
from urllib.parse import urlparse, urlunparse


@dataclass(frozen=True)
class Config:
    service_url: str
    api_key: str
    timeout: float


def _load_dotenv_if_available() -> None:
    try:
        from dotenv import load_dotenv
    except ImportError:
        return
    load_dotenv(override=False)


def _normalize_base_url(raw_url: str) -> str:
    text = raw_url.strip()
    parsed = urlparse(text)
    if parsed.scheme not in {"http", "https"}:
        raise ValueError("service URL must start with http:// or https://")
    if not parsed.netloc:
        raise ValueError("service URL must include a host")
    path = parsed.path.rstrip("/")
    if path.endswith("/v1") or path == "/v1":
        raise ValueError("service URL should be the base URL, without a trailing /v1")
    if parsed.params or parsed.query or parsed.fragment:
        raise ValueError("service URL should not include params, query, or fragment")
    return urlunparse((parsed.scheme, parsed.netloc, path, "", "", ""))


def _resolve_config(args: argparse.Namespace) -> Config:
    _load_dotenv_if_available()
    service_url = args.service_url or os.environ.get("DOCLING_SERVICE_URL", "")
    api_key = args.api_key or os.environ.get("DOCLING_SERVICE_API_KEY", "")
    if not service_url.strip():
        raise ValueError(
            "missing service URL; pass --service-url or set DOCLING_SERVICE_URL"
        )
    return Config(
        service_url=_normalize_base_url(service_url),
        api_key=api_key,
        timeout=args.timeout,
    )


def _ping_health(config: Config) -> tuple[bool, str]:
    try:
        import httpx
    except ImportError:
        return False, "--ping requires httpx; install docling-slim[service-client]"

    headers = {"X-Api-Key": config.api_key} if config.api_key else {}
    health_url = f"{config.service_url}/health"
    try:
        response = httpx.get(health_url, headers=headers, timeout=config.timeout)
    except httpx.HTTPError as exc:
        return False, f"health request failed: {exc}"

    if response.status_code != 200:
        detail = response.text.strip().replace("\n", " ")[:300]
        return False, f"health returned HTTP {response.status_code}: {detail}"

    try:
        payload = response.json()
    except ValueError:
        return False, "health returned non-JSON response"

    status = payload.get("status")
    if status != "ok":
        return False, f"health returned unexpected status: {status!r}"
    return True, "health returned status=ok"


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description=(
            "Validate Docling service URL/API-key configuration. Default mode is "
            "local-only and does not contact the service."
        )
    )
    parser.add_argument(
        "--service-url",
        help="Docling service base URL; defaults to DOCLING_SERVICE_URL.",
    )
    parser.add_argument(
        "--api-key",
        help="Docling service API key; defaults to DOCLING_SERVICE_API_KEY.",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=10.0,
        help="HTTP timeout in seconds when --ping is used.",
    )
    parser.add_argument(
        "--ping",
        action="store_true",
        help="Make one GET /health request. Does not upload documents.",
    )
    return parser


def main(argv: list[str] | None = None) -> int:
    parser = _build_parser()
    args = parser.parse_args(argv)
    try:
        config = _resolve_config(args)
    except ValueError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2

    print("Docling service configuration")
    print(f"  service_url: {config.service_url}")
    print(f"  api_key: {'present' if config.api_key else 'not set'}")
    print("  default_check: no network, no document upload")

    if not args.ping:
        print("OK: local configuration checks passed")
        return 0

    ok, message = _ping_health(config)
    if ok:
        print(f"OK: {message}")
        return 0
    print(f"ERROR: {message}", file=sys.stderr)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
