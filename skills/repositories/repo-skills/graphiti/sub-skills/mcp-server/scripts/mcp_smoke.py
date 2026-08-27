#!/usr/bin/env python3
"""Smoke-check the Graphiti MCP server with the official MCP client.

Stdio mode starts the installed `graphiti_mcp_server` package in a subprocess.
HTTP mode connects to an already-running streamable HTTP server.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
import time
from contextlib import AsyncExitStack
from pathlib import Path
from typing import Any
from uuid import uuid4

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


SERVER_BOOTSTRAP = (
    "import sys; sys.argv[0] = 'graphiti_mcp_server'; "
    'from graphiti_mcp_server import main; main()'
)
EXPECTED_TOOLS = {
    'add_memory',
    'search_nodes',
    'search_memory_facts',
    'get_episodes',
    'clear_graph',
    'get_status',
}


def _decode_tool_result(result: Any) -> Any:
    if not getattr(result, 'content', None):
        return None
    text = getattr(result.content[0], 'text', None)
    if text is None:
        return None
    try:
        return json.loads(text)
    except (json.JSONDecodeError, TypeError):
        return text


def _raise_on_error(tool: str, response: Any) -> None:
    if isinstance(response, dict) and response.get('error'):
        raise RuntimeError(f'{tool} returned error: {response["error"]}')


async def _open_stdio_session(args: argparse.Namespace, group_id: str, stack: AsyncExitStack) -> ClientSession:
    server_args = ['-c', SERVER_BOOTSTRAP, '--transport', 'stdio', '--group-id', group_id]
    if args.config:
        server_args.extend(['--config', args.config])
    if args.database_provider:
        server_args.extend(['--database-provider', args.database_provider])

    params = StdioServerParameters(
        command=sys.executable,
        args=server_args,
        env=dict(os.environ),
        cwd=str(Path(args.server_cwd)) if args.server_cwd else None,
    )
    read_stream, write_stream = await stack.enter_async_context(stdio_client(params))
    session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
    await session.initialize()
    return session


async def _open_http_session(args: argparse.Namespace, stack: AsyncExitStack) -> ClientSession:
    from mcp.client.http import http_client

    read_stream, write_stream = await stack.enter_async_context(http_client(args.base_url))
    session = await stack.enter_async_context(ClientSession(read_stream, write_stream))
    await session.initialize()
    return session


async def _call(session: ClientSession, tool: str, arguments: dict[str, Any]) -> Any:
    result = await session.call_tool(tool, arguments)
    decoded = _decode_tool_result(result)
    _raise_on_error(tool, decoded)
    return decoded


async def _wait_for_episodes(
    session: ClientSession,
    group_id: str,
    expected: int,
    timeout: float,
    poll: float,
) -> list[dict[str, Any]]:
    deadline = time.monotonic() + timeout
    while time.monotonic() < deadline:
        response = await _call(
            session,
            'get_episodes',
            {'group_ids': [group_id], 'max_episodes': max(expected, 10)},
        )
        episodes = response.get('episodes', []) if isinstance(response, dict) else []
        if len(episodes) >= expected:
            return episodes
        await asyncio.sleep(poll)
    raise RuntimeError('queued episode did not appear before timeout')


async def _run(args: argparse.Namespace) -> None:
    group_id = args.group_id or f'mcpsmoke{uuid4().hex[:8]}'
    async with AsyncExitStack() as stack:
        if args.transport == 'stdio':
            session = await _open_stdio_session(args, group_id, stack)
        else:
            session = await _open_http_session(args, stack)

        tool_result = await session.list_tools()
        tools = sorted(tool.name for tool in tool_result.tools)
        print(f'tools: {len(tools)}')
        for name in tools:
            print(f'- {name}')

        missing = sorted(EXPECTED_TOOLS - set(tools))
        if missing:
            raise RuntimeError(f'missing expected tools: {missing}')

        if args.list_only:
            return

        status = await _call(session, 'get_status', {})
        print(f'status: {status}')

        add_response = await _call(
            session,
            'add_memory',
            {
                'name': 'MCP smoke episode',
                'episode_body': 'Alice is a software engineer at Acme Corporation.',
                'group_id': group_id,
                'source': 'text',
                'source_description': 'mcp smoke test',
            },
        )
        print(f'add_memory: {add_response}')

        try:
            episodes = await _wait_for_episodes(
                session,
                group_id=group_id,
                expected=1,
                timeout=args.wait_timeout,
                poll=args.poll,
            )
            print(f'episodes: {len(episodes)}')

            facts = await _call(
                session,
                'search_memory_facts',
                {
                    'query': 'Who works at Acme?',
                    'group_ids': [group_id],
                    'max_facts': args.max_facts,
                },
            )
            fact_items = facts.get('facts', []) if isinstance(facts, dict) else []
            print(f'facts: {len(fact_items)}')

            nodes = await _call(
                session,
                'search_nodes',
                {
                    'query': 'Alice',
                    'group_ids': [group_id],
                    'max_nodes': args.max_nodes,
                },
            )
            node_items = nodes.get('nodes', []) if isinstance(nodes, dict) else []
            print(f'nodes: {len(node_items)}')
        finally:
            if args.cleanup:
                cleanup = await _call(session, 'clear_graph', {'group_ids': [group_id]})
                print(f'cleanup: {cleanup}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Smoke-check the Graphiti MCP server')
    parser.add_argument('--transport', choices=['stdio', 'http'], default='stdio')
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--config', help='Optional server YAML config path for stdio mode')
    parser.add_argument('--database-provider', choices=['neo4j', 'falkordb'], help='Optional stdio CLI backend override')
    parser.add_argument('--server-cwd', help='Optional working directory for the stdio server subprocess')
    parser.add_argument('--group-id', help='Optional group id; defaults to a fresh safe value')
    parser.add_argument('--wait-timeout', type=float, default=180.0)
    parser.add_argument('--poll', type=float, default=3.0)
    parser.add_argument('--max-facts', type=int, default=5)
    parser.add_argument('--max-nodes', type=int, default=5)
    parser.add_argument('--list-only', action='store_true', help='Only initialize the session and list tools')
    parser.add_argument('--no-cleanup', dest='cleanup', action='store_false', help='Keep the smoke group after the run')
    parser.set_defaults(cleanup=True)
    args = parser.parse_args()
    asyncio.run(_run(args))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
