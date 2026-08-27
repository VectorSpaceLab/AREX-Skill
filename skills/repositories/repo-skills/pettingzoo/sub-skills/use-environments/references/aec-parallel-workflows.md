# AEC And Parallel Workflows

PettingZoo exposes two interaction styles. AEC environments step one selected agent at a time; Parallel environments step all currently live agents together. The two APIs return different values from `reset()` and `step()`, so do not write one Gymnasium-style loop and reuse it unchanged for both.

## AEC Lifecycle

Use an AEC factory, usually named `env`, when agents act sequentially or when an environment is naturally turn-based.

```python
from pettingzoo.classic import rps_v2

env = rps_v2.env(render_mode=None)
try:
    env.reset(seed=42)

    for agent in env.agent_iter(max_iter=1_000):
        observation, reward, termination, truncation, info = env.last()

        if termination or truncation:
            action = None
        else:
            mask = action_mask_from(observation, info)
            action_space = env.action_space(agent)
            action = sample_action(action_space, mask)

        env.step(action)
finally:
    env.close()
```

Key AEC facts:

- `reset(seed=None, options=None)` returns `None` and prepares the environment before `last()`, `step()`, `render()`, or `agent_iter()` use.
- `agent_iter(max_iter=2**63)` yields the current `agent_selection`; the loop ends when there are no live agents or the iterator budget is exhausted.
- `last(observe=True)` returns `(observation, reward, termination, truncation, info)` for the selected agent.
- `step(action)` advances only the selected agent and switches control to the next selected agent.
- If `termination` or `truncation` is true for the selected agent, the only valid action is `None`; this vacuous step lets the environment remove the dead agent.
- `env.agents` contains the current live agents. When it becomes empty, the full environment is done.

## Parallel Lifecycle

Use a Parallel factory, usually named `parallel_env`, when all live agents act simultaneously.

```python
from pettingzoo.butterfly import pistonball_v6

env = pistonball_v6.parallel_env(render_mode=None)
try:
    observations, infos = env.reset(seed=42)

    for _ in range(100):
        if not env.agents:
            break

        actions = {}
        for agent in env.agents:
            observation = observations.get(agent)
            info = infos.get(agent, {})
            mask = action_mask_from(observation, info)
            actions[agent] = sample_action(env.action_space(agent), mask)

        observations, rewards, terminations, truncations, infos = env.step(actions)
finally:
    env.close()
```

Key Parallel facts:

- `reset(seed=None, options=None)` returns `(observations, infos)`, both keyed by agent.
- `step(actions)` accepts an action dictionary keyed by currently live agents and returns `(observations, rewards, terminations, truncations, infos)`.
- Build the action dictionary from `env.agents`, not from stale keys in an older observation dictionary.
- Stop when `env.agents` is empty or when your own bounded step budget is reached.
- Do not send `None` for removed agents in Parallel mode; simply omit agents that are no longer live.

## Shared Helpers

Use a single mask-aware sampler in both APIs.

```python
def action_mask_from(observation, info):
    if isinstance(info, dict) and "action_mask" in info:
        return info["action_mask"]
    if isinstance(observation, dict) and "action_mask" in observation:
        return observation["action_mask"]
    return None


def sample_action(action_space, mask):
    if mask is None:
        return action_space.sample()
    try:
        return action_space.sample(mask)
    except TypeError:
        # Some action spaces do not accept a mask argument.
        return action_space.sample()
```

For production policies, replace `sample_action(...)` with model inference while preserving the same AEC/Parallel control flow and dead-agent rules.

## Seeding And Reproducible Smoke Runs

- Pass a seed into `reset(seed=...)` for the environment RNG.
- If you compare random-action rollouts, also seed each agent action space when supported because `action_space(agent).sample()` uses the space RNG.
- Use stable agent ordering from `possible_agents` when available, falling back to `agents` after reset.

```python
def seed_action_spaces(env, seed):
    agents = list(getattr(env, "possible_agents", []) or getattr(env, "agents", []))
    for index, agent in enumerate(agents):
        try:
            env.action_space(agent).seed(seed + index)
        except Exception:
            pass
```

## Validation Tips

- Treat `termination` and `truncation` separately; either one means the selected AEC agent must step with `None`.
- Keep a hard loop budget during smoke checks so a buggy environment cannot run forever.
- Wrap environment use in `try/finally` and call `close()` even when a rollout raises.
- If the base package imports successfully but a particular environment module fails, suspect a missing optional family dependency rather than a broken PettingZoo core install.
- If you need wrapper or conversion behavior, keep the rollout loop here and read `../wrappers-and-utilities/SKILL.md` for conversion constraints.
