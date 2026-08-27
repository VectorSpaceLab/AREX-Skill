#!/usr/bin/env python3
"""Launch the bundled minimal LitServe server and verify one request.

This helper stays inside the generated skill tree so future agents can smoke-test
LitServe without reopening the source checkout.
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import subprocess
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path


def wait_for_health(url: str, timeout: float) -> None:
    deadline = time.time() + timeout
    last_error: Exception | None = None
    while time.time() < deadline:
        try:
            with urllib.request.urlopen(url, timeout=1) as response:
                if response.getcode() == 200:
                    return
        except Exception as exc:  # pragma: no cover - best effort smoke helper
            last_error = exc
        time.sleep(0.5)
    raise TimeoutError(f"server did not become ready at {url!r}: {last_error}")


def run_smoke(port: int, startup_timeout: float) -> dict[str, object]:
    skill_root = Path(__file__).resolve().parents[1]
    server_script = skill_root / "sub-skills" / "server-basics" / "scripts" / "minimal_server.py"
    cmd = [
        sys.executable,
        str(server_script),
        "--host",
        "127.0.0.1",
        "--port",
        str(port),
        "--accelerator",
        "cpu",
        "--devices",
        "1",
        "--workers-per-device",
        "1",
        "--timeout",
        "30",
        "--log-level",
        "warning",
    ]
    process = subprocess.Popen(cmd, start_new_session=True)
    try:
        wait_for_health(f"http://127.0.0.1:{port}/health", startup_timeout)
        request = urllib.request.Request(
            f"http://127.0.0.1:{port}/predict",
            data=json.dumps({"input": 4.0}).encode("utf-8"),
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        with urllib.request.urlopen(request, timeout=10) as response:
            payload = json.loads(response.read().decode("utf-8"))
            status = response.getcode()
    finally:
        try:
            os.killpg(process.pid, signal.SIGTERM)
        except ProcessLookupError:
            pass
        try:
            process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            process.wait(timeout=10)

    if status != 200:
        raise RuntimeError(f"unexpected status code: {status}")
    if payload.get("output") != 16.0:
        raise RuntimeError(f"unexpected payload: {payload!r}")
    return payload


def main() -> None:
    parser = argparse.ArgumentParser(description="Smoke-test the bundled LitServe server.")
    parser.add_argument("--port", type=int, default=8000, help="Local port to bind.")
    parser.add_argument(
        "--startup-timeout",
        type=float,
        default=30.0,
        help="Seconds to wait for /health before failing.",
    )
    args = parser.parse_args()

    payload = run_smoke(port=args.port, startup_timeout=args.startup_timeout)
    print(json.dumps(payload, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
