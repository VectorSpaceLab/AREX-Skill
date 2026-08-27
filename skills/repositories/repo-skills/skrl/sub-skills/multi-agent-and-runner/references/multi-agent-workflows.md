# Multi-agent workflows

This reference describes the public IPPO/MAPPO contract in skrl 2.1.0. It is
about wiring and diagnosis, not a full training recipe. The algorithm classes
are available from `skrl.multi_agents.torch.ippo`,
`skrl.multi_agents.torch.mappo`, `skrl.multi_agents.jax.ippo`, and
`skrl.multi_agents.jax.mappo`.

## Decide IPPO versus MAPPO

| Request characteristic | IPPO | MAPPO |
|---|---|---|
| Training/execution semantics | DTDE: each agent learns from its local observation | CTDE: policies execute locally while the value model can use a centralized state |
| Policy input | `observations[uid]` | `observations[uid]` |
| Value input | Usually the same local observation; an optional state input can be used when the model is built for it | `states[uid]` for a centralized value, normally a common global state copied for every agent by the wrapper |
| Required roles per agent | `policy`; `value` during training | `policy`; `value` during training |
| Algorithm update | One rollout and update per possible agent, with independent critic/optimizer state | One rollout and update per possible agent, with the centralized state used by each value model |

The implementation still stores data per agent. MAPPO does not turn
`models["agent_0"]["value"]` into one global object automatically, and it does
not concatenate other agents' observations for you. The environment wrapper
must expose the intended state and `state_spaces` must describe that state.

Use IPPO when independent local critics are intended. Use MAPPO when the
training-time value estimate should see a global or otherwise centralized
state while the deployed policy must remain observation-local. If a task has
no state at all, use IPPO with observation-based value models, or explicitly
acknowledge that the intended MAPPO centralized critic cannot be represented.
Do not silently call a local observation a centralized state.

## Constructor contract

Torch and JAX signatures are equivalent apart from the device type:

```python
IPPO_or_MAPPO(
    *,
    possible_agents: list[str],
    models: dict[str, dict[str, Model]],
    memories: dict[str, Memory] | None = None,
    observation_spaces: dict[str, gymnasium.Space] | None = None,
    state_spaces: dict[str, gymnasium.Space] | None = None,
    action_spaces: dict[str, gymnasium.Space] | None = None,
    device=None,
    cfg=IPPO_CFG_or_MAPPO_CFG(),
)
```

Prefer passing every space dictionary from the wrapped environment, even when
an algorithm could infer or ignore a field in evaluation. The environment's
`possible_agents` is the authoritative set of keys. It is the complete set of
agents the environment may generate, not merely the current active set
`env.agents`; current active agents can change in PettingZoo-style episodes.

The smallest training shape is:

```python
models = {}
memories = {}
for uid in env.possible_agents:
    models[uid] = {
        "policy": policy_model_for(uid),
        "value": value_model_for(uid),
    }
    memories[uid] = RandomMemory(
        memory_size=cfg_agent.rollouts,
        num_envs=env.num_envs,
        device=env.device,
    )

agent = IPPO_or_MAPPO(
    possible_agents=env.possible_agents,
    models=models,
    memories=memories,
    observation_spaces=env.observation_spaces,
    state_spaces=env.state_spaces,
    action_spaces=env.action_spaces,
    device=env.device,
    cfg=cfg_agent,
)
```

For evaluation, `memories=None` is allowed because no rollout update is
needed. A training call requires a memory for every possible agent and a value
model for every agent that will update. The algorithms iterate over
`possible_agents`; missing nested entries therefore fail as `KeyError` or
later as a missing role/memory error rather than being filled from a single
agent's dictionary.

Model initialization is part of construction. For models made with the public
instantiators, initialize lazy/stateful models before handing them to the
agent; JAX requires the model state dictionary before use, and the native
multi-agent examples explicitly initialize each role. Keep the model's input
expression consistent with its role:

```python
# policy: local observations -> action distribution
# value:  local observations or centralized states -> scalar value
```

The policy distribution must match each `action_spaces[uid]`:

- `Box`: Torch/JAX Gaussian or Torch multivariate Gaussian as appropriate.
- `Discrete`: categorical.
- `MultiDiscrete`: multi-categorical.
- Value: deterministic output `ONE`.

For the model-instantiator syntax, tokens such as `OBSERVATIONS`, `STATES`,
`ACTIONS`, and `ONE` are public and documented. Link to the framework model
guides for the mixin details instead of treating an ordinary single-agent
`dict[str, Model]` as the `dict[str, dict[str, Model]]` required here.

## Shared and separate models

There are two distinct meanings of “shared”:

1. **Shared policy/value model for one agent (Torch Runner/direct setup).**
   `shared_model` can expose two roles over one module. In direct setup, put the
   same object under `models[uid]["policy"]` and `models[uid]["value"]`. This
   is parameter sharing between roles for that one agent.
2. **One policy reused by several agent IDs.** This is not what
   `models.separate: false` means in Runner. Runner loops over
   `possible_agents` and creates a nested model dictionary for each ID. Do not
   claim cross-agent parameter sharing unless you have deliberately constructed
   and validated that object-sharing arrangement and its space compatibility.

