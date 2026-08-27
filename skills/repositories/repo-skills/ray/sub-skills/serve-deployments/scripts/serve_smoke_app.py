#!/usr/bin/env python3
"""Minimal Ray Serve app with safe default validation.

By default this script validates imports and constructs a Serve application graph
without starting Ray Serve. Pass --run-local to start a local Serve instance and
optionally issue one HTTP request. The local run mode is intended for explicit
smoke testing only.

When imported by `serve run serve_smoke_app:app`, the module exposes `app` at
module scope. When invoked as a normal CLI, imports are lazy so `--help` works
even before Ray Serve is installed.
"""

from __future__ import annotations

import argparse
import json
from typing import Any


def load_serve_modules() -> tuple[Any, Any]:
    try:
        from ray import serve
    except ImportError as exc:  # pragma: no cover - dependency message path
        raise SystemExit(
            'Ray Serve is not importable. Install it with: pip install "ray[serve]"'
        ) from exc

    try:
        from starlette.requests import Request
    except ImportError as exc:  # pragma: no cover - dependency message path
        raise SystemExit(
            'Starlette is required by Ray Serve HTTP request handling. Install "ray[serve]".'
        ) from exc

    return serve, Request


def build_app() -> Any:
    serve, Request = load_serve_modules()

    @serve.deployment(
        num_replicas=1,
        ray_actor_options={"num_cpus": 0.1},
        max_ongoing_requests=16,
    )
    class EchoDeployment:
        """Tiny class-based deployment pattern for local Serve checks."""

        def __init__(self, message: str = "Hello from Ray Serve") -> None:
            self.message = message
            self.prefix = ""

        def reconfigure(self, config: dict[str, Any]) -> None:
            self.prefix = str(config.get("prefix", ""))

        async def __call__(self, request: Request) -> dict[str, str]:
            payload = await request.json() if request.method != "GET" else {}
            message = str(payload.get("message", self.message))
            return {"result": f"{self.prefix}{message}"}

    return EchoDeployment.bind(message="Hello world!")


def validate_only() -> dict[str, Any]:
    serve_app = build_app()
    return {
        "ok": True,
        "app_type": type(serve_app).__name__,
        "deployment": "EchoDeployment",
        "starts_server": False,
    }


def run_local(route_prefix: str, request: bool) -> dict[str, Any]:
    serve, _ = load_serve_modules()
    serve_app = build_app()
    handle = serve.run(serve_app, route_prefix=route_prefix, blocking=False)
    result: dict[str, Any] = {
        "ok": True,
        "route_prefix": route_prefix,
        "handle_type": type(handle).__name__,
        "started_server": True,
    }
    if request:
        try:
            import requests
        except ImportError as exc:  # pragma: no cover - optional dependency path
            raise SystemExit("The optional HTTP request check requires the requests package.") from exc
        url = f"http://127.0.0.1:8000{route_prefix if route_prefix != '/' else '/'}"
        response = requests.post(url, json={"message": "ping"}, timeout=10)
        result["http_status"] = response.status_code
        result["http_body"] = response.json()
    return result


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Validate or explicitly run a tiny Ray Serve application."
    )
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Validate imports and app binding without starting a server (default).",
    )
    parser.add_argument(
        "--run-local",
        action="store_true",
        help="Start a local Ray Serve instance with serve.run(blocking=False).",
    )
    parser.add_argument(
        "--route-prefix",
        default="/",
        help="Route prefix to use with --run-local. Defaults to /.",
    )
    parser.add_argument(
        "--request",
        action="store_true",
        help="After --run-local, issue one local HTTP POST request to the app.",
    )
    args = parser.parse_args(argv)

    if args.run_local and args.validate_only:
        parser.error("choose either --validate-only or --run-local, not both")

    if args.run_local:
        result = run_local(args.route_prefix, args.request)
    else:
        result = validate_only()

    print(json.dumps(result, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
else:
    app = build_app()
