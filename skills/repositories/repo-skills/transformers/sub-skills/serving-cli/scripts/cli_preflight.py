#!/usr/bin/env python3
"""Dry-run preflight checks for Transformers CLI serving workflows.

The script imports CLI modules and optional client/server packages, validates common
serving flag combinations, and can probe an already-running health endpoint. It does
not download models, load weights, bind a port, or start a server.
"""

from __future__ import annotations

import argparse
import importlib
import json
import socket
import sys
from dataclasses import dataclass
from urllib.error import URLError
from urllib.request import Request, urlopen


BASE_MODULES = [
    "transformers",
    "transformers.cli.transformers",
    "transformers.cli.download",
    "transformers.cli.chat",
    "transformers.cli.serve",
]

CLIENT_PACKAGES = ["requests", "httpx", "typer", "huggingface_hub", "rich"]
SERVING_PACKAGES = ["fastapi", "uvicorn", "pydantic", "openai"]
OPTIONAL_BACKENDS = ["torch", "librosa", "multipart"]


@dataclass
class CheckResult:
    name: str
    ok: bool
    detail: str
    required: bool = False


def import_check(name: str, required: bool = False) -> CheckResult:
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - preflight should report import failures clearly.
        return CheckResult(name=name, ok=False, detail=f"{type(exc).__name__}: {exc}", required=required)
    version = getattr(module, "__version__", None)
    return CheckResult(name=name, ok=True, detail=f"version={version}" if version else "imported", required=required)


def port_available(host: str, port: int) -> CheckResult:
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    try:
        sock.settimeout(1.0)
        sock.bind((host, port))
    except OSError as exc:
        return CheckResult(name=f"port {host}:{port}", ok=False, detail=str(exc), required=False)
    finally:
        sock.close()
    return CheckResult(name=f"port {host}:{port}", ok=True, detail="available", required=False)


def probe_health(base_url: str, timeout: float) -> CheckResult:
    url = base_url.rstrip("/") + "/health"
    request = Request(url, method="GET")
    try:
        with urlopen(request, timeout=timeout) as response:  # noqa: S310 - user-provided local preflight URL.
            body = response.read(200).decode("utf-8", errors="replace")
            return CheckResult(name="health", ok=200 <= response.status < 300, detail=f"{response.status} {body}")
    except (OSError, URLError) as exc:
        return CheckResult(name="health", ok=False, detail=str(exc), required=False)


def validate_args(args: argparse.Namespace) -> list[CheckResult]:
    results: list[CheckResult] = []
    if args.continuous_batching and args.compile:
        results.append(
            CheckResult(
                name="flag compatibility",
                ok=False,
                detail="--compile is documented as incompatible with --continuous-batching",
                required=True,
            )
        )
    if args.chat_template_kwargs:
        try:
            parsed = json.loads(args.chat_template_kwargs)
        except json.JSONDecodeError as exc:
            results.append(CheckResult("chat-template-kwargs", False, f"invalid JSON: {exc}", True))
        else:
            results.append(
                CheckResult(
                    "chat-template-kwargs",
                    isinstance(parsed, dict),
                    "valid JSON object" if isinstance(parsed, dict) else "must decode to an object",
                    required=not isinstance(parsed, dict),
                )
            )
    if args.cb_max_memory_percent is not None:
        ok = 0.0 < args.cb_max_memory_percent <= 1.0
        results.append(
            CheckResult(
                "cb-max-memory-percent",
                ok,
                "within (0, 1]" if ok else "expected a fraction in (0, 1]",
                required=not ok,
            )
        )
    return results


def print_result(result: CheckResult) -> None:
    level = "OK" if result.ok else ("ERROR" if result.required else "WARN")
    print(f"{level} {result.name}: {result.detail}")


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Dry-run preflight for Transformers CLI serving workflows.")
    parser.add_argument("--check-serving", action="store_true", help="Require serving-extra packages to import.")
    parser.add_argument("--check-clients", action="store_true", help="Check client/chat CLI packages.")
    parser.add_argument("--check-backends", action="store_true", help="Report optional model/audio backend packages.")
    parser.add_argument("--host", default="localhost", help="Host to test for local port availability.")
    parser.add_argument("--port", type=int, default=None, help="Port to test for local availability without binding long-term.")
    parser.add_argument("--base-url", default="http://localhost:8000", help="Existing server URL for optional health probe.")
    parser.add_argument("--probe-health", action="store_true", help="Probe GET /health on an already-running server.")
    parser.add_argument("--timeout", type=float, default=2.0, help="Health probe timeout in seconds.")
    parser.add_argument("--continuous-batching", action="store_true", help="Validate continuous batching flag combinations.")
    parser.add_argument("--compile", action="store_true", help="Validate compile flag combinations.")
    parser.add_argument("--chat-template-kwargs", help="Validate JSON object for serve --chat-template-kwargs.")
    parser.add_argument("--cb-max-memory-percent", type=float, help="Validate continuous batching memory fraction.")
    args = parser.parse_args(argv)

    results: list[CheckResult] = []
    results.extend(import_check(module, required=True) for module in BASE_MODULES)

    if args.check_clients:
        results.extend(import_check(pkg, required=pkg in {"requests", "httpx", "typer", "huggingface_hub"}) for pkg in CLIENT_PACKAGES)
    if args.check_serving:
        results.extend(import_check(pkg, required=True) for pkg in SERVING_PACKAGES)
    if args.check_backends:
        results.extend(import_check(pkg, required=False) for pkg in OPTIONAL_BACKENDS)
    if args.port is not None:
        results.append(port_available(args.host, args.port))
    if args.probe_health:
        results.append(probe_health(args.base_url, args.timeout))
    results.extend(validate_args(args))

    for result in results:
        print_result(result)

    failed_required = [result for result in results if result.required and not result.ok]
    if failed_required:
        print("ERROR serving CLI preflight failed")
        return 1
    print("OK serving CLI preflight passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
