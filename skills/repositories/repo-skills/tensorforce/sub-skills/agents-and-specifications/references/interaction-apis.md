# Interaction APIs

## Purpose

Use this reference when you need to drive a Tensorforce agent manually instead of using `Runner`: non-independent `act`/`observe`, independent evaluation, and offline `experience`/`update`. Use [`agent-specifications.md`](agent-specifications.md) to construct the agent first.

## Interface choices

| Interface | Use when | Core rule |
|---|---|---|
| `Runner` | Standard training/evaluation orchestration. | Route to `../runner-and-cli-workflows/`. |
| `act` + `observe` | You need a custom environment loop but still want online training behavior. | Every non-independent `act` must be followed by exactly one `observe`. |
| `act(independent=True)` | Evaluation, action probing, or collecting external episode traces without online learning side effects. | Use `initial_internals()` for recurrent/internal states; do not call `observe`. |
| `experience` + `update` | You already have full episode traces and want to feed/update manually. | Supply complete episodes ending with terminal `1` or `2`, then call `update()`. |

## Online `act`/`observe` loop

A minimal custom loop:

```python
states = environment.reset()
terminal = False
sum_reward = 0.0
num_updates = 0

while not terminal:
    actions = agent.act(states=states)
    states, terminal, reward = environment.execute(actions=actions)
    num_updates += agent.observe(terminal=terminal, reward=reward)
    sum_reward += reward
```

Important details:

- `agent.act(states=...)` in non-independent mode records the timestep internally. Calling it again before `observe(...)` raises an ordering error.
- `agent.observe(...)` must receive the reward and terminal for the preceding action.
- `observe` returns the number of updates performed by that call. Depending on buffering and algorithm settings, many calls return `0`.
- `terminal=False` or `0` means non-terminal, `terminal=True` or `1` means true terminal, and `terminal=2` marks an aborted/time-limit terminal.
- If `max_episode_timesteps` is set and you exceed it without a terminal, Tensorforce raises an episode-length error.

Run the bundled smoke helper for a safe example:

```bash
python scripts/act_observe_smoke.py --episodes 1 --max-timesteps 3
```

## Independent evaluation/probing

Independent action calls do not append to the agent's online training memory and do not need `observe`.

```python
states = environment.reset()
internals = agent.initial_internals()
terminal = False
sum_reward = 0.0

while not terminal:
    actions, internals = agent.act(
        states=states,
        internals=internals,
        independent=True,
        deterministic=True
    )
    states, terminal, reward = environment.execute(actions=actions)
    sum_reward += reward
```

Notes:

- If you omit `internals`, `act(independent=True)` returns actions only. If you pass `internals`, it returns `(actions, next_internals)`.
- Use `agent.initial_internals()` at the start of every independent episode, especially for recurrent networks.
- `deterministic=True` is intended for independent mode, where it disables sampling/exploration for evaluation-style action selection.
- Independent mode rejects non-zero `parallel` arguments. For batched or parallel online execution, create the agent with sufficient `parallel_interactions` or use `Runner`.

## Offline `experience` + `update` loop

Use this when the task requires collecting an episode trace first and updating later.

```python
episode_states = []
episode_internals = []
episode_actions = []
episode_terminal = []
episode_reward = []

states = environment.reset()
internals = agent.initial_internals()
terminal = False

while not terminal:
    episode_states.append(states)
    episode_internals.append(internals)
    actions, internals = agent.act(
        states=states,
        internals=internals,
        independent=True,
        deterministic=False
    )
    episode_actions.append(actions)
    states, terminal, reward = environment.execute(actions=actions)
    episode_terminal.append(terminal)
    episode_reward.append(reward)

agent.experience(
    states=episode_states,
    internals=episode_internals,
    actions=episode_actions,
    terminal=episode_terminal,
    reward=episode_reward
)
agent.update()
```

Validation rules from the implementation:

- Do not call `experience(...)` while there are incomplete online `act`/`observe` buffers.
- All arrays/lists must have the same number of timesteps as `states`.
- The final `terminal` value must be non-zero; `experience()` requires complete episodes.
- `terminal` booleans are converted to integer terminal codes internally.
- If an agent has no internal states and `internals` is omitted, Tensorforce fills empty internals. Passing `episode_internals` from `initial_internals()` remains a safe pattern.
- Action masks can be included in each stored state using the same `<action-name>_mask` convention as online `act`.
- A few stateful preprocessing/network layers are not correctly updated from independent-mode traces; avoid `exponential_normalization` in this pattern unless you have a separate validation reason.

## Batched and parallel interactions

Tensorforce accepts batched forms for states, rewards, terminals, and parallel indices:

```python
actions = agent.act(states=[state0, state1], parallel=[0, 1])
updates = agent.observe(terminal=[False, True], reward=[0.0, 1.0], parallel=[0, 1])
```

Checklist:

- Create the agent with `parallel_interactions` at least as large as the number of parallel interaction streams, unless `Runner` constructs it for you.
- Keep each `parallel` id's `act`/`observe` sequence balanced.
- For manual batched input, use either `list[dict[state]]` or `dict[name -> batch-array]` consistently.
- If the task requires multiprocessing, socket clients/servers, or `batch_agent_calls`, route to `../runner-and-cli-workflows/` and `../environments-and-interaction/`.

## Action masks during interaction

Masks are consumed inside `act` and `experience` by stripping `<action-name>_mask` entries from the states before the remaining states are validated against the state spec.

Singleton integer action example:

```python
states = dict(
    state=np.asarray([0.1, 0.2], dtype=np.float32),
    action_mask=np.asarray([True, False, True], dtype=bool)
)
action = agent.act(states=states)
```

Named integer action example:

```python
states = dict(
    observation=np.asarray([0.1, 0.2], dtype=np.float32),
    move_mask=np.asarray([True, False, True, True], dtype=bool)
)
actions = agent.act(states=states)
```

Run the bundled mask smoke helper when changing mask guidance:

```bash
python scripts/action_masking_smoke.py --trials 20
```

## Common loop templates

### Online train, then independent evaluate

```python
for _ in range(num_train_episodes):
    states = environment.reset()
    terminal = False
    while not terminal:
        actions = agent.act(states=states)
        states, terminal, reward = environment.execute(actions=actions)
        agent.observe(terminal=terminal, reward=reward)

sum_rewards = 0.0
for _ in range(num_eval_episodes):
    states = environment.reset()
    internals = agent.initial_internals()
    terminal = False
    while not terminal:
        actions, internals = agent.act(
            states=states, internals=internals,
            independent=True, deterministic=True
        )
        states, terminal, reward = environment.execute(actions=actions)
        sum_rewards += reward
```

### Single action probe without learning

```python
internals = agent.initial_internals()
actions, next_internals = agent.act(
    states=states,
    internals=internals,
    independent=True,
    deterministic=True
)
```

Use this for validation or serving-like probes. If the task asks to export a serving artifact, route to `../persistence-export-and-recording/`.
