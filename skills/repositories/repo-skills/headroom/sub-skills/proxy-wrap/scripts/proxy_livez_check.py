#!/usr/bin/env python3
"""Check a Headroom proxy health endpoint safely.

This helper performs only loopback/target health probes and optional stats
checks. It never sends model traffic.

Examples:
  python proxy_livez_check.py --url http://127.0.0.1:8787
  python proxy_livez_check.py --url http://127.0.0.1:8787 --stats
  python proxy_livez_check.py --url http://127.0.0.1:8787 --json
"""

from __future__ import annotations

import argparse
import json
import sys
from dataclasses import asdict, dataclass
from typing import Any


@dataclass
class ProbeReport:
    ok: bool = False
    url: str = ""
    livez_status: int | None = None
    health_status: int | None = None
    stats_status: int | None = None
    version: str | None = None
    error: str | None = None


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Probe a Headroom proxy health endpoint.")
    parser.add_argument("--url", default="http://127.0.0.1:8787", help="Base proxy URL to probe.")
    parser.add_argument("--stats", action="store_true", help="Also try the /stats endpoint.")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text.")
    return parser.parse_args(argv)


def _get(url: str) -> tuple[int | None, dict[str, Any] | None, str | None]:
    try:
        import httpx

        response = httpx.get(url, timeout=3.0)
        payload: dict[str, Any] | None = None
        try:
            payload = response.json()
        except Exception:  # noqa: BLE001
            payload = None
        return response.status_code, payload, None
    except Exception as exc:  # noqa: BLE001
        return None, None, f"{type(exc).__name__}: {exc}"


def probe(base_url: str, include_stats: bool) -> ProbeReport:
    report = ProbeReport(url=base_url.rstrip("/"))
    livez_url = f"{report.url}/livez"
    health_url = f"{report.url}/health"

    report.livez_status, livez_payload, livez_error = _get(livez_url)
    if livez_payload and isinstance(livez_payload, dict):
        report.version = str(livez_payload.get("version") or "") or None

    report.health_status, _, health_error = _get(health_url)
    if include_stats:
        stats_url = f"{report.url}/stats"
        report.stats_status, _, stats_error = _get(stats_url)
    else:
        stats_error = None

    errors = [e for e in (livez_error, health_error, stats_error) if e]
    report.ok = report.livez_status == 200 and report.health_status == 200 and not errors
    if errors:
        report.error = "; ".join(errors)
    return report


def print_text(report: ProbeReport) -> None:
    print(f"Proxy URL: {report.url}")
    print(f"/livez: {report.livez_status}")
    print(f"/health: {report.health_status}")
    if report.stats_status is not None:
        print(f"/stats: {report.stats_status}")
    if report.version:
        print(f"version: {report.version}")
    if report.error:
        print(f"error: {report.error}")
    print("ok" if report.ok else "not-ok")


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv or sys.argv[1:])
    report = probe(args.url, args.stats)
    if args.json:
        print(json.dumps(asdict(report), indent=2, sort_keys=True))
    else:
        print_text(report)
    return 0 if report.ok else 1


if __name__ == "__main__":
    raise SystemExit(main())
