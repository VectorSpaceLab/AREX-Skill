#!/usr/bin/env python3
"""Deterministic no-network smoke test for Langroid MCP tool conversion.

The default smoke uses only an in-memory FastMCP server. It does not start an
external process and does not contact any network service.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from typing import Any


def make_server() -> Any:
    """Create an in-memory FastMCP server for deterministic smoke checks."""
    from fastmcp.server import FastMCP
    from pydantic import Field

    server = FastMCP("LangroidMcpSmoke")

    @server.tool()
    def add(
        a: int = Field(..., description="First integer"),
        b: int = Field(..., description="Second integer"),
    ) -> int:
        """Add two integers."""
        return a + b

    @server.tool()
    def echo(text: str = Field(..., description="Text to echo")) -> str:
        """Return text unchanged."""
        return text

    @server.tool()
    def choose_color(
        color: str = Field(..., description="One of red, green, or blue"),
    ) -> str:
        """Echo a color-like value for schema and invocation checks."""
        if color not in {"red", "green", "blue"}:
            return "invalid"
        return color

    return server


def request_name(tool_cls: type[Any]) -> str:
    """Return the Langroid request name for a generated tool class."""
    try:
        return str(tool_cls.default_value("request"))
    except Exception:
        return str(tool_cls.name())


def content_text(raw: Any) -> str:
    """Normalize recent and older call_tool_async return shapes to text."""
    if raw is None:
        return ""
    if isinstance(raw, tuple):
        return str(raw[0])
    return str(raw)


async def run_smoke(selected_tool: str) -> dict[str, Any]:
    """Run a deterministic MCP conversion and invocation smoke."""
    from langroid.agent.tools.mcp import get_tool_async, get_tools_async

    server = make_server()
    tools = await get_tools_async(server)
    names = sorted(request_name(tool) for tool in tools)

    expected = {"add", "echo", "choose_color"}
    missing = sorted(expected - set(names))
    if missing:
        raise AssertionError(f"Missing generated tool(s): {missing}")

    results: dict[str, Any] = {"tools": names, "checks": {}}

    if selected_tool in {"all", "add"}:
        AddTool = await get_tool_async(server, "add")
        add_result = await AddTool(a=2, b=5).handle_async()
        if "7" not in str(add_result):
            raise AssertionError(f"Unexpected add result: {add_result!r}")
        results["checks"]["add"] = str(add_result)

    if selected_tool in {"all", "echo"}:
        EchoTool = await get_tool_async(server, "echo")
        echo_result = await EchoTool(text="hello-mcp").handle_async()
        if "hello-mcp" not in str(echo_result):
            raise AssertionError(f"Unexpected echo result: {echo_result!r}")
        results["checks"]["echo"] = str(echo_result)

    if selected_tool in {"all", "custom"}:
        EchoBase = await get_tool_async(server, "echo")

        class LoudEchoTool(EchoBase):  # type: ignore[misc, valid-type]
            async def handle_async(self) -> str:
                raw = await self.call_tool_async()  # type: ignore[attr-defined]
                return content_text(raw).upper()

        custom_result = await LoudEchoTool(text="custom-handler").handle_async()
        if custom_result != "CUSTOM-HANDLER":
            raise AssertionError(f"Unexpected custom result: {custom_result!r}")
        results["checks"]["custom"] = custom_result

    return results


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Run a no-network in-memory FastMCP smoke test for Langroid MCP "
            "tool conversion and invocation."
        )
    )
    parser.add_argument(
        "--tool",
        choices=["all", "add", "echo", "custom"],
        default="all",
        help="Limit the invocation check to one tool path. Default: all.",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Print machine-readable JSON only.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    result = asyncio.run(run_smoke(args.tool))
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print("Langroid MCP in-memory smoke passed")
        print(json.dumps(result, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
