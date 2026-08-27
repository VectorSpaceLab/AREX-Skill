# Action Masking and Rendering

Built-in environments vary in what they expose through `info`, `metadata`, and render modes. Inspect the live environment instead of assuming every discrete environment supports the same mask or renderer.

## Taxi Action Masks

`Taxi-v4` returns `info["action_mask"]` from both `reset()` and `step()`. The mask is a binary array with one element per discrete action:

- `1` means the action changes the state or is otherwise valid for the current state.
- `0` means the action is a wall collision, invalid pickup/dropoff, or another no-op/invalid move for that state.
- Taxi actions are `0` south, `1` north, `2` east, `3` west, `4` pickup, and `5` dropoff.

Safe random masked action pattern:

```python
import gymnasium as gym

env = gym.make("Taxi-v4")
obs, info = env.reset(seed=123)
mask = info.get("action_mask")
action = env.action_space.sample(mask) if mask is not None else env.action_space.sample()
obs, reward, terminated, truncated, info = env.step(action)
env.close()
```

NumPy fallback when you need explicit valid action IDs:

```python
import numpy as np

valid_actions = np.flatnonzero(mask == 1)
if len(valid_actions) == 0:
    action = env.action_space.sample()
else:
    action = int(valid_actions[0])
```

Q-value masking pattern:

```python
valid_actions = np.flatnonzero(info["action_mask"] == 1)
best_action = int(valid_actions[np.argmax(q_values[obs, valid_actions])])
```

Important cautions:

- Do not assume masks exist for all discrete environments. Use `mask = info.get("action_mask")` unless the task is specifically Taxi.
- The mask describes current-state action validity; refresh it after every `step()` because it changes with the state.
- If a masked policy reaches a terminal or truncated state, reset before reading a new actionable mask.
- Action masks are environment-specific `info` data, not a generic `spaces.Discrete` feature.

## Bundled Mask Smoke Script

From this sub-skill directory:

```bash
python scripts/action_mask_smoke.py --help
python scripts/action_mask_smoke.py --steps 5 --seed 123
```

From the root Gymnasium skill directory:

```bash
python sub-skills/builtin-envs/scripts/action_mask_smoke.py --steps 5 --seed 123
```

Expected signal includes the environment ID, initial observation, mask values, selected valid actions, rewards, and termination/truncation flags.

## Render Mode Selection

Render mode is selected when the environment is created, not as an argument to `render()`:

```python
import gymnasium as gym

env = gym.make("CartPole-v1", render_mode="rgb_array")
obs, info = env.reset(seed=123)
frame = env.render()
env.close()
```

Inspect supported modes:

```python
env = gym.make("Taxi-v4")
print(env.metadata.get("render_modes", []))
env.close()
```

Common modes:

| Mode | Meaning | Notes |
| --- | --- | --- |
| `None` | No rendering | Best for training and CI smoke tests |
| `human` | Draw to a window or viewer | Needs display support and often `pygame-ce` or MuJoCo OpenGL |
| `rgb_array` | Return an image array | Best for tests, videos, and headless frame capture |
| `ansi` | Return text | Available on selected Toy Text envs |
| `rgb_array_list` | Collect frame lists through wrapper behavior | More wrapper-specific; route complex recording to wrappers |
| `depth_array`, `rgbd_tuple` | MuJoCo depth/RGBD outputs | Requires MuJoCo renderer and OpenGL backend support |

## Family Rendering Notes

- Classic Control: usually `human` and `rgb_array`; install `gymnasium[classic-control]` for `pygame-ce` rendering.
- Toy Text: selected envs support `ansi`, `human`, and/or `rgb_array`; install `gymnasium[toy-text]` for graphical rendering.
- Box2D: `human` and `rgb_array` depend on Box2D plus `pygame-ce`.
- MuJoCo: many envs support `human`, `rgb_array`, `depth_array`, and `rgbd_tuple`; choose `MUJOCO_GL=egl` or `MUJOCO_GL=osmesa` for headless systems when appropriate.
- Atari/ALE: render modes and preprocessing depend on the ALE plugin environment and ROM setup.

## Rendering Versus Recording

Rendering returns or displays frames. Recording writes media files and has additional dependencies and wrapper-order requirements.

- For one frame, create with `render_mode="rgb_array"` and call `env.render()`.
- For video recording, create with image-returning rendering and use `RecordVideo`; `moviepy` comes from `gymnasium[other]`.
- If `moviepy` is missing, route to `../wrappers-recording/SKILL.md` rather than installing broad simulator extras.

## Headless CI Tips

- Prefer `render_mode=None` for backend smoke tests unless the task is specifically rendering.
- Prefer `render_mode="rgb_array"` over `human` in CI.
- For `pygame` render tests in headless Linux, callers often set dummy SDL drivers before import/use:

```bash
SDL_VIDEODRIVER=dummy SDL_AUDIODRIVER=dummy python your_smoke.py
```

- For MuJoCo, set `MUJOCO_GL` before Python starts if the default windowed backend is unavailable.
