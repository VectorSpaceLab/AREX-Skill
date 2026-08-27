# Wrappers And Conversions

PettingZoo wrappers fall into two groups: conversion wrappers that change the environment API shape, and utility wrappers that validate or transform interaction with an environment. For normal rollout loops, keep the loop guidance in `../../use-environments/` as the source of truth; use this reference to decide what to wrap and in what order.

## Conversion Helpers

| Helper | Input | Output | Use when | Key constraint |
| --- | --- | --- | --- | --- |
| `parallel_to_aec(par_env)` | `ParallelEnv` | AEC env wrapped with `OrderEnforcingWrapper` | You authored or received a simultaneous-action environment but need AEC iteration or AEC utility wrappers. | Works for any correct Parallel environment; metadata on the wrapper marks it parallelizable. |
| `aec_to_parallel(aec_env)` | `AECEnv` | `ParallelEnv` | You need Parallel-style batched action dicts from an AEC env. | Requires `aec_env.metadata["is_parallelizable"] == True` and cycle-boundary update semantics. |
| `turn_based_aec_to_parallel(aec_env)` | turn-based `AECEnv` | `ParallelEnv` with one active action per step | You need a Parallel-shaped interface for a turn-based AEC env. | Returned `infos` includes `active_agent`; it is not the same simultaneous-action contract as normal `aec_to_parallel`. |
| `aec_wrapper_fn(par_env_fn)` | Parallel factory | AEC factory | You need an AEC factory from a Parallel factory. | Internally uses `parallel_to_aec` and order enforcement. |
| `parallel_wrapper_fn(env_fn)` | AEC factory | Parallel factory | You need a Parallel factory from an AEC factory. | The AEC factory must produce an env safe for `aec_to_parallel`. |

`aec_to_parallel` unwraps a `parallel_to_aec` result back to the original Parallel environment. `parallel_to_aec` unwraps an `aec_to_parallel` result back to the original AEC environment. This keeps repeated conversions from stacking unnecessary wrappers.

## AEC To Parallel Assumptions

Only use `aec_to_parallel` when all of these are true:

- The AEC environment steps through live agents in a stable cycle.
- Agent death, terminations, and truncations are applied only at cycle boundaries.
- Observations for agents are not updated mid-cycle in a way that Parallel callers would observe earlier than intended.
- Rewards that matter to the Parallel caller are allocated consistently at the end of a cycle, or the user accepts the reward-timing difference.
- `metadata["is_parallelizable"]` is set to `True` by the environment or wrapper after the semantics are verified.

If the assertion mentions that conversion is not generally safe, do not silence it by setting metadata alone. First inspect whether the AEC env updates only once per complete cycle. For authoring details, route to `../../custom-environments/SKILL.md`.

## Utility Wrappers

| Wrapper | Compatible API | Purpose | Typical placement |
| --- | --- | --- | --- |
| `OrderEnforcingWrapper(env)` | AEC | Raises clear errors for `step`, `render`, `observe`, `state`, or `agent_iter` before `reset`; catches missing `step()` calls inside `agent_iter`. | Outermost or near-outermost wrapper for user-facing `env()`. |
| `AssertOutOfBoundsWrapper(env)` | AEC | Asserts that non-dead-agent actions are inside the current agent's action space. | Inside `OrderEnforcingWrapper`, after invalid-action policy wrappers if they transform actions. |
| `ClipOutOfBoundsWrapper(env)` | AEC with `Box` actions for all possible agents | Clips continuous out-of-bounds actions to the action-space bounds and logs a warning; rejects NaN and wrong-shape actions. | For continuous-control AEC envs before order enforcement. |
| `TerminateIllegalWrapper(env, illegal_reward)` | AEC | Ends the game when the current agent chooses an action masked as illegal; assigns `illegal_reward` to that agent. | Use only when observations or infos expose `action_mask`. |
| `CaptureStdoutWrapper(env)` | AEC with `render_mode == "human"` | Converts a print-based human renderer into `render_mode == "ansi"` by capturing stdout as a string. | Before out-of-bounds/order wrappers in default env factories that support `ansi`. |
| `BaseWrapper(env)` | AEC | Delegating base class for custom AEC wrappers. | Subclass, do not use as a behavioral wrapper unless you only need pass-through delegation. |
| `BaseParallelWrapper(env)` | Parallel | Delegating base class for custom Parallel wrappers. | Subclass or use for pass-through instrumentation. |
| `MultiEpisodeEnv(env, num_episodes)` | AEC | Automatically resets an underlying env across several episodes before truncating. | Evaluation-only wrapper; avoid for algorithms that assume Markovian transitions across reset points. |
| `MultiEpisodeParallelEnv(env, num_episodes)` | Parallel | Parallel equivalent of `MultiEpisodeEnv`; reset observations replace terminal observations between internal episodes. | Evaluation-only wrapper with the same non-Markovian reset caveat. |

