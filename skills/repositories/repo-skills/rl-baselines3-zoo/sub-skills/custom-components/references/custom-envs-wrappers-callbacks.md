# Custom environments, wrappers, callbacks, schedules, and algorithm patches

This reference is for component work that happens before or around an RL Zoo run. It is intentionally self-contained and uses installed-package entry points. For full configuration-file grammar, use `../../config-hyperparams/SKILL.md`; for launching a run, use `../../training-cli/SKILL.md`.

## Custom Gymnasium environment registration

RL Zoo can only train or evaluate an environment id after Gymnasium knows that id. There are two registration paths:

1. **Explicit package import with `--gym-packages`**: pass one or more importable Python modules. RL Zoo imports them before checking `gym.envs.registry`.

   ```bash
   python -m rl_zoo3.train --algo ppo --env MyEnv-v0 \
     --gym-packages my_envs another_registration_module \
     --conf-file ./my_hyperparams.yml --n-timesteps 1000 --log-folder ./runs/rl-zoo
   ```

   The same pattern applies to installed RL Zoo evaluation commands that expose `--gym-packages`, for example `python -m rl_zoo3.enjoy ... --gym-packages my_envs`.

2. **Conventional `custom_envs` module**: the installed `rl_zoo3.import_envs` module attempts to import a module named `custom_envs` during RL Zoo startup. This is convenient for local experiments, but explicit `--gym-packages` is easier to audit and more portable.

A safe registration package usually keeps all behavior in import-time `register(...)` calls:

```python
# my_envs/__init__.py
from gymnasium.envs.registration import register

register(
    id="MyEnv-v0",
    entry_point="my_envs.my_env:MyEnv",
)
```

Constraints:

- Keep module import deterministic and side-effect-light. Avoid training, downloads, credential reads, GPU allocation, process spawning, or slow simulator construction at import time.
- The environment class should be a Gymnasium `Env`, implement `reset(seed=..., options=...)` and `step(...)`, and expose valid `observation_space` and `action_space`.
- If the env has custom constructor kwargs, pass them through `--env-kwargs` / `--eval-env-kwargs` or config `env_kwargs`; route exact syntax to `../../config-hyperparams/SKILL.md`.
- If RL Zoo reports `MyEnv-v0 not found in gym registry`, first validate that the registration module imports in the same environment and that the id string matches exactly.

## Built-in optional environment imports

At startup, installed `rl_zoo3.import_envs` tries several optional imports and silently skips packages that are absent:

| Module | Runtime meaning | Boundary |
| --- | --- | --- |
| `pybullet_envs_gymnasium` | Registers PyBullet-style environments when installed. | Optional simulator dependency. |
| `ale_py` | Registers Atari/ALE environments through Gymnasium. | Optional Atari dependency; ROM availability is separate. |
| `highway_env` | Registers highway environments and applies a NumPy compatibility alias. | Optional simulator dependency. |
| `custom_envs` | User/local convention for environment registration. | Prefer explicit `--gym-packages` for portability. |
| `gym_donkeycar` | DonkeyCar environments. | Optional simulator dependency. |
| `panda_gym` | Panda robotic manipulation environments. | Optional simulator dependency. |
| `rocket_lander_gym` | Rocket lander environments. | Optional simulator dependency. |
| `minigrid` | MiniGrid environments/wrappers. | Optional simulator dependency. |

The same startup module also registers no-velocity aliases for the supported `MaskVelocityWrapper` ids: `CartPoleNoVel-v1`, `MountainCarNoVel-v0`, `MountainCarContinuousNoVel-v0`, `PendulumNoVel-v1`, `LunarLanderNoVel-v3`, and `LunarLanderContinuousNoVel-v3`.

## Component configuration flow

RL Zoo preprocesses hyperparameters before constructing the model:

1. Schedule strings are converted for selected numeric hyperparameters.
2. `env_wrapper` and `vec_env_wrapper` entries are converted into wrapper callables with `get_wrapper_class(...)`.
3. `callback` entries are converted into callback instances with `get_callback_list(...)`.
4. A dotted `policy` string is imported as a class when it contains a dot.
5. Training-only execution then creates environments, wraps them, and learns the model.

Use the bundled checker to validate the import and constructor layers before step 5:

```bash
python ../scripts/component_import_checker.py \
  --config ./my_hyperparams.yml --env MyEnv-v0 --gym-package my_envs --json
```

The checker does not create environments or train. It cannot prove that a wrapper is semantically valid for a specific environment; it can catch bad imports, missing attributes, malformed wrapper/callback dict entries, and many constructor-kwargs errors.

## Wrapper entries

Minimal wrapper forms accepted by RL Zoo:

```yaml
# One wrapper by dotted import string.
env_wrapper: rl_zoo3.wrappers.HistoryWrapper

# Multiple wrappers, applied top-to-bottom.
env_wrapper:
  - rl_zoo3.wrappers.DelayedRewardWrapper:
      delay: 4
  - rl_zoo3.wrappers.ActionNoiseWrapper:
      noise_std: 0.05

# VecEnv wrapper uses the same parser but must accept a VecEnv.
vec_env_wrapper: stable_baselines3.common.vec_env.VecMonitor
```

Important constraints:

- A wrapper dict item must have exactly one key: the dotted import string or class object. Multiple keys in one dict usually mean bad YAML indentation.
- Regular `env_wrapper` classes must accept the environment as their first constructor argument. The remaining keyword arguments come from the YAML dict.
- `vec_env_wrapper` uses the same syntax but receives a vectorized environment, not a raw Gymnasium environment.
- Wrapper order matters. The output environment of the first wrapper becomes the input to the second.
- `VecNormalize` is configured separately with `normalize`; frame stacking has a dedicated `frame_stack` key. Do not duplicate those unless you intentionally know the wrapper stack.

