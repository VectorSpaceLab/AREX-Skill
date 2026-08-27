# Hyperparameter file patterns

RL Zoo configs are intentionally small dictionaries with some Python-expression escape hatches. Prefer editing the smallest env-specific entry or adding a clear `default` fallback rather than copying a whole algorithm file.

## Algorithm file families

Canonical algorithm YAML names used by RL Zoo include:

- On-policy and contrib: `a2c.yml`, `ppo.yml`, `ppo_lstm.yml`, `trpo.yml`, `ars.yml`.
- Off-policy: `ddpg.yml`, `dqn.yml`, `sac.yml`, `td3.yml`, `crossq.yml`, `qrdqn.yml`, `tqc.yml`.
- Goal/HER reference: `her.yml` is retained as reference material for older HER-style configs; current off-policy configs may instead use `HerReplayBuffer` through `replay_buffer_class` and `replay_buffer_kwargs`.
- Python config example pattern: a Python file/module can define `hyperparams = {"EnvId-vN": dict(...)}` and can import Python objects needed by `policy_kwargs`.

The file name convention is algorithm-owned: `--algo ppo` normally loads a PPO config unless `--conf-file` points elsewhere. The config root is still keyed by environment id or fallback entries.

## Required entry shape

A complete entry should include at least:

```yaml
CartPole-v1:
  n_timesteps: !!float 1e5
  policy: 'MlpPolicy'
```

A portable fallback config should add `default`:

```yaml
default:
  n_timesteps: !!float 1e6
  policy: 'MlpPolicy'

CartPole-v1:
  n_timesteps: !!float 1e5
  policy: 'MlpPolicy'
  n_envs: 8
  learning_rate: lin_0.001
  clip_range: lin_0.2
```

For Atari fallback entries, use an image policy and Atari/frame stacking wrappers:

```yaml
atari:
  env_wrapper:
    - stable_baselines3.common.atari_wrappers.AtariWrapper
  frame_stack: 4
  policy: 'CnnPolicy'
  n_timesteps: !!float 1e7
  learning_rate: lin_2.5e-4
```

`default` is not used for Atari envs when an `atari` entry is required; exact env-id entries still win first.

## Reusable YAML patterns

### Linear schedules

Use `lin_<float>` strings for keys that RL Zoo preprocesses as schedules:

```yaml
learning_rate: lin_7.3e-4
clip_range: lin_0.2
```

Use plain YAML numbers when you want a constant schedule:

```yaml
learning_rate: !!float 3e-4
clip_range: 0.2
```

### Normalization

Boolean form uses VecNormalize defaults plus the algorithm gamma when present:

```yaml
normalize: true
gamma: 0.99
```

Dict/expression form customizes observation/reward normalization:

```yaml
normalize: "{'norm_obs': True, 'norm_reward': False}"
```

### Policy kwargs

Either a YAML mapping for literal values:

```yaml
policy_kwargs:
  net_arch: [64, 64]
  ortho_init: false
```

or a Python-expression string when you need names imported by the training module, such as `nn.ReLU`:

```yaml
policy_kwargs: "dict(activation_fn=nn.ReLU, net_arch=[256, 256])"
```

### Wrappers and callbacks

One wrapper can be a string:

```yaml
env_wrapper: minigrid.wrappers.FlatObsWrapper
```

Multiple wrappers or callbacks use a list. A kwargs-bearing item must be a single-key mapping:

```yaml
env_wrapper:
  - rl_zoo3.wrappers.FrameSkip:
      skip: 2
  - gymnasium.wrappers.TimeLimit:
      max_episode_steps: 100

vec_env_wrapper: stable_baselines3.common.vec_env.VecMonitor

callback:
  - rl_zoo3.callbacks.ParallelTrainCallback:
      gradient_steps: 256
```

Class implementation and constructor details belong to the custom-components sub-skill; this sub-skill owns only the config syntax and static shape.

### Env and Monitor kwargs

Config file `env_kwargs` is a YAML mapping:

```yaml
env_kwargs:
  gravity: 0.0
```

Monitor kwargs may be a mapping or expression string:

```yaml
monitor_kwargs: "dict(info_keywords=('is_success',))"
```

CLI `--env-kwargs` and `--eval-env-kwargs` do not use YAML. They use StoreDict `key:value` tokens, described in [configuration.md](configuration.md).

### Frame stacking and vector wrappers

Prefer the dedicated `frame_stack` key for VecFrameStack-like behavior:

```yaml
frame_stack: 4
```

Use `vec_env_wrapper` for other vector wrappers. Avoid configuring both `frame_stack` and a `VecFrameStack` `vec_env_wrapper`; wrapper order becomes harder to reason about and may change observation shapes before normalization/stat loading.

## Python config pattern

Python configs must define `hyperparams`. They are useful when you need real Python objects or imports rather than YAML strings:

```python
import torch

hyperparams = {
    "MountainCarContinuous-v0": dict(
        env_wrapper=[{"gymnasium.wrappers.TimeLimit": {"max_episode_steps": 100}}],
        normalize=True,
        n_envs=1,
        n_timesteps=20000.0,
        policy="MlpPolicy",
        batch_size=8,
        n_steps=8,
        policy_kwargs=dict(
            activation_fn=torch.nn.ReLU,
            ortho_init=False,
        ),
    ),
    "default": dict(
        n_timesteps=1000000.0,
        policy="MlpPolicy",
    ),
}
```

Use the validator's default static mode first:

```bash
python scripts/validate_hyperparams_config.py <config.py> --env-id MountainCarContinuous-v0
```

Only use Python execution/import when the file is trusted and static inspection cannot see the final dictionary:

```bash
python scripts/validate_hyperparams_config.py <config.py> --env-id MountainCarContinuous-v0 --import-python
```

## Version and package portability

- Environment ids are exact strings. Gymnasium package upgrades can change versions such as `LunarLander-v2` to `LunarLander-v3` or MuJoCo `Ant-v3` to `Ant-v4`; update config keys and command `--env` together.
- Optional environment families (Atari ROMs, Box2D, MuJoCo, PyBullet, MiniGrid, highway-env, custom packages) must be installed and registered before runtime training can prove the config.
- A static config can be shape-valid while still failing because a wrapper target, callback target, policy path, or optional env package is unavailable. Use [troubleshooting.md](troubleshooting.md) to decide whether to fix syntax here or route to a runtime/import check elsewhere.
