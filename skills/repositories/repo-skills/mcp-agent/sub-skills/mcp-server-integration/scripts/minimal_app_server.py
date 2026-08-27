#!/usr/bin/env python3
"""Minimal MCPApp server skeleton with a safe dry-run mode.

Default mode is dry-run: it initializes a tiny MCPApp, records expected tool
registration, and exits without starting a network or stdio server.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from types import SimpleNamespace
from typing import Any

GENERIC_WORKFLOW_TOOLS = [
    "workflows-list",
    "workflows-runs-list",
    "workflows-run",
    "workflows-get_status",
    "workflows-resume",
    "workflows-cancel",
    "workflows-store-credentials",
]


class ToolRecorder:
    """Small FastMCP-like recorder for dry-run tool registration checks."""

    def __init__(self) -> None:
        self.names: list[str] = []
        self.metadata: list[dict[str, Any]] = []

    def tool(self, *args: Any, **kwargs: Any):
        name = kwargs.get("name") or (args[0] if args and isinstance(args[0], str) else None)

        def decorator(func):
            tool_name = name or getattr(func, "__name__", "<unnamed>")
            self.names.append(tool_name)
            self.metadata.append({"name": tool_name, "source": "tool_decorator"})
            return func

        return decorator

    def add_tool(self, func, *, name: str | None = None, **kwargs: Any) -> None:
        tool_name = name or getattr(func, "__name__", "<unnamed>")
        self.names.append(tool_name)
        self.metadata.append(
            {
                "name": tool_name,
                "source": "add_tool",
                "structured_output": kwargs.get("structured_output"),
            }
        )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Create or inspect a minimal MCPApp exposed through FastMCP."
    )
    parser.add_argument(
        "--mode",
        choices=["dry-run", "stdio", "sse"],
        default="dry-run",
        help="dry-run inspects expected tools; stdio/sse explicitly start a server.",
    )
    parser.add_argument("--name", default="minimal_agent_server", help="MCPApp/server name.")
    parser.add_argument("--host", default="127.0.0.1", help="Host for --mode sse.")
    parser.add_argument("--port", type=int, default=8000, help="Port for --mode sse.")
    parser.add_argument("--debug", action="store_true", help="Pass debug=True to FastMCP in server modes.")
    parser.add_argument("--log-level", default="INFO", help="FastMCP log level in server modes.")
    parser.add_argument("--json", action="store_true", help="Print JSON in dry-run mode.")
    parser.add_argument(
        "--require-runtime-imports",
        action="store_true",
        help="In dry-run mode, fail instead of using static fallback when mcp-agent imports are unavailable.",
    )
    return parser


def build_demo_app(name: str):
    """Build a tiny app. Imports are lazy so --help works without mcp-agent."""

    from mcp_agent.app import MCPApp
    from mcp_agent.config import LoggerSettings, MCPSettings, Settings
    from mcp_agent.executor.workflow import Workflow, WorkflowResult

    settings = Settings(
        name=name,
        description="Minimal bundled MCPApp server skeleton",
        execution_engine="asyncio",
        logger=LoggerSettings(transports=["console"], level="info"),
        mcp=MCPSettings(servers={}),
    )
    app = MCPApp(name=name, description="Minimal bundled MCPApp server skeleton", settings=settings)

    @app.tool(name="echo", structured_output=True)
    async def echo(message: str) -> dict[str, str]:
        """Return the input message synchronously to the MCP caller."""
        return {"message": message}

    @app.async_tool(name="echo_async")
    async def echo_async(message: str) -> dict[str, str]:
        """Start an async echo workflow and return workflow_id/run_id."""
        return {"message": message}

    @app.workflow
    class EchoWorkflow(Workflow[str]):
        """Explicit workflow exposed as workflows-EchoWorkflow-run."""

        @app.workflow_run
        async def run(self, message: str) -> WorkflowResult[str]:
            return WorkflowResult(value=message)

    return app


def static_dry_run_result(app_name: str, missing_module: str | None = None) -> dict[str, Any]:
    registered = ["echo", "echo_async", "workflows-EchoWorkflow-run"]
    notes = [
        "Static fallback used; install mcp-agent and dependencies for actual registration introspection.",
        "Decorator tools expose their declared names.",
        "Explicit workflow classes expose workflows-<WorkflowName>-run.",
        "Run with --mode stdio or --mode sse only when you intentionally want to start a server.",
    ]
    if missing_module:
        notes.insert(1, f"Missing import: {missing_module}")
    return {
        "mode": "dry-run",
        "started_service": False,
        "runtime_imports": False,
        "app_name": app_name,
        "generic_workflow_tools": GENERIC_WORKFLOW_TOOLS,
        "registered_app_tools": registered,
        "expected_all_tools": sorted(set(GENERIC_WORKFLOW_TOOLS) | set(registered)),
        "notes": notes,
    }


async def dry_run(args: argparse.Namespace) -> dict[str, Any]:
    try:
        from mcp_agent.server.app_server import create_declared_function_tools, create_workflow_tools

        app = build_demo_app(args.name)
        await app.initialize()
    except ModuleNotFoundError as exc:
        if args.require_runtime_imports:
            raise
        return static_dry_run_result(args.name, exc.name)

    try:
        recorder = ToolRecorder()
        server_context = SimpleNamespace(workflows=app.workflows, context=app.context, app=app)
        create_workflow_tools(recorder, server_context)
        create_declared_function_tools(recorder, server_context)
        registered = sorted(set(recorder.names))
        return {
            "mode": "dry-run",
            "started_service": False,
            "runtime_imports": True,
            "app_name": args.name,
            "generic_workflow_tools": GENERIC_WORKFLOW_TOOLS,
            "registered_app_tools": registered,
            "expected_all_tools": sorted(set(GENERIC_WORKFLOW_TOOLS) | set(registered)),
            "notes": [
                "Decorator tools expose their declared names.",
                "Explicit workflow classes expose workflows-<WorkflowName>-run.",
                "Run with --mode stdio or --mode sse only when you intentionally want to start a server.",
            ],
        }
    finally:
        await app.cleanup()


async def run_server(args: argparse.Namespace) -> None:
    from mcp_agent.server.app_server import create_mcp_server_for_app

    app = build_demo_app(args.name)
    async with app.run() as agent_app:
        fastmcp_kwargs: dict[str, Any] = {"debug": args.debug, "log_level": args.log_level}
        if args.mode == "sse":
            fastmcp_kwargs.update({"host": args.host, "port": args.port})
        mcp_server = create_mcp_server_for_app(agent_app, **fastmcp_kwargs)
        if args.mode == "stdio":
            await mcp_server.run_stdio_async()
        elif args.mode == "sse":
            await mcp_server.run_sse_async()
        else:  # pragma: no cover - guarded by caller
            raise ValueError(f"Unsupported server mode: {args.mode}")


def print_dry_run(result: dict[str, Any], as_json: bool) -> None:
    if as_json:
        print(json.dumps(result, indent=2, sort_keys=True))
        return
    print(f"Dry-run app: {result['app_name']}")
    print("Started service: no")
    print(f"Runtime imports: {'yes' if result.get('runtime_imports') else 'no'}")
    print("Expected tools:")
    for name in result["expected_all_tools"]:
        print(f"- {name}")
    print("Notes:")
    for note in result["notes"]:
        print(f"- {note}")


async def async_main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    try:
        if args.mode == "dry-run":
            result = await dry_run(args)
            print_dry_run(result, args.json)
            return 0
        await run_server(args)
        return 0
    except ModuleNotFoundError as exc:
        print(
            f"ERROR: required module {exc.name!r} is not importable. Install mcp-agent "
            "and its dependencies before using strict dry-run or server modes."
        )
        return 2


def main(argv: list[str] | None = None) -> int:
    return asyncio.run(async_main(argv))


if __name__ == "__main__":
    raise SystemExit(main())
