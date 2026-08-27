#!/usr/bin/env python3
"""Run a tiny Graphiti SDK ingest/search smoke.

Requires a live graph backend and model credentials. The script uses a unique
`group_id` by default and does not clear any existing graph data.
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
from datetime import datetime, timezone
from uuid import uuid4

from dotenv import load_dotenv

from graphiti_core import Graphiti
from graphiti_core.driver.falkordb_driver import FalkorDriver
from graphiti_core.driver.neo4j_driver import Neo4jDriver
from graphiti_core.nodes import EpisodeType
from graphiti_core.search.search_config_recipes import NODE_HYBRID_SEARCH_RRF


EPISODES = [
    {
        'content': 'Kamala Harris is the Attorney General of California. She was previously the district attorney for San Francisco.',
        'type': EpisodeType.text,
        'description': 'biographical information',
    },
    {
        'content': 'As AG, Harris was in office from January 3, 2011 to January 3, 2017.',
        'type': EpisodeType.text,
        'description': 'term dates',
    },
    {
        'content': {
            'name': 'Gavin Newsom',
            'position': 'Governor',
            'state': 'California',
            'previous_role': 'Lieutenant Governor',
        },
        'type': EpisodeType.json,
        'description': 'structured profile',
    },
]


def _neo4j_driver() -> Neo4jDriver:
    return Neo4jDriver(
        uri=os.environ.get('NEO4J_URI', 'bolt://localhost:7687'),
        user=os.environ.get('NEO4J_USER', 'neo4j'),
        password=os.environ.get('NEO4J_PASSWORD', 'password'),
        database=os.environ.get('NEO4J_DATABASE', 'neo4j'),
    )


def _falkordb_driver() -> FalkorDriver:
    return FalkorDriver(
        host=os.environ.get('FALKORDB_HOST', 'localhost'),
        port=int(os.environ.get('FALKORDB_PORT', '6379')),
        username=os.environ.get('FALKORDB_USERNAME'),
        password=os.environ.get('FALKORDB_PASSWORD'),
        database=os.environ.get('FALKORDB_DATABASE', 'default_db'),
    )


def _driver_for_backend(backend: str):
    if backend == 'neo4j':
        return _neo4j_driver()
    if backend == 'falkordb':
        return _falkordb_driver()
    raise ValueError(f'Unsupported backend: {backend}')


async def _run(args: argparse.Namespace) -> None:
    if not os.environ.get('OPENAI_API_KEY'):
        raise SystemExit('OPENAI_API_KEY is required for the default Graphiti clients')

    group_id = args.group_id or f'graphiti-quickstart-{uuid4().hex[:8]}'
    graphiti = Graphiti(graph_driver=_driver_for_backend(args.backend))

    try:
        print(f'backend={args.backend} group_id={group_id}')
        await graphiti.build_indices_and_constraints()

        for index, episode in enumerate(EPISODES):
            body = episode['content'] if isinstance(episode['content'], str) else json.dumps(episode['content'])
            await graphiti.add_episode(
                name=f'Quickstart Episode {index}',
                episode_body=body,
                source=episode['type'],
                source_description=episode['description'],
                reference_time=datetime.now(timezone.utc),
                group_id=group_id,
            )
            print(f'added: Quickstart Episode {index} ({episode["type"].value})')

        if args.build_communities:
            communities, community_edges = await graphiti.build_communities(group_ids=[group_id])
            print(f'communities={len(communities)} community_edges={len(community_edges)}')

        print(f'\nfact search: {args.query!r}')
        edges = await graphiti.search(args.query, group_ids=[group_id], num_results=args.limit)
        for edge in edges:
            print(f'- {edge.fact}')

        config = NODE_HYBRID_SEARCH_RRF.model_copy(deep=True)
        config.limit = args.limit
        node_results = await graphiti.search_(
            args.node_query,
            group_ids=[group_id],
            config=config,
        )
        print(f'\nnode search: {args.node_query!r}')
        for node in node_results.nodes:
            labels = ', '.join(node.labels or [])
            print(f'- {node.name} [{labels}]')

        print('\nquickstart complete')
    finally:
        await graphiti.close()


def main() -> int:
    load_dotenv()
    parser = argparse.ArgumentParser(description='Tiny Graphiti ingest/search smoke')
    parser.add_argument('--backend', choices=['neo4j', 'falkordb'], default=os.environ.get('GRAPHITI_BACKEND', 'neo4j'))
    parser.add_argument('--group-id', help='Graphiti group_id to use; defaults to a generated isolated value')
    parser.add_argument('--query', default='Who was the California Attorney General?')
    parser.add_argument('--node-query', default='California Governor')
    parser.add_argument('--limit', type=int, default=5)
    parser.add_argument('--build-communities', action='store_true', help='Also run community detection after ingest')
    args = parser.parse_args()
    asyncio.run(_run(args))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
