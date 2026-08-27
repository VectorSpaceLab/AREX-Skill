---
name: agents-and-specifications
description: "Use Tensorforce Agent.create, Agent.load, algorithm aliases,
  state/action specifications, action masking, and low-level act/observe or
  experience/update APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tensorforce Agents and Specifications

Use this sub-skill when a task asks how to construct or load a Tensorforce agent, choose an algorithm alias, write state/action specifications, pass action masks, or drive an agent without `Runner` through `act`, `observe`, `experience`, and `update`.

## Route by task

- **Create or load an agent**: read [`references/agent-specifications.md`](references/agent-specifications.md), then confirm exact public signatures and aliases in [`references/api-reference.md`](references/api-reference.md).
- **Choose between `ppo`, `dqn`, `random`, `tensorforce`, and other aliases**: use the alias table in [`references/api-reference.md`](references/api-reference.md). Route deep network, optimizer, memory, objective, policy, preprocessing, and parameter catalogs to `../modules-and-configuration/`.
- **Write state/action schemas**: use [`references/agent-specifications.md`](references/agent-specifications.md). Route custom environment implementations and adapter spaces to `../environments-and-interaction/`.
- **Use action masking**: read the action-mask section in [`references/agent-specifications.md`](references/agent-specifications.md) and run or adapt [`scripts/action_masking_smoke.py`](scripts/action_masking_smoke.py).
- **Write a manual training/evaluation loop**: read [`references/interaction-apis.md`](references/interaction-apis.md) and run or adapt [`scripts/act_observe_smoke.py`](scripts/act_observe_smoke.py).
- **Diagnose errors**: use [`references/troubleshooting.md`](references/troubleshooting.md) before changing dependencies or agent specs.

## Key operating rules

1. Prefer `Agent.create(..., environment=environment)` when an environment object is already available; Tensorforce then infers `states`, `actions`, and `max_episode_timesteps` where possible.
2. If no environment object is available, pass explicit `states`, `actions`, and any required algorithm arguments. The primitive value spec is `dict(type='bool'|'int'|'float', shape=..., num_values=..., min_value=..., max_value=...)`.
3. For non-independent training, every `agent.act(states=...)` must be followed by exactly one `agent.observe(terminal=..., reward=...)` for the same parallel interaction.
4. For evaluation, offline recording, or externally collected episodes, call `agent.act(..., independent=True)` and use `agent.initial_internals()` when recurrent/internal states are present.
5. Action masks are auxiliary state entries, not part of `states` specs. For a singleton integer action, use `action_mask`; for a named integer action such as `move`, use `move_mask`.
6. Always close agents and environments you created directly. If `Runner` owns construction/closing, route to `../runner-and-cli-workflows/`.

## Boundaries

This sub-skill owns agent creation/loading, algorithm alias selection, state/action specifications, action masking, and low-level interaction APIs. It intentionally excludes Runner orchestration and CLI workflows, custom environment implementation details, persistence/export/recording depth, and exhaustive module catalogs; use the sibling routes named above for those areas.
