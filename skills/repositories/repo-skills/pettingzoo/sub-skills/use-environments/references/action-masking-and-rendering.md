# Action Masking And Rendering

Action masks and render modes are environment-dependent. Write rollouts so they work when masks are absent, when masks live in `observation`, and when masks live in `info`.

## Finding Action Masks

PettingZoo action masks are optional. When present, they are usually exposed as `"action_mask"` in one of two places:

- `info["action_mask"]` for integrations that keep the observation payload separate from validity metadata.
- `observation["action_mask"]` when the observation is a dictionary containing both the observation payload and the mask.

Use this lookup order because it supports both conventions without hardcoding an environment family:

```python
def action_mask_from(observation, info):
    if isinstance(info, dict) and "action_mask" in info:
        return info["action_mask"]
    if isinstance(observation, dict) and "action_mask" in observation:
        return observation["action_mask"]
    return None
```

## Sampling With Masks

For random policies, pass the mask to `action_space(agent).sample(mask)` when the space accepts it.

```python
def sample_masked(action_space, mask):
    if mask is None:
        return action_space.sample()
    try:
        return action_space.sample(mask)
    except TypeError:
        return action_space.sample()
```

Policy code should still validate mask assumptions:

- For a discrete action space, the mask length should match the number of actions and contain at least one valid action.
- For composite spaces, confirm the mask structure matches the Gymnasium space's documented `sample(mask=...)` shape.
- Do not apply a stale mask from a previous agent or previous step.
- Do not choose `None` just because a live agent has an all-zero mask; `None` is valid only for terminated or truncated AEC agents unless the environment explicitly documents otherwise.

## Dead-Agent Action Rules

AEC environments may select agents that have just terminated or truncated so the environment can remove them cleanly.

```python
observation, reward, termination, truncation, info = env.last()
if termination or truncation:
    action = None
else:
    action = policy_or_sample(...)
env.step(action)
```

Parallel environments do not use the same dead-agent `None` step pattern. Build each action dictionary from the current `env.agents` list and omit agents that are no longer live.

## Render Modes

Set the render mode when constructing the environment, not as an argument to `render()`.

```python
env = module.env(render_mode="rgb_array")
# or
env = module.parallel_env(render_mode="ansi")
```

Common modes:

- `None` or no render mode: safest default for headless smoke checks and automated agents.
- `human`: opens or updates a display window when supported; expect failures on machines without a GUI/display.
- `rgb_array`: returns an image-like array from `render()` when supported.
- `ansi`: returns text output for environments that support terminal rendering.

Rendering tips:

- Check `getattr(env, "metadata", {}).get("render_modes", [])` before assuming a mode is supported.
- Call `reset()` before rendering unless the environment explicitly supports pre-reset render.
- Some `human` environments render during `step()` and return `None` from `render()`; this is normal.
- Always call `close()` when a render mode can allocate windows, subprocesses, or graphical resources.

## Headless Safety

For CI, notebooks, remote terminals, and coding-agent smoke checks, prefer no rendering. If visual output is needed without a display, try `rgb_array` or `ansi` first and fall back to no render mode when unsupported.

A safe progression is:

1. Run one bounded rollout with no render mode.
2. Inspect `metadata["render_modes"]`.
3. Try `rgb_array` or `ansi` with a low step budget.
4. Use `human` only when an interactive display is available and the user asked for it.
