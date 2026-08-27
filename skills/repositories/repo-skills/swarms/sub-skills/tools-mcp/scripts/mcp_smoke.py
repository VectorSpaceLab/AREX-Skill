#!/usr/bin/env python3
"""Offline MCP smoke check for Swarms."""

from __future__ import annotations

import socket
import subprocess
import sys
import time
from pathlib import Path

from swarms.schemas.mcp_schemas import MCPConnection
from swarms.tools.mcp_manager import MCPManager

SERVER_SCRIPT = Path(__file__).with_name("mcp_local_server.py")
API_KEY = "test-key-123"
BEARER_TOKEN = "test-token-abc"


def free_port() -> int:
    with socket.socket() as sock:
        sock.bind(("127.0.0.1", 0))
        return sock.getsockname()[1]


def wait_for_port(port: int, timeout: float = 30.0) -> None:
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            with socket.create_connection(("127.0.0.1", port), timeout=0.5):
                return
        except OSError:
            time.sleep(0.1)
    raise RuntimeError(f"MCP test server on port {port} never started")


class Server:
    def __init__(self, profile: str):
        self.port = free_port()
        self.profile = profile
        self.url = f"http://127.0.0.1:{self.port}/mcp"
        self.process = subprocess.Popen(
            [
                sys.executable,
                str(SERVER_SCRIPT),
                str(self.port),
                profile,
            ],
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
        try:
            wait_for_port(self.port)
        except Exception:
            self.stop()
            raise

    def stop(self) -> None:
        self.process.terminate()
        try:
            self.process.wait(timeout=10)
        except subprocess.TimeoutExpired:
            self.process.kill()


def smoke_profile(profile: str):
    server = Server(profile)
    try:
        if profile == "open":
            manager = MCPManager(mcp_url=server.url, agent_name="smoke")
        elif profile == "apikey":
            manager = MCPManager(
                mcp_config=MCPConnection(
                    url=server.url,
                    api_key=API_KEY,
                    api_key_header="X-API-Key",
                    api_key_prefix=None,
                ),
                agent_name="smoke",
            )
        else:
            manager = MCPManager(
                mcp_config=MCPConnection(
                    url=server.url,
                    authorization_token=BEARER_TOKEN,
                ),
                agent_name="smoke",
            )

        tools = manager.get_tools()
        names = manager.list_tool_names()
        assert "add" in names
        assert any(t.get("function", {}).get("name") == "add" for t in tools)

        result = manager.execute_tool_calls(
            [
                {
                    "function": {
                        "name": "add",
                        "arguments": '{"a": 2, "b": 3}',
                    }
                }
            ],
            output_type="dict",
        )
        print(profile, result)
    finally:
        server.stop()


def main() -> None:
    for profile in ("open", "apikey", "bearer"):
        smoke_profile(profile)
    print("mcp smoke ok")


if __name__ == "__main__":
    main()
