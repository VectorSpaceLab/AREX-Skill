#!/usr/bin/env python3
"""No-network smoke check for Pydantic AI agent-core APIs.

Usage:
    python agent_smoke.py
    python agent_smoke.py --json

The script imports Pydantic AI, disables live model requests, constructs agents
with TestModel, runs sync and async agent flows, and verifies basic message
history continuation. It is safe to run from any current working directory.
"""

from __future__ import annotations

import argparse
import asyncio
import json
from dataclasses import dataclass
from typing import Any



@dataclass
class SmokeDeps:
    user_name: str


def run_sync_smoke() -> dict[str, Any]:
    agent = Agent(
        'openai:gpt-5.2',
        deps_type=SmokeDeps,
        instructions='Return a deterministic test response.',
        defer_model_check=True,
    )

    @agent.instructions
    def add_user(ctx: RunContext[SmokeDeps]) -> str:
        return f'The user is {ctx.deps.user_name}.'

    with agent.override(model=TestModel(custom_output_text='sync-ok')):
        first = agent.run_sync('hello', deps=SmokeDeps('Ada'))

    with agent.override(model=TestModel(custom_output_text='history-ok')):
        second = agent.run_sync(
            'continue',
            deps=SmokeDeps('Ada'),
            message_history=first.new_messages(),
        )

    if first.output != 'sync-ok':
        raise AssertionError(f'Unexpected first output: {first.output!r}')
    if second.output != 'history-ok':
        raise AssertionError(f'Unexpected second output: {second.output!r}')
    if not first.new_messages():
        raise AssertionError('Expected first run to produce new messages')
    if first.conversation_id != second.conversation_id:
        raise AssertionError('Expected message history continuation to preserve conversation_id')

    return {
        'sync_output': first.output,
        'history_output': second.output,
        'message_count': len(second.all_messages()),
        'conversation_continued': True,
    }


async def run_async_smoke() -> dict[str, Any]:
    agent = Agent(TestModel(custom_output_text='async-ok'))
    result = await agent.run('hello async')
    if result.output != 'async-ok':
        raise AssertionError(f'Unexpected async output: {result.output!r}')
    return {
        'async_output': result.output,
        'requests': result.usage.requests,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description='Run a no-network Pydantic AI Agent/TestModel smoke check.')
    parser.add_argument('--json', action='store_true', help='emit machine-readable JSON instead of text')
    args = parser.parse_args()

    global Agent, RunContext, TestModel, models
    try:
        from pydantic_ai import Agent, RunContext, models
        from pydantic_ai.models.test import TestModel
    except ModuleNotFoundError as exc:
        raise SystemExit(
            'Could not import pydantic_ai. Install Pydantic AI in the active Python environment, then rerun this smoke check.'
        ) from exc

    models.ALLOW_MODEL_REQUESTS = False

    report = {
        'ok': True,
        'sync': run_sync_smoke(),
        'async': asyncio.run(run_async_smoke()),
    }

    if args.json:
        print(json.dumps(report, sort_keys=True))
    else:
        print('Pydantic AI agent-core smoke passed')
        print(f"sync_output={report['sync']['sync_output']}")
        print(f"history_output={report['sync']['history_output']}")
        print(f"async_output={report['async']['async_output']}")

    return 0


if __name__ == '__main__':
    raise SystemExit(main())
