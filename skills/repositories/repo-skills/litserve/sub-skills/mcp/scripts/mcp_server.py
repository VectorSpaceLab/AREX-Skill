#!/usr/bin/env python
"""Safe LitServe MCP example.

Run this file from an environment with litserve and fastmcp installed.

Examples:
    python mcp_server.py --print-tool
    python mcp_server.py --port 8000

The MCP streamable HTTP endpoint is /mcp/ on the same host and port as the
LitServe server. The generated tool schema expects MCP call arguments shaped as:

    {"request": {"input": 3.0}}
"""

import argparse
import json
import logging
from typing import Any

from pydantic import BaseModel, Field

import litserve as ls
from litserve.mcp import MCP


class PowerRequest(BaseModel):
    """Request body for the bundled MCP power tool."""

    input: float = Field(description="Number whose square should be returned.")


class PowerAPI(ls.LitAPI):
    """Return the square of a number."""

    def __init__(self, api_path: str = "/predict", tool_name: str = "power") -> None:
        super().__init__(
            api_path=api_path,
            mcp=MCP(
                name=tool_name,
                description="Return the square of a number from a PowerRequest.",
            ),
        )

    def setup(self, device: str) -> None:
        self.device = device

    def decode_request(self, request: PowerRequest) -> float:
        return request.input

    def predict(self, x: float) -> float:
        return x * x

    def encode_response(self, output: float) -> dict[str, float]:
        return {"output": output}


def build_api(args: argparse.Namespace) -> PowerAPI:
    return PowerAPI(api_path=args.api_path, tool_name=args.tool_name)


def tool_as_dict(api: PowerAPI) -> dict[str, Any]:
    # Keep --print-tool machine-readable even though LitServe logs a warning when
    # auto-extracting an omitted MCP input_schema.
    logging.getLogger("litserve.mcp").setLevel(logging.ERROR)
    tool = api.mcp.as_tool()
    return {
        "name": tool.name,
        "description": tool.description,
        "endpoint": tool.endpoint,
        "inputSchema": tool.inputSchema,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run a small MCP-enabled LitServe server.")
    parser.add_argument("--host", default="0.0.0.0", help="Host passed to LitServer.run().")
    parser.add_argument("--port", default=8000, type=int, help="Port passed to LitServer.run().")
    parser.add_argument("--api-path", default="/predict", help="LitServe prediction endpoint path.")
    parser.add_argument("--tool-name", default="power", help="MCP tool name.")
    parser.add_argument(
        "--print-tool",
        action="store_true",
        help="Print generated MCP tool metadata and exit without starting the server.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    api = build_api(args)

    if args.print_tool:
        print(json.dumps(tool_as_dict(api), indent=2, sort_keys=True))
        return

    print(f"Starting LitServe prediction endpoint at http://{args.host}:{args.port}{args.api_path}")
    print(f"Starting MCP streamable HTTP endpoint at http://{args.host}:{args.port}/mcp/")
    print('Example MCP call arguments: {"request": {"input": 3.0}}')
    server = ls.LitServer(api)
    server.run(host=args.host, port=args.port)


if __name__ == "__main__":
    main()
