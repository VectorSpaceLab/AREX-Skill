#!/usr/bin/env python3
"""Check one already-running, loopback-only GIMP-ML service.

This helper performs a single GET /status. It never starts or stops a process,
imports an application module, reads configuration files, follows redirects,
uses environment proxies, contacts a non-loopback host, or changes files.
"""

from __future__ import annotations

import argparse
import ipaddress
import json
import sys
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.request import HTTPRedirectHandler, ProxyHandler, Request, build_opener


MAX_RESPONSE_BYTES = 1024 * 1024


class NoRedirect(HTTPRedirectHandler):
    """Keep a loopback check from following a response to another endpoint."""

    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None


def parse_port(value: str) -> int:
    try:
        port = int(value, 10)
    except ValueError as exc:
        raise argparse.ArgumentTypeError("port must be an integer") from exc
    if not 1 <= port <= 65535:
        raise argparse.ArgumentTypeError("port must be between 1 and 65535")
    return port


def loopback_host(value: str) -> str:
    host = value.strip()
    if host.lower() == "localhost":
        return host
    try:
        address = ipaddress.ip_address(host)
    except ValueError as exc:
        raise argparse.ArgumentTypeError(
            "host must be localhost, 127.0.0.1, or ::1"
        ) from exc
    if not address.is_loopback:
        raise argparse.ArgumentTypeError("host must be loopback-only")
    return host


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Perform one safe GET /status against an already-running "
            "loopback service; never starts or configures a process."
        )
    )
    parser.add_argument(
        "--port",
        required=True,
        type=parse_port,
        metavar="PORT",
        help="active operator-provided loopback port",
    )
    parser.add_argument(
        "--host",
        default="127.0.0.1",
        type=loopback_host,
        metavar="HOST",
        help="loopback host only (default: 127.0.0.1)",
    )
    parser.add_argument(
        "--timeout",
        type=float,
        default=5.0,
        metavar="SECONDS",
        help="GET timeout from 0.1 to 10 seconds (default: 5)",
    )
    return parser.parse_args()


def url_for(host: str, port: int) -> str:
    display_host = f"[{host}]" if ":" in host else host
    return f"http://{display_host}:{port}/status"


def read_status(url: str, timeout: float) -> Any:
    request = Request(url, method="GET", headers={"Accept": "application/json"})
    # Do not send the local health check through a proxy configured in the
    # calling environment.
    opener = build_opener(ProxyHandler({}), NoRedirect())
    with opener.open(request, timeout=timeout) as response:
        body = response.read(MAX_RESPONSE_BYTES + 1)
    if len(body) > MAX_RESPONSE_BYTES:
        raise ValueError("response exceeded the 1 MiB diagnostic limit")
    return json.loads(body.decode("utf-8"))


def main() -> int:
    args = parse_args()
    if not 0.1 <= args.timeout <= 10:
        print("ERROR timeout must be between 0.1 and 10 seconds", file=sys.stderr)
        return 2

    url = url_for(args.host, args.port)
    print(f"GET {url} (loopback-only; no process start)" )
    try:
        payload = read_status(url, args.timeout)
    except HTTPError as exc:
        print(f"ERROR HTTP {exc.code} from /status", file=sys.stderr)
        return 1
    except (OSError, URLError, TimeoutError, ValueError, UnicodeError) as exc:
        print(f"ERROR status check failed: {exc}", file=sys.stderr)
        return 1

    if not isinstance(payload, dict):
        print("ERROR /status response is not a JSON object", file=sys.stderr)
        return 1
    if payload.get("service") != "running":
        print("ERROR /status did not report service=running", file=sys.stderr)
        print(json.dumps(payload, sort_keys=True))
        return 1

    print("OK service=running")
    print(json.dumps(payload, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
