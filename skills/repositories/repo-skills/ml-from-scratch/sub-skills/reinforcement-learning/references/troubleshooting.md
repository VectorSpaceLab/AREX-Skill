# DeepQNetwork troubleshooting

## Quick diagnosis table

| Symptom | Likely cause | Fix |
|---|---|---|
| `module 'numpy' has no attribute 'bool8'` | Older Gym passive checker with NumPy 2.x | Prefer `gym==0.25.2` and `numpy==1.26.4`; for a smoke-only process, the bundled script aliases `np.bool8` to `np.bool_` before importing Gym. |
| Gym warns that it is unmaintained | Upstream Gym deprecation warning | Warning is expected for this educational package; treat it as compatibility context, not a failure by itself. |
| `ValueError: too many values to unpack` from `env.step` | Newer Gym step API returns `(obs, reward, terminated, truncated, info)` | Adapt to old API: `done = terminated or truncated`, then return `(obs, reward, done, info)`. The bundled smoke wraps this. |
| State becomes `(obs, info)` after reset | Newer reset API returns `(obs, info)` | Keep only `obs` before passing state to DQN replay or prediction. |
| `AxisError` or action selection failure around `axis=1` | Package predicts on a 1-D state vector in greedy action selection | Batch the state before prediction: `state_2d = np.asarray(state).reshape(1, -1)`, then call `model.predict(state_2d)`. Keep `epsilon=1.0` for smoke checks that should avoid this path. |
| Dense shape mismatch in first layer | Model builder ignored `n_inputs` | Use `Dense(..., input_shape=(n_inputs,))`; CartPole is normally 4 state values. |
| Target/output shape mismatch, bad Q targets, or action index errors | Model builder final layer does not match `n_outputs` | Use `Dense(n_outputs)` as the final layer; CartPole is normally 2 actions. |
| Render opens no window or fails with display errors | `play` calls `env.render()` in a headless environment | Do not call `play` in CI/agent smoke checks. Use no-render training smoke, or run with an intentional display/Xvfb setup. |
| Rewards vary or training appears unstable | Epsilon-greedy exploration and random replay sampling | Seed `random`, NumPy, and Gym spaces for repeatability; do not expect benchmark-stable curves from this educational implementation. |
| Training is slow | Per-step neural-network updates inside Python loops | Use one epoch and a small max-step wrapper for smoke; reserve longer runs for interactive experiments. |

## Gym and NumPy pins

Supported baseline for this skill is `gym==0.25.x` with NumPy `<2`; the prepared environment used `gym==0.25.2` and `numpy==1.26.4`. Newer Gym/Gymnasium APIs can work only if reset/step outputs are adapted to the older interface expected by `DeepQNetwork.train`.

If the user cannot change package versions, use a local compatibility wrapper in the experiment process:

```python
import numpy as np

if not hasattr(np, "bool8"):
    np.bool8 = np.bool_


def old_reset(env):
    out = env.reset()
    return out[0] if isinstance(out, tuple) and len(out) == 2 else out


def old_step(env, action):
    out = env.step(action)
    if len(out) == 5:
        obs, reward, terminated, truncated, info = out
        return obs, reward, bool(terminated or truncated), info
    return out
```

Use the version pin when possible; use monkey-patching only as a bounded compatibility tactic, not as the preferred installation contract.

## State and action shape checklist

Before training, verify:

```python
assert dqn.n_states == dqn.env.observation_space.shape[0]
assert dqn.n_actions == dqn.env.action_space.n
probe = dqn.model.predict(np.zeros((1, dqn.n_states)))
assert probe.shape == (1, dqn.n_actions)
```

If a user-provided builder returns the wrong shape, trace these two values:

- `n_inputs` controls the first layer input shape.
- `n_outputs` controls the number of Q-values, one per action.

## Epsilon and prediction path

`epsilon=1.0` means the episode uses random actions. That is ideal for smoke checks because it proves replay and `train_on_batch` without exercising greedy prediction. As epsilon decays, greedy predictions become possible; if the raw package path passes a 1-D state into `model.predict`, adapt the state to two dimensions before `argmax(axis=1)`.

## Educational scope limits

This package is useful for understanding a compact DQN loop, not for production RL training. It lacks many framework features: target networks, vectorized environments, checkpointing, wrappers library integration, extensive logging, and benchmark evaluation harnesses. Route requests for generic RL frameworks or modern Gymnasium training stacks outside this sub-skill.
