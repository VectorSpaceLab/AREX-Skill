"""Helper for examples and tests that need a local agent-server subprocess.

The helper starts `python -m openhands.agent_server`, waits for `/health`, and
shuts the process down on exit. It is intentionally small and reusable.
"""

from __future__ import annotations

import os
import secrets
import subprocess
import sys
import threading
import time
from collections.abc import Mapping
from contextlib import AbstractContextManager
from typing import TextIO

import httpx


def _stream_output(stream: TextIO, prefix: str, target_stream: TextIO) -> None:
    try:
        for line in iter(stream.readline, ""):
            if line:
                target_stream.write(f"[{prefix}] {line}")
                target_stream.flush()
    finally:
        stream.close()


class ManagedAPIServer(AbstractContextManager["ManagedAPIServer"]):
    """Run `openhands.agent_server` in a subprocess and wait for `/health`."""

    def __init__(
        self,
        port: int = 8000,
        host: str = "127.0.0.1",
        *,
        extra_env: Mapping[str, str] | None = None,
        use_session_api_key: bool = False,
        health_request_timeout: float = 1.0,
        max_start_wait_seconds: int = 30,
    ) -> None:
        self.port = port
        self.host = host
        self.base_url = f"http://{host}:{port}"
        self.process: subprocess.Popen[str] | None = None
        self.session_api_key = (
            secrets.token_urlsafe(32) if use_session_api_key else None
        )
        self._extra_env = dict(extra_env) if extra_env else {}
        self._health_request_timeout = health_request_timeout
        self._max_start_wait_seconds = max_start_wait_seconds

    def __enter__(self) -> ManagedAPIServer:
        env = {"LOG_JSON": "true", **self._extra_env, **os.environ}
        env.setdefault("OPENHANDS_SUPPRESS_BANNER", "1")
        if self.session_api_key is not None:
            env["SESSION_API_KEY"] = self.session_api_key

        self.process = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "openhands.agent_server",
                "--port",
                str(self.port),
                "--host",
                self.host,
            ],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            env=env,
        )
        assert self.process.stdout is not None
        assert self.process.stderr is not None
        threading.Thread(
            target=_stream_output,
            args=(self.process.stdout, "SERVER", sys.stdout),
            daemon=True,
        ).start()
        threading.Thread(
            target=_stream_output,
            args=(self.process.stderr, "SERVER", sys.stderr),
            daemon=True,
        ).start()

        for _ in range(self._max_start_wait_seconds):
            try:
                response = httpx.get(
                    f"{self.base_url}/health", timeout=self._health_request_timeout
                )
                if response.status_code == 200:
                    return self
            except httpx.RequestError:
                pass
            if self.process.poll() is not None:
                raise RuntimeError("Server exited before becoming healthy")
            time.sleep(1)
        raise RuntimeError(
            f"Server failed to start after {self._max_start_wait_seconds} seconds"
        )

    def __exit__(self, *exc: object) -> None:
        if self.process is None:
            return
        self.process.terminate()
        try:
            self.process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            self.process.kill()
            self.process.wait()