Most PettingZoo utility wrappers are AEC wrappers. For a Parallel environment that needs AEC-only behavior, convert first:

```python
from pettingzoo.utils import aec_to_parallel, parallel_to_aec
from pettingzoo.utils.wrappers import OrderEnforcingWrapper, AssertOutOfBoundsWrapper

parallel_env = make_parallel_env()
aec_env = parallel_to_aec(parallel_env)
aec_env = AssertOutOfBoundsWrapper(aec_env)
aec_env = OrderEnforcingWrapper(aec_env)
parallel_again = aec_to_parallel(aec_env)  # only if the wrapped AEC env remains parallelizable
```

## Wrapper Ordering Examples

For a typical AEC factory using discrete actions:

```python
env = raw_env(**kwargs)
env = AssertOutOfBoundsWrapper(env)
env = OrderEnforcingWrapper(env)
return env
```

For an action-masked board game that should terminate illegal moves:

```python
env = raw_env(**kwargs)
env = TerminateIllegalWrapper(env, illegal_reward=-1)
env = AssertOutOfBoundsWrapper(env)
env = OrderEnforcingWrapper(env)
return env
```

For print-based text rendering that exposes `ansi`:

```python
internal_render_mode = "human" if render_mode == "ansi" else render_mode
env = raw_env(render_mode=internal_render_mode)
if render_mode == "ansi":
    env = CaptureStdoutWrapper(env)
env = AssertOutOfBoundsWrapper(env)
env = OrderEnforcingWrapper(env)
return env
```

For continuous `Box` actions:

```python
env = raw_env(**kwargs)
env = ClipOutOfBoundsWrapper(env)
env = OrderEnforcingWrapper(env)
return env
```

Do not combine `AssertOutOfBoundsWrapper` and `ClipOutOfBoundsWrapper` for the same continuous action unless the desired behavior is explicit. Asserting rejects invalid actions; clipping mutates them into valid bounds with a warning.

## Parallel Limitations

- AEC utility wrappers assert that their input is an `AECEnv`; applying them directly to a `ParallelEnv` is an error.
- `BaseParallelWrapper` and `MultiEpisodeParallelEnv` are the built-in Parallel wrapper bases; other utility wrappers should be used through conversion or replaced with a custom Parallel wrapper.
- `parallel_to_aec` calls the underlying Parallel `step(actions)` only after all currently live agents in the AEC cycle have supplied actions.
- `aec_to_parallel` calls the underlying AEC `step(action)` once per live agent and accumulates rewards across that cycle.
- If agents are added or removed mid-cycle, conversion behavior may differ from direct AEC behavior. Prefer direct AEC use or a custom Parallel implementation for dynamic-agent designs.

## Multi-Episode Wrappers

`MultiEpisodeEnv` and `MultiEpisodeParallelEnv` are evaluation helpers. They run the base environment for `num_episodes`, automatically resetting between internal episodes, then truncate. This is useful for a single long evaluation stream, but it means the wrapper is no longer Markovian around internal reset boundaries. Do not use these wrappers as a default training environment unless the downstream algorithm explicitly tolerates reset discontinuities.