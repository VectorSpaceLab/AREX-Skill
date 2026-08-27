#!/usr/bin/env python3
"""Tiny local MCP server for Swarms smoke testing."""

from __future__ import annotations

import sys

from mcp.server.fastmcp import FastMCP
from starlette.responses import JSONResponse

API_KEY = "test-key-123"
BEARER_TOKEN = "test-token-abc"


def build_app(profile: str, port: int):
    mcp = FastMCP("swarms-test-server", host="127.0.0.1", port=port)

    @mcp.tool()
    def add(a: int, b: int) -> int:
        """Add two numbers together."""
        return a + b

    @mcp.tool()
    def greet(name: str) -> str:
        """Greet someone by name."""
        return f"Hello, {name}!"

    @mcp.tool()
    def boom() -> str:
        """Always raises, so error handling can be tested."""
        raise ValueError("intentional tool failure")

    @mcp.tool()
    def whoami() -> str:
        """Return the identity of this server instance."""
        return f"server-{port}"

    app = mcp.streamable_http_app()

    if profile != "open":

        @app.middleware("http")
        async def require_auth(request, call_next):
            if profile == "apikey":
                ok = request.headers.get("x-api-key") == API_KEY
            else:
                ok = (
                    request.headers.get("authorization")
                    == f"Bearer {BEARER_TOKEN}"
                )
            if not ok:
                return JSONResponse(
                    {"error": "unauthorized"}, status_code=401
                )
            return await call_next(request)

    return app


if __name__ == "__main__":
    port = int(sys.argv[1])
    profile = sys.argv[2] if len(sys.argv) > 2 else "open"

    import uvicorn

    uvicorn.run(
        build_app(profile, port),
        host="127.0.0.1",
        port=port,
        log_level="error",
    )
