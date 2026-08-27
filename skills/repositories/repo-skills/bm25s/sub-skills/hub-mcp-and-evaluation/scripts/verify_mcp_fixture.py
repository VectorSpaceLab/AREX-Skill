#!/usr/bin/env python3
"""Run bounded, in-process MCP tool checks against a local bm25s index."""
from __future__ import annotations

import argparse
import asyncio
import importlib
import inspect
import json
import sys
from pathlib import Path
from typing import Any


def diagnose_import() -> int:
    """Print safe dependency/import diagnostics without loading an index."""
    for module_name in ("mcp", "mcp.server.fastmcp", "bm25s.mcp.server"):
        try:
            module = importlib.import_module(module_name)
            version = getattr(module, "__version__", "")
            print(f"{module_name}: OK" + (f" (version {version})" if version else ""))
        except Exception as exc:  # diagnostic mode must report, not traceback
            print(f"{module_name}: FAIL {type(exc).__name__}: {exc}")
    try:
        from mcp.server.fastmcp import FastMCP

        print(f"FastMCP.call_tool async: {inspect.iscoroutinefunction(FastMCP.call_tool)}")
        print(f"FastMCP.list_tools async: {inspect.iscoroutinefunction(FastMCP.list_tools)}")
        print(f"FastMCP.run signature: {inspect.signature(FastMCP.run)}")
    except Exception as exc:
        print(f"FastMCP API details: unavailable ({type(exc).__name__}: {exc})")
    return 0


def _content_to_text(value: Any) -> str:
    """Make MCP text/content-block results readable without assuming one API shape."""
    if isinstance(value, str):
        return value
    if isinstance(value, dict):
        # Some MCP versions return a structured result with a nested ``result``.
        if set(value) == {"result"}:
            return _content_to_text(value["result"])
        return json.dumps(value, default=str, sort_keys=True)
    if isinstance(value, (list, tuple)):
        pieces = []
        for item in value:
            text = _content_to_text(item)
            if text and text not in pieces:
                pieces.append(text)
        return "\n".join(pieces)
    if hasattr(value, "text"):
        return str(value.text)
    return str(value)


async def verify(index_dir: Path, query: str, k: int) -> dict[str, object]:
    if not index_dir.is_dir():
        raise SystemExit(f"Index directory does not exist: {index_dir}")
    corpus = index_dir / "corpus.jsonl"
    if not corpus.is_file():
        raise SystemExit(
            "MCP fixture requires corpus-backed index data; missing "
            f"{corpus}. Recreate with create_mcp_fixture.py."
        )
    try:
        from bm25s.mcp.server import create_mcp_server
    except Exception as exc:
        raise SystemExit(
            "Cannot import bm25s.mcp.server.create_mcp_server. "
            "Run --diagnose-import and check the mcp<2 compatibility line. "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    try:
        server = create_mcp_server(str(index_dir))
        call_tool = getattr(server, "call_tool", None)
        if call_tool is None or not callable(call_tool):
            raise RuntimeError("installed MCP FastMCP has no callable call_tool method")
        list_tools = getattr(server, "list_tools", None)
        tools = await list_tools() if list_tools is not None else []
        names = [getattr(tool, "name", str(tool)) for tool in tools]
        info = await call_tool("get_info", arguments={})
        results = await call_tool(
            "retrieve", arguments={"query": query, "k": k}
        )
    except Exception as exc:
        raise SystemExit(
            "Bounded MCP tool call failed; no server was launched. "
            f"{type(exc).__name__}: {exc}"
        ) from exc

    summary = {
        "index_dir": str(index_dir),
        "tool_names": names,
        "get_info": _content_to_text(info),
        "retrieve": _content_to_text(results),
        "transport_started": False,
    }
    print(json.dumps(summary, indent=2))
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Verify bm25s MCP tools in-process using a local corpus-backed index."
    )
    parser.add_argument("--index-dir", type=Path, help="Local saved bm25s index directory.")
    parser.add_argument("--query", default="blue fox", help="Bounded fixture query.")
    parser.add_argument("--k", type=int, default=2, help="Small retrieval cutoff (default: 2).")
    parser.add_argument(
        "--diagnose-import",
        action="store_true",
        help="Print MCP/import/API diagnostics without loading an index.",
    )
    args = parser.parse_args()
    if args.diagnose_import:
        return diagnose_import()
    if args.index_dir is None:
        parser.error("--index-dir is required unless --diagnose-import is used")
    if args.k < 1 or args.k > 20:
        parser.error("--k must be between 1 and 20 for a bounded fixture check")
    asyncio.run(verify(args.index_dir, args.query, args.k))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