Torch's IPPO/MAPPO code handles a shared policy/value object by using one
optimizer and one checkpoint module for the two roles. With separate objects,
it chains policy and value parameters into one optimizer. JAX's Runner
supports separate role models only and does not support the Torch-style shared
role model. The JAX direct algorithms expect policy and value entries, not a
single-agent model dictionary.

## Configuration expansion and per-agent values

`IPPO_CFG` and `MAPPO_CFG` share the same fields. The important update fields
are:

| Field | Meaning and shape |
|---|---|
| `rollouts` | Collection steps between updates; also the conventional memory size when Runner sees `memory_size: -1` |
| `learning_epochs`, `mini_batches` | Update loop counts; scalar or per-agent dictionaries |
| `discount_factor`, `gae_lambda` | GAE discount and lambda; scalar or per-agent dictionaries |
| `learning_rate` | Scalar or `(policy_lr, value_lr)`; may be per-agent |
| `learning_rate_scheduler`, `learning_rate_scheduler_kwargs` | One scheduler or a policy/value pair; kwargs must not provide an `optimizer` key |
| `observation_preprocessor*` | Optional observation preprocessing, per-agent or broadcast from a scalar |
| `state_preprocessor*` | Optional state preprocessing; use this for a centralized state model rather than the old shared-state key |
| `value_preprocessor*` | Optional scalar-value preprocessing |
| `value_clip`, `ratio_clip`, `entropy_loss_scale`, `value_loss_scale`, `kl_threshold`, `grad_norm_clip` | PPO update controls, scalar or per-agent |
| `time_limit_bootstrap` | Whether truncation is bootstrapped, scalar or per-agent |
| `random_timesteps`, `learning_starts`, `rollouts`, `rewards_shaper` | Global/immutable controls during expansion |
| `experiment` | Directory, experiment name, TensorBoard/W&B and checkpoint policy |

At construction, `MultiAgentCfg.expand(possible_agents=...)` broadcasts
scalar values to every agent. A supplied mapping must cover every
`possible_agents` key; an incomplete mapping raises `ValueError` describing
its keys and the expected set. Expansion also turns a scalar learning rate
into a two-element policy/value pair and normalizes scheduler and scheduler
kwargs to policy/value pairs. Configure all agent-specific values with the
same IDs as the environment; do not use list indices or current `agents`.

The config constructor is strict about field names. A misspelled key is not a
silent per-agent override: with a direct dataclass construction it becomes an
unexpected keyword error; with Runner it can surface during config creation.
Use `gae_lambda` in new configurations.

## Interaction and trainer choices

The normal single multi-agent object follows this sequence:

1. `trainer.train()`/a caller sets the agent to training mode.
2. `env.reset()` returns observation and info dictionaries.
3. `env.state()` returns a state dictionary keyed by possible agents (for a
   homogeneous global state, each entry contains the same state).
4. `agent.act(observations, states, timestep=..., timesteps=...)` returns an
   action dictionary and per-agent model outputs.
5. `env.step(actions)` returns observation, reward, terminated, truncated, and
   info dictionaries.
6. `agent.record_transition(...)` stores each agent's transition when training.
7. `agent.post_interaction(...)` performs updates at the configured rollout
   cadence, then writes tracking data/checkpoints at their configured cadence.

`SequentialTrainer` supports one `Agent` or one `MultiAgent` object directly.
`StepTrainer` exposes one iteration at a time and is useful when the caller
owns the outer loop. The Torch `ParallelTrainer` spawns one worker process per
simultaneous list element and is intended for vectorized environments; see
below and the troubleshooting matrix before using it.

### Scope semantics for simultaneous agents

Trainer `agents` can be a list, and `scopes` is a list of **environment counts**
not `(start, stop)` tuples at construction. The base trainer checks:

- `len(scopes) == len(agents)` when scopes are supplied;
- the sum of counts equals `env.num_envs`;
- when omitted, counts are generated as equally as possible, with the final
  count receiving the remainder;
- the number of list agents cannot exceed `env.num_envs`.

The trainer converts counts into contiguous half-open slices such as
`(0, count0)`, `(count0, count0 + count1)`. Each simultaneous agent must have
memory sized for its own scope. A list containing one agent is collapsed to
one agent and receives the full environment scope.

This facility means several agent instances control disjoint slices of one
vectorized environment. It does **not** mean several possible agents inside
one IPPO/MAPPO object are split into independent environments. For a genuine
multi-agent environment, keep its possible-agent dictionaries intact.

The source trainer tests exercise a single multi-agent object with a vectorized
environment. The simultaneous-list multi-agent cases are explicitly skipped
as not implemented in the native trainer tests, and the generic simultaneous
trainer code slices array-like observations rather than a dict per possible
agent. Treat simultaneous lists of `MultiAgent` objects as an unsupported or
custom-trainer boundary until a task-specific integration proves otherwise.
Likewise, sequential and parallel simultaneous execution require
`env.num_envs > 1`; a single non-vectorized environment raises a runtime error
in those branches.

Torch `ParallelTrainer` uses multiprocessing, barriers, queues, and shared
memory for local memories/models. It requires picklable components and has
additional GPU memory overhead. Its native multi-agent simultaneous-list
coverage is not a publication gate. Do not launch a long process merely to
validate a scope shape.
