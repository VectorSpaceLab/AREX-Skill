# Troubleshooting Wrappers And Utilities

Use this guide when a wrapper, conversion helper, or utility fails. For basic rollout-loop mistakes, route to `../../use-environments/SKILL.md`; for custom environment implementation defects, route to `../../custom-environments/SKILL.md`; for formal compliance checks, route to `../../testing-and-validation/SKILL.md`.

## `aec_to_parallel` Assertion Fails

Typical message: converting from AEC to Parallel is not generally safe and the environment should set `metadata["is_parallelizable"] = True`.

Checklist:

1. Confirm the env is truly cycle-based: each live agent acts exactly once per environment cycle.
2. Confirm observations and rewards are not semantically updated until the full cycle is complete.
3. Confirm terminations and truncations are applied at cycle boundaries, not in the middle of another agent's cycle.
4. Check `env.metadata.get("is_parallelizable")`; only set it to `True` after the semantics above are true.
5. If the env is turn-based and only one agent is active per step, consider `turn_based_aec_to_parallel` or keep the AEC API.
6. If the env came from a Parallel env via `parallel_to_aec`, call `aec_to_parallel` on that wrapper to recover the original Parallel env rather than stacking conversions.

A second assertion may mention `expected agent ... got agent ...` or death only at the end of a cycle. That means the wrapper entered a Parallel step expecting one full ordered AEC cycle, but `agent_selection` moved unexpectedly or an agent died mid-cycle. Fix the underlying AEC turn/death logic rather than catching the assertion.

## `parallel_to_aec` Looks Stuck Or Delays Rewards

`parallel_to_aec` buffers actions until all live agents in the AEC cycle have acted. It calls the underlying Parallel `step(actions)` only when the selector reaches the last live agent. Therefore:

- Rewards and observations from the Parallel step appear after the last agent in the AEC cycle acts.
- Early agents may see old observations until the cycle resolves.
- Dead-agent handling still requires `None` actions when the AEC wrapper reports termination or truncation.
- If `reset()` returned an empty or malformed `infos` dict, the wrapper may warn and duplicate info entries for current agents.

If that behavior is wrong for the task, use the native Parallel API directly.

## OrderEnforcingWrapper Errors

| Symptom | Cause | Fix |
| --- | --- | --- |
| `reset() needs to be called before step.` | The env was stepped before `reset`. | Call `env.reset(seed=...)` before `step`, `last`, `render`, `observe`, `state`, or `agent_iter`. |
| `<attribute> cannot be accessed before reset` | Accessed `agents`, `rewards`, `terminations`, `truncations`, `infos`, `agent_selection`, or `num_agents` too early. | Reset first, then inspect runtime attributes. |
| `need to call step() or reset() in a loop over agent_iter` | The loop advanced to the next agent without calling `env.step(action)`. | In every `agent_iter` iteration, call `env.step(action)` or `env.step(None)` for terminated/truncated agents. |
| Warning: `step() called after all agents are terminated or truncated` | The loop kept stepping after `env.agents` was empty. | Stop the loop or call `reset()` for a new episode. |

Keep `OrderEnforcingWrapper` near the outside of a user-facing wrapper stack so its messages reflect the final environment the user calls.

## Wrapper State Shadowing

`BaseWrapper.__getattr__` delegates attributes to the wrapped environment, but wrapper methods can accidentally create shadow attributes on the wrapper if they assign state directly. A known regression pattern is `TerminateIllegalWrapper` or another wrapper ending a game and leaving wrapper-level `agent_selection` out of sync with the base env.

Diagnosis:

- Walk the wrapper chain through `.env` until `.unwrapped` and compare any explicit `__dict__["agent_selection"]` values.
- Only the unwrapped env should own core mutable AEC state unless a wrapper intentionally mirrors it.
- If wrapper and base env selections differ after an illegal move or reset, inspect wrapper ordering and any direct state assignment.
- Prefer calling base env methods that update the unwrapped state consistently, or use `env.unwrapped` intentionally when a wrapper must alter core state.

The repository's wrapper tests include a regression check that runs a `TerminateIllegalWrapper` game twice and asserts agent-selection values remain aligned; optional environment dependencies may be needed to execute that native test.

## Illegal Action Termination

`TerminateIllegalWrapper` requires an action mask for the current observation:

- If the observation is a dict, it must contain `observation["action_mask"]`.
- If the observation is not a dict, `info["action_mask"]` must exist.
- The chosen action indexes into the mask; false/zero means illegal.
- On illegal action, all agents are marked terminated/truncated, all rewards are zero except the illegal actor receives `illegal_reward`, rewards are accumulated, and dead-agent stepping begins.

Common fixes:

- Add or preserve the action mask in `observe(agent)` or `infos[agent]` before applying the wrapper.
- Do not wrap environments that lack masks with `TerminateIllegalWrapper`.
- Make sure mask length matches the discrete action space size.
- If the invalid action is outside the action space, use `AssertOutOfBoundsWrapper` to catch that separately.

## Clipping Or Asserting Out-Of-Bounds Actions

`AssertOutOfBoundsWrapper` is for any AEC action space and raises `action is not in action space` unless the current agent is dead and action is `None`.

`ClipOutOfBoundsWrapper` is only for AEC environments where every possible agent has a `Box` action space. It:

- Rejects NaN actions.
- Asserts that action shape matches the `Box` shape.
- Logs a warning and clips values to `[low, high]`.
- Passes `None` through only for terminated/truncated agents.

Choose one policy: assert for strict validation, clip for continuous-control tolerance. Do not use clipping to hide a policy that emits wrong-shaped or NaN actions.

## Missing Render Or Reset

`CaptureStdoutWrapper` asserts that the env has a `render_mode` attribute and that the active mode is `"human"`. To expose ANSI text rendering, create the raw env with internal human rendering, then wrap it only when the requested public mode is `"ansi"`.

If `render()` itself fails before reset, this is usually `OrderEnforcingWrapper` doing its job. Reset before rendering, or route to `../../use-environments/SKILL.md` for lifecycle guidance.

## `save_observation` Fails Or Writes Unexpected Files

Common failures:

- `Observations must be Box`: the observation space is discrete, dict, tuple, or another non-image type.
- `Observations must be 0 to 255`: the helper saves image-like uint8 observations only.
- `Observations must be 2D or 3D`: vector observations cannot be saved as images.
- `3D observations can only have 1 or 3 channels`: channel count is not image-compatible.
- `Observation must be different than None`: the requested agent has no current observation.
- `ModuleNotFoundError: PIL`: install the optional image dependency used by Pillow before running this helper.

Output behavior:

- Always call `env.reset()` first.
- Pass an explicit `agent` unless the current `env.agent_selection` is definitely the desired agent.
- Pass `all_agents=True` only when every live agent has image observations.
- Pass a scratch `save_dir` in automation; the helper creates a subdirectory named from `str(env)` and writes `<agent>.png` files.

## Native Wrapper Tests

The source repository has wrapper tests covering multi-episode wrappers and the `TerminateIllegalWrapper` state regression. These tests instantiate optional Classic and Butterfly environments, so they should be treated as native verification candidates only when matching optional dependencies are installed. For generated skill smoke checks, prefer the bundled `scripts/wrapper_conversion_smoke.py`, which uses only base PettingZoo, Gymnasium, and NumPy.