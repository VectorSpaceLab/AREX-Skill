# PettingZoo Troubleshooting

Use this root guide for cross-cutting PettingZoo failures. For workflow-specific details, follow the linked sub-skill references.

## Import And Install Failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError: pettingzoo` | Package is not installed in the active Python. | Install `pettingzoo`, then run `python -c "import pettingzoo; print(pettingzoo.__version__)"`. |
| `ModuleNotFoundError: numpy` or `gymnasium` | Base dependencies are absent or the wrong Python is active. | Reinstall base PettingZoo in the active environment; do not assume another environment's install is visible. |
| `ModuleNotFoundError: pygame` while importing Classic/Butterfly/SISL | Missing optional family extra. | Install the smallest matching extra, such as `pettingzoo[classic]` or `pettingzoo[butterfly]`; read [installation-and-extras.md](installation-and-extras.md). |
| `ModuleNotFoundError: rlcard`, `chess`, or `shimmy` | Classic extra is missing or incomplete. | Install `pettingzoo[classic]`; retry a safe import probe before running training. |
| `ModuleNotFoundError: multi_agent_ale_py` | Atari extra is missing. | Install `pettingzoo[atari]`; handle ROMs separately. |
| `ModuleNotFoundError: pymunk`, `Box2D`, or `scipy` | Butterfly/SISL dependency mismatch. | Install the family extra and check system build prerequisites if wheels are unavailable. |

## Atari ROM Failures

Installing `pettingzoo[atari]` does not install ROM files. If an Atari constructor fails with a missing ROM or ALE resource error:

1. Confirm `pettingzoo[atari]` imports successfully.
2. Acquire ROMs through an approved AutoROM workflow or pass a valid `rom_path`/`auto_rom_install_path` when supported.
3. Keep ROM acquisition out of default automated checks because it can involve downloads, licenses, and filesystem state.

Read [sub-skills/environment-families/references/troubleshooting.md](../sub-skills/environment-families/references/troubleshooting.md) for family-specific details.

## API Loop Failures

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `AttributeError` accessing `agents`, `rewards`, `terminations`, or `agent_selection` | `reset()` has not been called or `OrderEnforcingWrapper` is protecting call order. | Call `env.reset(seed=...)` before `agent_iter`, `last`, `step`, `observe`, `render`, or state access. |
| `ValueError: when an agent is dead, the only valid action is None` | AEC loop stepped a terminated/truncated agent with a real action. | In AEC loops, use `action = None` whenever `termination or truncation` is true. |
| Code expects `done` | PettingZoo uses Gymnasium-style `termination` and `truncation`. | Treat episode completion as `termination or truncation`; keep the two flags separate when debugging. |
| Masked sampling fails | Mask is missing, wrong shape, wrong dtype, or all zeros. | Check both observation dict and info dict for `action_mask`; verify it matches the discrete action space. |

Read [sub-skills/use-environments/references/troubleshooting.md](../sub-skills/use-environments/references/troubleshooting.md) for rollout-level fixes.

## Custom Environment Failures

Common `api_test` and `parallel_api_test` failures usually come from:

- Recreating spaces on every `observation_space(agent)` or `action_space(agent)` call instead of returning stable objects.
- Returning dict keys for dead agents or omitting live agents in Parallel `step` output.
- Not updating `agents` after terminations/truncations.
- Returning a value from AEC `step`, which should return `None`.
- Missing `_cumulative_rewards`, `terminations`, `truncations`, `infos`, or `agent_selection` after reset.
- Non-deterministic reset/action-space seeding.

Read [sub-skills/custom-environments/references/troubleshooting.md](../sub-skills/custom-environments/references/troubleshooting.md) and [sub-skills/testing-and-validation/references/troubleshooting.md](../sub-skills/testing-and-validation/references/troubleshooting.md).

## Wrapper And Conversion Failures

- `aec_to_parallel` asserts when the AEC env cannot safely be interpreted as simultaneous-cycle updates or lacks `metadata["is_parallelizable"] = True`.
- PettingZoo utility wrappers are AEC-oriented; for Parallel envs, use conversion wrappers deliberately or `BaseParallelWrapper` for pass-through behavior.
- Illegal-action termination requires a valid action mask for the current agent.
- `CaptureStdoutWrapper` is for terminal-rendering environments, especially `ansi` style output.

Read [sub-skills/wrappers-and-utilities/references/troubleshooting.md](../sub-skills/wrappers-and-utilities/references/troubleshooting.md).

## Render And Headless Failures

- Avoid `render_mode="human"` in headless CI or remote sessions unless display forwarding is configured.
- Prefer no render mode, `ansi`, or `rgb_array` for automated checks.
- `human` render methods should return `None`; `rgb_array` should return an image array; `ansi` should return a string.
- Always call `close()` when leaving an environment loop, especially after GUI or physics environments.

## Training Integration Failures

Framework tutorials often require packages outside PettingZoo extras. Missing `torch`, `tianshou`, `stable_baselines3`, `ray`, `agilerl`, `supersuit`, or `langchain` should be handled as framework dependency planning, not as a PettingZoo family install issue.

Read [sub-skills/training-integrations/references/troubleshooting.md](../sub-skills/training-integrations/references/troubleshooting.md) before running long training, GPU, display, network, or credential-dependent examples.
