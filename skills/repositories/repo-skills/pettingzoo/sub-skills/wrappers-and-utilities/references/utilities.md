# Utilities

PettingZoo utility helpers support two audiences: environment implementers and environment users. Keep that distinction clear so future agents do not reach into implementation-only tools during ordinary rollouts.

## Quick Selection

| Utility | Best for | Audience | Notes |
| --- | --- | --- | --- |
| `AgentSelector(agent_order)` | Cycling AEC turn order inside custom environments. | Implementers. | Use `env.agent_iter()` for external interaction instead. |
| `average_total_reward(env, max_episodes=100, max_steps=10000000000)` | Random-policy reward baseline for AEC envs. | End users and evaluators. | Sums rewards across all agents; misleading for zero-sum comparisons. |
| `save_observation(env, agent=None, all_agents=False, save_dir=...)` | Saving image observations from a reset AEC env. | End users and evaluators. | Requires image-like `Box` observations and Pillow. Writes PNG files. |
| `CaptureStdoutWrapper(env)` | Turning print-based `human` rendering into `ansi` string rendering. | Factory authors and end users. | Requires `render_mode == "human"`; wrapper sets `render_mode` to `"ansi"`. |
| `capture_stdout` | Capturing arbitrary stdout in a context manager. | Implementers and test authors. | Lower-level utility used by `CaptureStdoutWrapper`. |
| `EnvLogger` | Standard warnings/errors for environment and wrapper failures. | Implementers and test authors. | Can suppress/flush warnings, but do not hide real contract failures in user guidance. |

## AgentSelector

`AgentSelector` is an implementation aid for AEC environments. It stores an `agent_order`, returns agents with `reset()` and `next()`, and exposes `is_first()` and `is_last()` checks for cycle-boundary reward and observation updates.

Use it when authoring a custom AEC environment that needs stable turn cycling:

```python
from pettingzoo.utils import AgentSelector

self._agent_selector = AgentSelector(self.agents)
self.agent_selection = self._agent_selector.reset()
...
if self._agent_selector.is_last():
    # Resolve simultaneous outcome and accumulate rewards.
self.agent_selection = self._agent_selector.next()
```

Do not use `AgentSelector` to interact with an existing environment from the outside. Use `for agent in env.agent_iter():` and `env.last()` instead; that preserves wrappers, dead-agent handling, and order-enforcement checks.

`agent_selector` with lowercase name is deprecated. Prefer `AgentSelector`.

## average_total_reward

`average_total_reward` runs random actions on an AEC environment until `max_episodes` or `max_steps` is reached, prints `Average total reward ...`, and returns the average.

Use it for a rough smoke baseline:

```python
from pettingzoo.utils import average_total_reward

score = average_total_reward(env, max_episodes=5, max_steps=500)
```

Caveats:

- It expects an AEC env because it calls `env.agent_iter()` and `env.last()`.
- It calls `env.reset()` internally for each episode.
- It handles action masks only when `obs` is a dict containing `"action_mask"`.
- It samples from action spaces otherwise.
- It sums rewards across all agents, so it is not a policy-quality metric for zero-sum or adversarial games.
- It does not close the env; callers should close the env when finished.

## save_observation

`save_observation(env, agent=None, all_agents=False, save_dir=...)` saves one or more current observations as PNG files. The environment must already be reset. If `agent` is omitted, it uses `env.agent_selection`; if `all_agents=True`, it saves for every live agent.

Requirements enforced by assertions:

- The observation space for each requested agent must be `gymnasium.spaces.Box`.
- The space bounds must be exactly 0 to 255.
- The observation shape must be 2D or 3D.
- A 3D observation must have 1 or 3 channels.
- `env.observe(agent)` must not return `None`.
- Pillow must be installed because the helper imports `PIL.Image`.

File behavior:

- The helper creates a subdirectory under `save_dir` named from `str(env)` with angle brackets replaced by underscores.
- It writes one PNG per agent using `<agent>.png` as the filename.
- Because it creates files, pass an explicit scratch `save_dir` in tests or automation rather than relying on the process working directory.

## CaptureStdoutWrapper And capture_stdout

`CaptureStdoutWrapper` is for environments that render by printing to terminal in `human` mode. It captures the output of `render()` and returns it as a string, while exposing `render_mode == "ansi"`.

Typical factory pattern:

```python
internal_render_mode = "human" if render_mode == "ansi" else render_mode
env = raw_env(render_mode=internal_render_mode)
if render_mode == "ansi":
    env = CaptureStdoutWrapper(env)
```

`capture_stdout` is the lower-level context manager:

```python
from pettingzoo.utils.capture_stdout import capture_stdout

with capture_stdout() as stdout:
    print("hello")
text = stdout.getvalue()
```

Use the wrapper for environment rendering. Use the context manager only for implementation tests or one-off utility code.

## EnvLogger

`EnvLogger` centralizes common wrapper warnings and errors, including:

- Action out-of-bounds warnings for clipping.
- Illegal move warnings for `TerminateIllegalWrapper`.
- Errors for `step`, `render`, `observe`, `state`, or `agent_iter` before `reset`.
- Warnings for `step()` after all agents are terminated or truncated.
- NaN action errors.

`EnvLogger.flush()`, `suppress_output()`, and `unsuppress_output()` are useful in tests that assert warnings. Avoid suppressing output in user-facing examples unless the task is specifically about warning capture; warnings often identify real API contract violations.