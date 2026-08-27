#!/usr/bin/env python3
"""Quick import and version smoke check for the Graphiti skill."""

from __future__ import annotations

import inspect
import sys
from importlib.metadata import PackageNotFoundError, version


def _show_version(dist_name: str) -> None:
    try:
        print(f'{dist_name}: {version(dist_name)}')
    except PackageNotFoundError:
        print(f'{dist_name}: missing')


def main() -> int:
    print('Graphiti install smoke')
    for dist_name in ('graphiti-core', 'graph-service', 'mcp-server'):
        _show_version(dist_name)

    from graphiti_core import Graphiti
    from graphiti_core.driver.falkordb_driver import FalkorDriver
    from graphiti_core.driver.neo4j_driver import Neo4jDriver
    from graphiti_core.llm_client.openai_client import OpenAIClient
    from graphiti_core.llm_client.openai_generic_client import OpenAIGenericClient

    print('graphiti_core: import ok')
    print(f'Graphiti.__init__: {inspect.signature(Graphiti.__init__)}')
    print(f'Neo4jDriver.__init__: {inspect.signature(Neo4jDriver.__init__)}')
    print(f'FalkorDriver.__init__: {inspect.signature(FalkorDriver.__init__)}')
    print(f'OpenAIClient: {OpenAIClient.__name__}')
    print(f'OpenAIGenericClient.__init__: {inspect.signature(OpenAIGenericClient.__init__)}')

    try:
        import graph_service.main as graph_service_main

        print(f'graph_service.main: {type(graph_service_main.app).__name__}')
    except Exception as exc:  # pragma: no cover - smoke helper only
        print(f'graph_service.main: import failed ({exc})')
        return 1

    try:
        import graphiti_mcp_server as mcp_server

        print(f'graphiti_mcp_server.main: {mcp_server.main.__name__}')
    except Exception as exc:  # pragma: no cover - smoke helper only
        print(f'graphiti_mcp_server: import failed ({exc})')
        return 1

    print('Graphiti install smoke: ok')
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