## Callback entries

Minimal callback forms accepted by RL Zoo:

```yaml
callback: rl_zoo3.callbacks.RawStatisticsCallback

callback:
  - stable_baselines3.common.callbacks.StopTrainingOnMaxEpisodes:
      max_episodes: 3
  - rl_zoo3.callbacks.RawStatisticsCallback
```

Important constraints:

- Callback dict items also require exactly one key.
- RL Zoo imports the class and instantiates it immediately from config kwargs. If the callback requires runtime objects such as an eval environment, it is usually not suitable as a plain config callback.
- Config callbacks are combined with RL Zoo's own progress/checkpoint/eval callbacks later in the training lifecycle.
- HPO-specific behavior involving `TrialEvalCallback` belongs in `../../tuning-optimization/SKILL.md`.

## Linear schedules

RL Zoo converts string schedules for `learning_rate`, `clip_range`, `clip_range_vf`, and `delta_std`. The common config form is:

```yaml
learning_rate: lin_0.0003
clip_range: lin_0.2
```

Internally this becomes a `SimpleLinearSchedule(initial_value)` where `schedule(progress_remaining)` returns `progress_remaining * initial_value`. A numeric non-negative value becomes a constant SB3 schedule; a negative numeric value is left as-is for parameters where negative means disabled.

You can validate the public helper directly without training:

```bash
python - <<'PY'
from rl_zoo3.utils import linear_schedule
schedule = linear_schedule("0.0003")
print(schedule, schedule(1.0), schedule(0.5), schedule(0.0))
PY
```

## Bundled RL Zoo wrappers: quick selection guide

| Wrapper | Use when | Main constraints |
| --- | --- | --- |
| `rl_zoo3.wrappers.YAMLCompatResizeObservation` | Resize image observations with a YAML-friendly `shape: [height, width]` list. | Underlying observation must be image-like and compatible with Gymnasium `ResizeObservation`. |
| `rl_zoo3.wrappers.TruncatedOnSuccessWrapper` | Stop goal-style episodes after one or more consecutive successes and optionally offset rewards. | Relies on `info["is_success"]`; `reset(options=...)` is asserted unsupported. |
| `rl_zoo3.wrappers.ActionNoiseWrapper` | Add Gaussian action noise to test control robustness. | `action_space` must be `spaces.Box`; clips to action bounds. |
| `rl_zoo3.wrappers.ActionSmoothingWrapper` | Smooth continuous actions with an exponential moving average. | Assumes array-like continuous actions; `reset(options=...)` is asserted unsupported. |
| `rl_zoo3.wrappers.DelayedRewardWrapper` | Accumulate rewards and emit them every `delay` steps or at episode end. | `delay` should be a positive integer; `reset(options=...)` is asserted unsupported. |
| `rl_zoo3.wrappers.HistoryWrapper` | Concatenate past Box observations and Box actions into a flat history. | Observation and action spaces must both be `spaces.Box`; do not use with Dict observations. |
| `rl_zoo3.wrappers.HistoryWrapperObsDict` | Add history to the `observation` key of a Dict observation. | Observation space must be `spaces.Dict` with a Box `"observation"` key and a Box action space. |
| `rl_zoo3.wrappers.FrameSkip` | Repeat each action for `skip` environment steps and sum rewards. | Early-stops on termination/truncation; choose `skip` carefully for time-limit tasks. |
| `rl_zoo3.wrappers.MaskVelocityWrapper` | Mask velocity entries in classic-control observations or use generated NoVel env ids. | Only supports the env ids listed in the API reference. |

## SBX and custom algorithm registry patching

RL Zoo's algorithm list is an in-process registry named `ALGOS`. To use SBX/JAX or another compatible algorithm class, patch the registry before calling the RL Zoo `train()` or `enjoy()` function in the same Python process. This requires the optional backend package (for SBX, JAX/SBX) to be installed.

Training shim pattern:

```python
# train_custom_algos.py
import rl_zoo3
import rl_zoo3.exp_manager
import rl_zoo3.train
from rl_zoo3.train import train
from sbx import DQN, DroQ, PPO, SAC, TQC

rl_zoo3.ALGOS.update({
    "dqn": DQN,
    "droq": DroQ,
    "ppo": PPO,
    "sac": SAC,
    "tqc": TQC,
})
rl_zoo3.train.ALGOS = rl_zoo3.ALGOS
rl_zoo3.exp_manager.ALGOS = rl_zoo3.ALGOS

if __name__ == "__main__":
    train()
```

Evaluation shim pattern:

```python
# enjoy_custom_algos.py
import rl_zoo3
import rl_zoo3.enjoy
import rl_zoo3.exp_manager
from rl_zoo3.enjoy import enjoy
from sbx import DQN, DroQ, PPO, SAC, TQC

rl_zoo3.ALGOS.update({
    "dqn": DQN,
    "droq": DroQ,
    "ppo": PPO,
    "sac": SAC,
    "tqc": TQC,
})
rl_zoo3.enjoy.ALGOS = rl_zoo3.ALGOS
rl_zoo3.exp_manager.ALGOS = rl_zoo3.ALGOS

if __name__ == "__main__":
    enjoy()
```

Notes:

- Patch before the CLI parser is built; patching after `train()` starts is too late.
- Use an algorithm name that has compatible hyperparameters. New names such as `droq` generally need a custom config file; route config construction to `../../config-hyperparams/SKILL.md`.
- This is a process-local patch. A normal `python -m rl_zoo3.train` subprocess will not see it unless the patch is packaged and executed in that same process.
