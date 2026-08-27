#!/usr/bin/env python3
"""Read-only SMARTS camera/Panda3D and optional Envision endpoint probe.

This helper never installs packages, starts a server, loads a scenario, or
runs a long renderer test. For headless Linux, invoke it through an approved
Xvfb wrapper, for example: ``xvfb-run -a python check_rendering.py``.
"""

from __future__ import annotations

import argparse
import importlib
import importlib.util
import os
import socket
from urllib.parse import urlparse


IMPORTS = (
    ("panda3d.core", "Panda3D camera extra"),
    ("gltf", "panda3d-gltf loader"),
    ("smarts.p3d.renderer", "SMARTS renderer"),
)


def _check_import(name: str, label: str) -> bool:
    if importlib.util.find_spec(name) is None:
        print(f"MISSING {label}: {name}")
        return False
    try:
        module = importlib.import_module(name)
    except Exception as exc:  # import diagnostics should not hide the cause
        print(f"ERROR {label}: {name}: {type(exc).__name__}: {exc}")
        return False
    version = getattr(module, "__version__", None)
    suffix = f" ({version})" if version else ""
    print(f"OK {label}: {name}{suffix}")
    return True


def _probe_offscreen() -> bool:
    try:
        from panda3d.core import loadPrcFileData

        loadPrcFileData("", "window-type offscreen")
        from smarts.p3d.renderer import Renderer

        renderer = Renderer("diagnostic-renderer")
        renderer.destroy()
    except Exception as exc:
        print(f"ERROR bounded offscreen renderer probe: {type(exc).__name__}: {exc}")
        return False
    print("OK bounded offscreen renderer construction/teardown")
    print("NOTE this is not a map, image, shader, or full renderer test")
    return True


def _check_endpoint(endpoint: str, timeout: float) -> bool:
    parsed = urlparse(endpoint)
    host = parsed.hostname or "localhost"
    port = parsed.port or (443 if parsed.scheme == "wss" else 80)
    try:
        with socket.create_connection((host, port), timeout=timeout):
            print(f"OK Envision TCP endpoint reachable: {host}:{port}")
            return True
    except OSError as exc:
        print(f"UNAVAILABLE Envision endpoint {endpoint}: {exc}")
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Probe SMARTS camera imports without changing the host."
    )
    parser.add_argument(
        "--probe-offscreen",
        action="store_true",
        help="construct and destroy one bounded offscreen Renderer",
    )
    parser.add_argument(
        "--check-envision",
        action="store_true",
        help="make a short TCP reachability probe; never starts Envision",
    )
    parser.add_argument(
        "--endpoint",
        default="ws://localhost:8081",
        help="Envision websocket endpoint for --check-envision",
    )
    parser.add_argument("--timeout", type=float, default=0.5)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    print(f"DISPLAY={os.environ.get('DISPLAY', '<unset>')}")
    results = [_check_import(name, label) for name, label in IMPORTS]
    if args.probe_offscreen and all(results):
        results.append(_probe_offscreen())
    elif args.probe_offscreen:
        print("SKIP offscreen probe because an import prerequisite is missing")
        results.append(False)
    if args.check_envision:
        results.append(_check_endpoint(args.endpoint, max(0.05, args.timeout)))
    print("RESULT=" + ("pass" if all(results) else "incomplete"))
    return 0 if all(results) else 1


if __name__ == "__main__":
    raise SystemExit(main())
