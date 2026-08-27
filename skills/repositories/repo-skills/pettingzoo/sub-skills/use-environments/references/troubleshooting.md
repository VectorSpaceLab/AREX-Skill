# Troubleshooting Environment Use

Use this guide for failures while instantiating, resetting, stepping, rendering, masking, or closing PettingZoo environments.

| Symptom | Likely Cause | Fix |
| --- | --- | --- |
| Error says to call `reset()` before `step()`, `last()`, `agent_iter()`, or `render()` | The environment is protected by order-enforcing wrappers or has not initialized live-agent state | Create the env, call `reset(seed=...)`, then enter the AEC or Parallel loop. Keep `render()` after reset unless the environment documents otherwise. |
| `ModuleNotFoundError` or `ImportError` for packages such as `pygame`, `rlcard`, `multi_agent_ale_py`, `pymunk`, `box2d`, `shimmy`, or an Atari/ROM backend | The base PettingZoo install includes core APIs but not every optional environment family dependency | Install the smallest matching optional family extra or dependency set; use `../environment-families/SKILL.md` to choose the right family. |
| A masked random policy raises a mask shape/type error | The mask was read from the wrong location, belongs to a previous agent, or does not match the action space | Recompute the mask on every step from current `info` or current `observation`; check the action space and mask shape before sampling. |
| Mask lookup fails for one environment but works for another | Masks are optional and environment-dependent; some use `observation["action_mask"]`, others use `info["action_mask"]` | Implement a lookup that checks both locations and falls back to unmasked sampling when no mask exists. |
| Mask is all zeros for a live agent | The environment may be in an invalid state, the wrong mask was used, or the policy is treating a terminal state as live | First check `termination or truncation` in AEC; only then use `None`. Otherwise diagnose the environment state or mask source instead of inventing an action. |
| Code uses a single `done` boolean and behaves incorrectly | PettingZoo separates task success/failure termination from time-limit truncation | Replace `done` with `termination, truncation` and treat `termination or truncation` as the control-flow condition. Preserve both dictionaries in Parallel mode. |
| AEC `step(action)` fails after an agent dies | Dead AEC agents require a vacuous `None` action before removal | In the AEC loop, call `env.last()` first and set `action = None` whenever `termination or truncation` is true. |
| Parallel loop sends actions for agents that disappeared | The action dictionary was built from stale observation keys | Build `actions` from current `env.agents` each iteration, not from old `observations` or `possible_agents`. |
| GUI, SDL, display, or window errors | `render_mode="human"` or a graphical environment needs a display backend | Use no render mode for smoke checks, or try `rgb_array`/`ansi` if supported. Use `human` only in an interactive display session. |
| `render()` returns `None` | Human render modes commonly draw to a window and return nothing | Treat `None` as normal for `human`; use `rgb_array` or `ansi` if code needs a returned frame. |
| Process hangs or resources remain after a render run | The rollout did not close the environment after allocating render resources | Always put rollout code in `try/finally` and call `env.close()` in the `finally` block. |
| A smoke script works for a simple environment but fails for Atari, Butterfly, SISL, or Classic | Optional family dependencies, ROMs, display backends, or environment-specific constructor arguments may be missing | Keep the smoke loop bounded and generic, then route dependency and constructor questions to `../environment-families/SKILL.md`. |

## Quick Isolation Checklist

1. Import `pettingzoo` itself and confirm the base package loads.
2. Import the target environment module; if this fails, handle optional family dependencies first.
3. Instantiate with no GUI render mode unless visual output is required.
4. Call `reset(seed=...)` before any step or render calls.
5. For AEC, call `last()` every agent turn and use `None` for terminated or truncated agents.
6. For Parallel, build actions only for current `env.agents`.
7. Close the environment in `finally`.
