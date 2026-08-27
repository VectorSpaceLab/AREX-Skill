# Environment Lifecycle

## When To Read

Read this before constructing an OASIS environment, calling `env.step`, or
adapting older examples. It captures the current runtime contract verified from
OASIS source and public examples.

## Public Imports

Prefer package-level exports for common simulation code:

```python
from oasis import (
    make, DefaultPlatformType, ActionType, ManualAction, LLMAction,
    AgentGraph, SocialAgent, UserInfo,
)
```

Profile-file helpers such as `generate_reddit_agent_graph` and
`generate_twitter_agent_graph` are useful for full profile workflows, but
profile schemas and validators are owned by the `agent-profiles` sub-skill.

## Database Path And Process State

- `DefaultPlatformType.REDDIT` and `DefaultPlatformType.TWITTER` require a
  `database_path` argument to `make(...)`.
- Use an absolute path for the SQLite database when possible.
- Set `OASIS_DB_PATH` to the same path before steps that read environment state;
  OASIS helper methods use this variable when they need to reopen the DB.
- OASIS creates `./log` files in the process current working directory during
  imports/environment setup. Run smoke tests from a disposable directory when
  you do not want logs beside project files.

```python
import os
from pathlib import Path

db_path = Path("simulation.db").resolve()
os.environ["OASIS_DB_PATH"] = str(db_path)
```

## Construct The Agent Graph

A minimal manual graph can be built without profile files:

```python
available_actions = [
    ActionType.CREATE_POST,
    ActionType.CREATE_COMMENT,
    ActionType.FOLLOW,
    ActionType.DO_NOTHING,
]

agent_graph = AgentGraph()
for agent_id, user_name, name in [(0, "alice", "Alice"), (1, "bob", "Bob")]:
    agent = SocialAgent(
        agent_id=agent_id,
        user_info=UserInfo(
            user_name=user_name,
            name=name,
            description=f"{name} is a safe manual-smoke user.",
            profile=None,
            recsys_type="reddit",
        ),
        agent_graph=agent_graph,
        model=None,
        available_actions=available_actions,
    )
    agent_graph.add_agent(agent)
```

Current CAMEL-backed `SocialAgent(model=None)` construction may still require a
non-empty `OPENAI_API_KEY` because the default model backend is OpenAI. For a
manual-only smoke, a non-secret placeholder is acceptable only if no
`LLMAction` is executed. For real LLM steps, supply real provider credentials
or an explicit non-OpenAI model backend; see [model-backends.md](model-backends.md).

## Create, Reset, Step, Close

Use `try/finally` so the platform task exits and the SQLite connection closes:

```python
env = make(
    agent_graph=agent_graph,
    platform=DefaultPlatformType.REDDIT,
    database_path=str(db_path),
    semaphore=8,
)
try:
    await env.reset()          # starts platform task and signs up agents
    await env.step(actions)    # updates rec table, then performs actions
finally:
    await env.close()          # sends EXIT, waits for platform, closes DB
```

For a custom `Platform` instance, pass `platform=platform`. The platform's own
`db_path` is authoritative; do not pass a different `database_path` value.

## Current `env.step` Action Mapping

The active source signature is conceptually:

```python
dict[SocialAgent, ManualAction | LLMAction | list[ManualAction | LLMAction]]
```

Keys are the `SocialAgent` objects themselves:

```python
alice = env.agent_graph.get_agent(0)
bob = env.agent_graph.get_agent(1)
```

Manual values use the dataclass fields `action_type` and `action_args`:

```python
await env.step({
    alice: ManualAction(
        action_type=ActionType.CREATE_POST,
        action_args={"content": "Hello from a manual smoke."},
    ),
})

await env.step({
    bob: [
        ManualAction(
            action_type=ActionType.CREATE_COMMENT,
            action_args={"post_id": 1, "content": "Reply from Bob."},
        ),
        ManualAction(
            action_type=ActionType.FOLLOW,
            action_args={"followee_id": 0},
        ),
    ],
})
```

`LLMAction()` values ask the agent's CAMEL model backend to choose a tool/action
from the agent's `available_actions` plus any external tools:

```python
await env.step({
    agent: LLMAction()
    for _, agent in env.agent_graph.get_agents([1, 3, 5])
})
```

## Stale Documentation Trap

Some public simulation pages describe `EnvAction`, `SingleAction`, or
`ManualAction(action=..., args=...)`. The current package export and source use
`ManualAction(action_type=..., action_args={...})`, `LLMAction()`, and an action
mapping keyed by `SocialAgent`. If code fails to import `EnvAction` or rejects
`action`/`args`, switch to the mapping above.

## Ordering And Concurrency

Within one `env.step`, OASIS gathers manual and LLM tasks concurrently. A list
of actions for the same agent is accepted, but the source does not provide a
serial dependency guarantee. If an action depends on a previous action's side
effect, split them into separate awaited steps:

```python
await env.step({alice: ManualAction(ActionType.CREATE_POST, {"content": "A"})})
await env.step({bob: ManualAction(ActionType.CREATE_COMMENT,
                                  {"post_id": 1, "content": "B"})})
```

The `semaphore` argument limits concurrent LLM requests only. Manual actions may
still run concurrently inside the step.

## Safe Validation Signals

After `env.close()`, open the SQLite database and check small table counts such
as `user`, `post`, `comment`, `follow`, and `trace`. The bundled
[manual smoke script](../scripts/oasis_manual_smoke.py) performs this check
without provider calls.
