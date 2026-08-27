---
name: simulation-workflows
description: "Run OASIS Reddit, Twitter, custom-platform, manual-action, and
  LLM-action simulations with safe environment lifecycle and model-backend
  guidance."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Simulation Workflows

Use this sub-skill when a task asks a future agent to run or adapt an OASIS
simulation: Reddit-style or Twitter-style runs, custom `Platform` setup,
manual interventions, selected `LLMAction` steps, concurrency controls, or a
small no-credential smoke test.

## Start Here

- For the current async lifecycle and `env.step` action contract, read
  [environment-lifecycle.md](references/environment-lifecycle.md).
- For Reddit, Twitter, hybrid manual/LLM, and custom-platform recipes, read
  [workflows.md](references/workflows.md).
- For CAMEL/OpenAI/VLLM/local-server/DeepSeek model setup, credentials, and
  cost controls, read [model-backends.md](references/model-backends.md).
- For common failures, stale-doc traps, database locks, and provider recovery,
  read [troubleshooting.md](references/troubleshooting.md).
- For a tiny no-LLM check, run or adapt
  [scripts/oasis_manual_smoke.py](scripts/oasis_manual_smoke.py).

## Core Runtime Contract

Use public imports from `oasis` where possible:

```python
from oasis import (
    make, DefaultPlatformType, ActionType, ManualAction, LLMAction,
    AgentGraph, SocialAgent, UserInfo,
)
```

The active environment lifecycle is:

```python
env = make(agent_graph=agent_graph,
           platform=DefaultPlatformType.REDDIT,
           database_path=db_path,
           semaphore=8)
await env.reset()
await env.step(actions)
await env.close()
```

`actions` must be keyed by `SocialAgent` objects, not integer IDs:

```python
actions: dict[SocialAgent, ManualAction | LLMAction | list[ManualAction | LLMAction]]
```

For manual actions, use the source-backed dataclass fields
`ManualAction(action_type=..., action_args={...})`. Some public docs still show
older `EnvAction`/`SingleAction` or `action`/`args` spellings; those names are
not the current package contract.

## Boundary Routing

- Agent profile schema validation, `UserInfo` templates, and `AgentGraph`
  construction details belong to the `agent-profiles` sibling sub-skill.
- Detailed action argument tables, platform/recsys internals, SQLite schema, and
  DB trace analysis belong to `platform-actions`.
- Legacy paper experiment YAMLs, large-scale runs, and post-simulation analysis
  belong to `experiments-analysis`.

Do not run real `LLMAction` steps unless provider credentials, a model with
function/tool-calling support, concurrency limits, and an explicit token/cost
budget are available.
