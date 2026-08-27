# Simulation Workflows

## When To Read

Read this to adapt OASIS into a concrete Reddit, Twitter, custom-platform, or
hybrid manual/LLM simulation. Keep profile schema validation in `agent-profiles`
and detailed action-argument lookup in `platform-actions`.

## No-Credential Manual Smoke

Start with the bundled no-LLM helper before spending tokens or using provider
credentials:

```bash
python sub-skills/simulation-workflows/scripts/oasis_manual_smoke.py --help
python sub-skills/simulation-workflows/scripts/oasis_manual_smoke.py --keep-db
```

The script builds two manual Reddit-style agents, sets a non-secret placeholder
`OPENAI_API_KEY` only if the variable is absent, runs `reset -> step -> step ->
close`, and prints SQLite table counts. It does not execute `LLMAction` or call
any provider.

## Reddit Profile Workflow

Use this shape when the user provides a Reddit JSON profile file and a real or
explicitly chosen CAMEL model backend:

```python
import asyncio
import os
from pathlib import Path

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from oasis import ActionType, DefaultPlatformType, LLMAction, ManualAction, make
from oasis import generate_reddit_agent_graph

async def run_reddit(profile_path: str, db_path: str):
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    available_actions = ActionType.get_default_reddit_actions()
    agent_graph = await generate_reddit_agent_graph(
        profile_path=profile_path,
        model=model,
        available_actions=available_actions,
    )

    db = Path(db_path).resolve()
    os.environ["OASIS_DB_PATH"] = str(db)
    env = make(
        agent_graph=agent_graph,
        platform=DefaultPlatformType.REDDIT,
        database_path=str(db),
        semaphore=8,
    )
    try:
        await env.reset()
        await env.step({
            env.agent_graph.get_agent(0): ManualAction(
                action_type=ActionType.CREATE_POST,
                action_args={"content": "Seed post for the simulation."},
            )
        })
        await env.step({
            agent: LLMAction()
            for _, agent in env.agent_graph.get_agents([1, 2, 3])
        })
    finally:
        await env.close()

asyncio.run(run_reddit("/path/to/reddit_profiles.json", "reddit_sim.db"))
```

Replace the profile path with the user's own data. Do not depend on repository
sample data being present. Validate profile fields through `agent-profiles` if
the file did not come from a trusted OASIS generator.

## Twitter Profile Workflow

Use this shape when the user provides a Twitter CSV profile file. Default
Twitter environments use OASIS's Twitter-like platform preset; LLM-backed steps
require model credentials or a local server.

```python
import asyncio
import os
from pathlib import Path

from camel.models import ModelFactory
from camel.types import ModelPlatformType, ModelType
from oasis import ActionType, DefaultPlatformType, LLMAction, ManualAction, make
from oasis import generate_twitter_agent_graph

async def run_twitter(profile_path: str, db_path: str):
    model = ModelFactory.create(
        model_platform=ModelPlatformType.OPENAI,
        model_type=ModelType.GPT_4O_MINI,
    )
    agent_graph = await generate_twitter_agent_graph(
        profile_path=profile_path,
        model=model,
        available_actions=ActionType.get_default_twitter_actions(),
    )

    db = Path(db_path).resolve()
    os.environ["OASIS_DB_PATH"] = str(db)
    env = make(
        agent_graph=agent_graph,
        platform=DefaultPlatformType.TWITTER,
        database_path=str(db),
        semaphore=8,
    )
    try:
        await env.reset()
        await env.step({
            env.agent_graph.get_agent(0): ManualAction(
                action_type=ActionType.CREATE_POST,
                action_args={"content": "Initial Twitter-style seed post."},
            )
        })
        await env.step({
            agent: LLMAction()
            for _, agent in env.agent_graph.get_agents([1, 3, 5])
        })
    finally:
        await env.close()
```

For a no-download/no-provider dry run, prefer the manual smoke or a custom
platform with a simple recommendation setting before attempting a full
Twitter/VLLM recipe.

## Custom Platform Handoff

Use a custom `Platform` when the user needs explicit recommendation settings,
clock behavior, scoring, or a platform preset that avoids model-heavy optional
paths. The `Platform` object owns its DB path.

```python
from oasis import ActionType, ManualAction, Platform, make
from oasis.clock.clock import Clock
from oasis.social_platform.channel import Channel
from oasis.social_platform.typing import RecsysType

channel = Channel()
platform = Platform(
    db_path=str(db_path),
    channel=channel,
    sandbox_clock=Clock(60),
    recsys_type=RecsysType.RANDOM,
    refresh_rec_post_count=2,
    max_rec_post_len=5,
    following_post_count=2,
    show_score=False,
    allow_self_rating=False,
)

env = make(agent_graph=agent_graph, platform=platform, semaphore=4)
```

After creating the environment, use the same `await env.reset()`,
`await env.step(actions)`, and `await env.close()` lifecycle. Route detailed
`Platform` and recsys semantics to `platform-actions`.

## Mixing Manual And LLM Actions

A single step can activate only selected agents and mix manual and LLM values:

```python
actions = {
    env.agent_graph.get_agent(0): ManualAction(
        action_type=ActionType.CREATE_POST,
        action_args={"content": "A controlled message."},
    ),
    env.agent_graph.get_agent(1): LLMAction(),
    env.agent_graph.get_agent(2): [
        ManualAction(action_type=ActionType.FOLLOW,
                     action_args={"followee_id": 0}),
        LLMAction(),
    ],
}
await env.step(actions)
```

If one action needs a DB row produced by another action, split the actions into
multiple awaited steps because actions inside one step are scheduled
concurrently.

## Concurrency And Budget Workflow

1. Run the bundled manual smoke first.
2. Decide provider/server and create a CAMEL model backend; see
   [model-backends.md](model-backends.md).
3. Restrict `available_actions` to the actions the task actually needs.
4. Activate a small subset of agents with `env.agent_graph.get_agents([...])`.
5. Set `semaphore` conservatively for the provider or local server.
6. Estimate cost before increasing agent count, activation probability, or time
   steps. Token use scales with all three.
7. Close the environment even on provider errors so the DB is not left locked.

Credentialed OpenAI, DeepSeek, VLLM, group-chat, interview, report, and
large-scale experiment examples should be treated as recipes to adapt, not as
default smoke tests.
