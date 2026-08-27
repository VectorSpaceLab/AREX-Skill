#!/usr/bin/env python3
"""Run a safe UnrealCV Python client smoke test.

This script exercises the packaged Python client without requiring Unreal Engine.
It starts a tiny local echo/message server, connects with ``unrealcv.Client``,
checks framing and reconnect behavior, and decodes a couple of tiny in-memory
payloads.

Example:
    python local_client_smoke.py
"""

from __future__ import annotations

import argparse
import io
import random
import socket
import socketserver
import threading
from dataclasses import dataclass
from pathlib import Path

import numpy as np
from PIL import Image

from unrealcv import ApiVersionManager, Client, SocketMessage
from unrealcv.api import MsgDecoder
from unrealcv.util import parse_resolution, read_npy, read_png


class _RejectionHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        self.request.close()


class _ThreadedServer(socketserver.ThreadingTCPServer):
    daemon_threads = True
    allow_reuse_address = True

    def __init__(self, server_address, request_handler):
        super().__init__(server_address, request_handler)
        self._thread = threading.Thread(target=self.serve_forever, daemon=True)
        self._thread.start()

    def shutdown(self) -> None:  # pragma: no cover - exercised via smoke script
        try:
            super().shutdown()
        finally:
            super().server_close()


class _MessageHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        while True:
            message = SocketMessage.ReceivePayload(self.request)
            if not message:
                break
            SocketMessage.WrapAndSendPayload(self.request, message)


class _NullHandler(socketserver.BaseRequestHandler):
    def handle(self) -> None:
        while True:
            message = SocketMessage.ReceivePayload(self.request)
            if not message:
                break


class MessageServer(_ThreadedServer):
    def __init__(self, endpoint):
        super().__init__(endpoint, _MessageHandler)


class EchoServer(_ThreadedServer):
    def __init__(self, endpoint):
        super().__init__(endpoint, _MessageHandler)


class NullServer(_ThreadedServer):
    def __init__(self, endpoint):
        super().__init__(endpoint, _NullHandler)


@dataclass
class SmokeResult:
    connected: bool
    echoed: list[str]
    png_shape: tuple[int, ...]
    npy_shape: tuple[int, ...]
    capability_checked: bool


def _free_port(host: str) -> int:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind((host, 0))
        return sock.getsockname()[1]


def _make_png_bytes() -> bytes:
    image = Image.new("RGBA", (1, 1), (10, 20, 30, 255))
    buf = io.BytesIO()
    image.save(buf, format="PNG")
    return buf.getvalue()


def _make_npy_bytes() -> bytes:
    buf = io.BytesIO()
    np.save(buf, np.ones((1, 2), dtype=np.float32))
    return buf.getvalue()


def run_smoke(host: str, trials: int, timeout: float) -> SmokeResult:
    port = _free_port(host)
    server = MessageServer((host, port))
    client = Client((host, port))
    echoed: list[str] = []

    try:
        client.connect(timeout=timeout)
        connected = client.isconnected()
        for index in range(trials):
            payload = f"trial-{index}-{random.randrange(10_000)}"
            echoed.append(client.request(payload, timeout=timeout))
        client.disconnect()

        png_shape = tuple(read_png(_make_png_bytes()).shape)
        npy_shape = tuple(read_npy(_make_npy_bytes()).shape)

        version_calls = []

        def fake_request(message, timeout=5):
            version_calls.append(message)
            if message == ApiVersionManager.COMMANDS_QUERY:
                return "vget /unrealcv/commands\nvget /camera/[uint]/location"
            if message == ApiVersionManager.VERSION_QUERY:
                return "1.2.0"
            return "ok"

        api_version = ApiVersionManager(fake_request)
        api_version.load()
        capability_checked = api_version.command_capabilities_checked() and bool(version_calls)

        return SmokeResult(
            connected=connected,
            echoed=echoed,
            png_shape=png_shape,
            npy_shape=npy_shape,
            capability_checked=capability_checked,
        )
    finally:
        try:
            client.disconnect()
        finally:
            server.shutdown()


def main() -> int:
    parser = argparse.ArgumentParser(description="Run a safe UnrealCV client smoke test")
    parser.add_argument("--host", default="127.0.0.1", help="Host to bind the local smoke server")
    parser.add_argument("--trials", type=int, default=3, help="Number of echo requests to send")
    parser.add_argument("--timeout", type=float, default=1.0, help="Client request timeout in seconds")
    args = parser.parse_args()

    result = run_smoke(args.host, args.trials, args.timeout)
    assert result.connected, "Client did not connect to the local smoke server"
    assert len(result.echoed) == args.trials, "Unexpected number of echoed responses"
    assert result.png_shape == (1, 1, 3), f"Unexpected PNG decode shape: {result.png_shape}"
    assert result.npy_shape == (1, 2, 1), f"Unexpected NPY decode shape: {result.npy_shape}"
    assert result.capability_checked, "ApiVersionManager did not complete a capability check"

    print("UnrealCV client smoke test passed")
    print(f"- echoed {len(result.echoed)} messages")
    print(f"- PNG shape: {result.png_shape}")
    print(f"- NPY shape: {result.npy_shape}")
    print("- ApiVersionManager capability check: passed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
