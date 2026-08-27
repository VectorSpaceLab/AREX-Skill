#!/usr/bin/env python3
"""Emit a tiny Agent Lightning metrics stream to console and Prometheus.

This is adapted from the repository's minimal metrics example but exits quickly
and avoids external dependencies beyond prometheus-client and agentlightning.

Examples:
    python scripts/check_prometheus_metrics.py --help
    python scripts/check_prometheus_metrics.py --duration 1 --host 127.0.0.1
"""

from __future__ import annotations

import argparse
import asyncio
import random
import sys
import time


async def _emit_metrics(backend, duration: float) -> None:
    operations = ["search", "summary", "answer"]
    statuses = ["200", "404", "500"]
    end_time = time.time() + duration
    random.seed(1337)
    while time.time() < end_time:
        operation = random.choice(operations)
        status = random.choices(statuses, weights=[0.9, 0.05, 0.05], k=1)[0]
        latency = random.lognormvariate(-4.0, 0.5)
        await backend.inc_counter("agentlightning_skill_requests_total", labels={"operation": operation, "status": status})
        await backend.observe_histogram("agentlightning_skill_latency_seconds", value=latency, labels={"operation": operation})
        await asyncio.sleep(0.2)


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a short local Agent Lightning metrics smoke test.")
    parser.add_argument("--duration", type=float, default=1.0, help="Seconds to emit metrics before exiting.")
    parser.add_argument("--host", default="127.0.0.1", help="Host/IP for the /metrics endpoint.")
    parser.add_argument("--port", type=int, default=9105, help="Port for the /metrics endpoint.")
    parser.add_argument("--no-http", action="store_true", help="Do not start an HTTP metrics endpoint; console backend only.")
    args = parser.parse_args()

    try:
        import agentlightning as agl
        from agentlightning.utils.metrics import ConsoleMetricsBackend, MultiMetricsBackend, PrometheusMetricsBackend
    except Exception as exc:
        print(f"FAIL importing agentlightning metrics helpers: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    try:
        from prometheus_client import start_http_server
    except Exception as exc:
        if args.no_http:
            start_http_server = None
        else:
            print(f"FAIL prometheus-client is required unless --no-http is used: {type(exc).__name__}: {exc}", file=sys.stderr)
            return 1

    agl.setup_logging("WARNING")
    console_backend = ConsoleMetricsBackend(window_seconds=5.0, log_interval_seconds=1.0, group_level=2)
    if args.no_http:
        backend = console_backend
    else:
        assert start_http_server is not None
        start_http_server(args.port, addr=args.host)
        prom_backend = PrometheusMetricsBackend()
        backend = MultiMetricsBackend([console_backend, prom_backend])
        print(f"metrics endpoint: http://{args.host}:{args.port}/metrics")

    backend.register_counter("agentlightning_skill_requests_total", ["operation", "status"])
    backend.register_histogram(
        "agentlightning_skill_latency_seconds",
        ["operation"],
        buckets=[0.01, 0.05, 0.1, 0.2, 0.5, 1.0],
    )

    try:
        asyncio.run(_emit_metrics(backend, duration=args.duration))
    except OSError as exc:
        print(f"FAIL metrics server error: {exc}", file=sys.stderr)
        return 1
    print(f"PASS emitted metrics for {args.duration:.2f}s")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
