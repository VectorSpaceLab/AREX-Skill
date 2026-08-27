#!/usr/bin/env python3
"""Inspect or briefly serve the apod-api Flask application.

This wrapper deliberately imports ``application`` only after argument parsing.
It never performs an APOD request for --help or --inspect-routes. A live query
made by a client still depends on the external APOD website.
"""

from __future__ import annotations

import argparse
import sys
import threading
from pathlib import Path
from types import ModuleType


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Inspect routes or serve the apod-api Flask app for a bounded interval."
    )
    mode = parser.add_mutually_exclusive_group()
    mode.add_argument(
        "--inspect-routes",
        action="store_true",
        help="import the app and print its service version and routes; no APOD request",
    )
    mode.add_argument(
        "--serve",
        action="store_true",
        help="serve the app until --duration expires",
    )
    parser.add_argument("--host", help="explicit bind host (required with --serve)")
    parser.add_argument(
        "--port",
        type=int,
        help="explicit bind port 1-65535 (required with --serve)",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=30,
        help="maximum serving seconds, 1-300 (default: 30)",
    )
    return parser


def load_application() -> ModuleType:
    """Import the public application module without constructing a request."""
    # Executing a file by path puts its script directory first on sys.path.
    # Add the caller's project root so ``application.py`` is importable without
    # embedding any checkout-specific path in this bundled helper.
    project_root = str(Path.cwd())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    try:
        import application  # type: ignore[import-not-found]
    except ImportError as exc:
        raise RuntimeError(
            "cannot import application; run from the project root with runtime dependencies installed"
        ) from exc
    return application


def inspect_routes(application: ModuleType) -> None:
    app = application.app
    print(f"service_version={getattr(application, 'SERVICE_VERSION', 'unknown')}")
    for rule in sorted(app.url_map.iter_rules(), key=lambda item: item.rule):
        methods = sorted(rule.methods.difference({"HEAD", "OPTIONS"}))
        method_text = ",".join(methods) if methods else "-"
        print(f"{method_text} {rule.rule}")


def serve(application: ModuleType, host: str, port: int, duration: int) -> None:
    from werkzeug.serving import make_server

    server = make_server(host, port, application.app)
    stop_timer = threading.Timer(duration, server.shutdown)
    stop_timer.daemon = True
    stop_timer.start()
    print(f"serving http://{host}:{port} for at most {duration}s", flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("stopping on keyboard interrupt", flush=True)
    finally:
        stop_timer.cancel()
        server.server_close()
    print("service stopped", flush=True)


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if not args.inspect_routes and not args.serve:
        parser.error("choose exactly one mode: --inspect-routes or --serve")

    if args.inspect_routes:
        if args.host is not None or args.port is not None:
            parser.error("--host and --port are only valid with --serve")
        application = load_application()
        inspect_routes(application)
        return 0

    if args.host is None or args.port is None:
        parser.error("--serve requires explicit --host and --port")
    if not 1 <= args.port <= 65535:
        parser.error("--port must be between 1 and 65535")
    if not 1 <= args.duration <= 300:
        parser.error("--duration must be between 1 and 300 seconds")

    try:
        application = load_application()
        serve(application, args.host, args.port, args.duration)
    except RuntimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
