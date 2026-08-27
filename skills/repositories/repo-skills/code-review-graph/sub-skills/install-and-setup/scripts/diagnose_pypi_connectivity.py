#!/usr/bin/env python3
"""Diagnose whether this Python can reach PyPI over HTTPS.

Use this only when installs fail while fetching build dependencies such as
hatchling. The check performs two explicit network probes to pypi.org and then
prints a local workaround. It never writes configuration files or installs
packages.

Examples:
  python diagnose_pypi_connectivity.py
  python diagnose_pypi_connectivity.py --timeout 10
"""

from __future__ import annotations

import argparse
import socket
import ssl
import sys
import urllib.error
import urllib.request


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--timeout",
        type=float,
        default=15.0,
        help="Network timeout in seconds for each PyPI probe (default: 15).",
    )
    args = parser.parse_args()

    ok_tls = _try_tls_pypi(args.timeout)
    ok_url = _try_urllib(args.timeout)
    if ok_tls and ok_url:
        print("PyPI check: OK (this Python can use HTTPS to pypi.org).")
        return 0
    print("PyPI check: FAILED (pip/pipx may be unable to download build deps like hatchling).")
    print("Workaround when uv is available: run `uv tool install code-review-graph --force`,")
    print("or install from a trusted local checkout with `uv tool install /path/to/checkout --force`.")
    print("If the failure is terminal-specific, retry from a normal system terminal.")
    return 1


def _try_tls_pypi(timeout: float) -> bool:
    try:
        ctx = ssl.create_default_context()
        ctx.minimum_version = ssl.TLSVersion.TLSv1_2
        with socket.create_connection(("pypi.org", 443), timeout=timeout) as sock:
            with ctx.wrap_socket(sock, server_hostname="pypi.org") as tsock:
                return bool(tsock.version())
    except OSError as exc:
        print(f"  TLS pypi.org:443 -> {exc!r}", file=sys.stderr)
        return False


def _try_urllib(timeout: float) -> bool:
    try:
        req = urllib.request.Request(
            "https://pypi.org/simple/hatchling/",
            headers={"User-Agent": "code-review-graph-diagnostic/1.0"},
        )
        with urllib.request.urlopen(req, timeout=timeout) as resp:  # noqa: S310 - explicit diagnostic URL
            resp.read(256)
        return True
    except (urllib.error.URLError, OSError) as exc:
        print(f"  urllib hatchling index -> {exc!r}", file=sys.stderr)
        return False


if __name__ == "__main__":
    raise SystemExit(main())
