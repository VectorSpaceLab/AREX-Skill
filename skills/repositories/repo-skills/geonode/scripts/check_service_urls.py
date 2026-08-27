#!/usr/bin/env python3
"""Non-credentialed GeoNode service readiness probe.

Checks explicit HTTP(S) URLs and/or host:port pairs. It never sends
credentials, changes state, follows arbitrary redirects, or treats a failed
probe as permission to mutate a deployment.
"""

from __future__ import annotations

import argparse
import socket
import sys
import urllib.error
import urllib.request
from dataclasses import dataclass
from urllib.parse import urlparse


@dataclass
class Result:
    target: str
    ok: bool
    detail: str


def check_url(target: str, timeout: float) -> Result:
    parsed = urlparse(target)
    if parsed.scheme not in {"http", "https"} or not parsed.netloc:
        return Result(target, False, "expected an explicit http(s) URL")
    request = urllib.request.Request(target, method="GET", headers={"User-Agent": "geonode-skill-probe/1"})
    try:
        with urllib.request.urlopen(request, timeout=timeout) as response:
            return Result(target, 200 <= response.status < 500, f"HTTP {response.status}")
    except urllib.error.HTTPError as exc:
        # An HTTP response proves reachability even when authentication is required.
        return Result(target, True, f"HTTP {exc.code} (reachable; auth/policy may still block it)")
    except (urllib.error.URLError, TimeoutError, OSError) as exc:
        return Result(target, False, f"unreachable: {exc.reason if hasattr(exc, 'reason') else exc}")


def parse_host_port(target: str) -> tuple[str, int] | None:
    if ":" not in target or target.startswith("["):
        return None
    host, port = target.rsplit(":", 1)
    try:
        parsed_port = int(port)
    except ValueError:
        return None
    return host, parsed_port


def check_tcp(target: str, timeout: float) -> Result:
    parsed = parse_host_port(target)
    if parsed is None:
        return Result(target, False, "expected HOST:PORT")
    host, port = parsed
    try:
        with socket.create_connection((host, port), timeout=timeout):
            return Result(target, True, "TCP connection succeeded")
    except (OSError, TimeoutError) as exc:
        return Result(target, False, f"connection failed: {exc}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("targets", nargs="+", help="explicit http(s) URLs or HOST:PORT values")
    parser.add_argument("--timeout", type=float, default=5.0, help="per-target timeout in seconds (default: 5)")
    parser.add_argument("--tcp", action="store_true", help="treat all targets as HOST:PORT instead of URLs")
    args = parser.parse_args(argv)
    if args.timeout <= 0:
        parser.error("--timeout must be positive")
    checker = check_tcp if args.tcp else check_url
    results = [checker(target, args.timeout) for target in args.targets]
    for result in results:
        print(f"{'OK' if result.ok else 'FAIL'}\t{result.target}\t{result.detail}")
    return 0 if all(result.ok for result in results) else 1


if __name__ == "__main__":
    sys.exit(main())
