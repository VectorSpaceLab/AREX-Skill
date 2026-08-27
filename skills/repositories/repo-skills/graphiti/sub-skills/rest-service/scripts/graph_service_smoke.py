#!/usr/bin/env python3
"""Smoke-check the Graphiti REST service.

By default the script:
1. checks /healthcheck,
2. posts one message to /messages,
3. polls /episodes/{group_id},
4. calls /search,
5. cleans up the generated group.
"""

from __future__ import annotations

import argparse
import asyncio
from datetime import datetime, timezone
from uuid import uuid4

import httpx


async def _wait_for_episode(client: httpx.AsyncClient, group_id: str, timeout: float, poll: float) -> list[dict]:
    deadline = asyncio.get_running_loop().time() + timeout
    last_response: httpx.Response | None = None
    while asyncio.get_running_loop().time() < deadline:
        response = await client.get(f'/episodes/{group_id}', params={'last_n': 10})
        last_response = response
        if response.status_code == 200:
            episodes = response.json()
            if isinstance(episodes, list) and episodes:
                return episodes
        await asyncio.sleep(poll)
    detail = f' last_status={last_response.status_code}' if last_response is not None else ''
    raise RuntimeError(f'episode did not appear before timeout{detail}')


async def _run(args: argparse.Namespace) -> None:
    group_id = args.group_id or f'rest-smoke-{uuid4().hex[:8]}'
    async with httpx.AsyncClient(base_url=args.base_url, timeout=args.timeout) as client:
        health = await client.get('/healthcheck')
        health.raise_for_status()
        print(f'healthcheck: {health.json()}')

        if args.health_only:
            return

        message = {
            'content': 'Alice is a software engineer at Acme Corporation.',
            'role_type': 'user',
            'role': 'Alice',
            'name': 'REST smoke episode',
            'timestamp': datetime.now(timezone.utc).isoformat(),
            'source_description': 'smoke test',
        }

        try:
            ingest = await client.post(
                '/messages',
                json={
                    'group_id': group_id,
                    'messages': [message],
                },
            )
            ingest.raise_for_status()
            print(f'messages: {ingest.json()}')

            episodes = await _wait_for_episode(client, group_id, args.wait_timeout, args.poll)
            print(f'episodes: {len(episodes)}')

            search = await client.post(
                '/search',
                json={
                    'group_ids': [group_id],
                    'query': 'Who works at Acme?',
                    'max_facts': args.max_facts,
                },
            )
            search.raise_for_status()
            facts = search.json().get('facts', [])
            print(f'facts: {len(facts)}')
            for fact in facts[: args.max_facts]:
                print(f'- {fact.get("fact")}')
        finally:
            if args.cleanup:
                cleanup = await client.delete(f'/group/{group_id}')
                if cleanup.is_success:
                    print(f'cleanup: {cleanup.json()}')
                else:
                    print(f'cleanup failed: {cleanup.status_code} {cleanup.text}')


def main() -> int:
    parser = argparse.ArgumentParser(description='Smoke-check the Graphiti REST service')
    parser.add_argument('--base-url', default='http://127.0.0.1:8000')
    parser.add_argument('--timeout', type=float, default=10.0, help='HTTP timeout per request')
    parser.add_argument('--wait-timeout', type=float, default=180.0, help='How long to wait for queued ingest')
    parser.add_argument('--poll', type=float, default=3.0, help='Polling interval for /episodes')
    parser.add_argument('--group-id', help='Optional group id; defaults to a fresh unique value')
    parser.add_argument('--max-facts', type=int, default=5)
    parser.add_argument('--health-only', action='store_true', help='Only call /healthcheck')
    parser.add_argument('--no-cleanup', dest='cleanup', action='store_false', help='Keep the smoke group after the run')
    parser.set_defaults(cleanup=True)
    args = parser.parse_args()
    asyncio.run(_run(args))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
