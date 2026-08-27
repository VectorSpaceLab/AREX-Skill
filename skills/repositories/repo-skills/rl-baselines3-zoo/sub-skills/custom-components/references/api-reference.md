# API reference for custom components

This reference records the installed `rl_zoo3` component APIs relevant to custom environments, wrappers, callbacks, schedules, and algorithm registry patches. Use it to plan and validate components before handing actual command execution to `../../training-cli/SKILL.md`.

## Import-string rules shared by wrappers, callbacks, and policies

A dotted import string is split at the last dot:

```text
module.path.ClassOrObjectName
```

RL Zoo imports `module.path` and reads attribute `ClassOrObjectName`. Common failure points are missing packages, wrong module path, wrong case, or a class that imports successfully but has an incompatible constructor for the role.

The bundled checker validates this layer:

```bash
python ../scripts/component_import_checker.py \
  --wrapper rl_zoo3.wrappers.HistoryWrapper \
  --callback stable_baselines3.common.callbacks.StopTrainingOnMaxEpisodes \
  --policy stable_baselines3.ppo.MlpPolicy
```

## Utility APIs

| API | Signature | Return / effect | Key constraints |
| --- | --- | --- | --- |
| `rl_zoo3.utils.get_wrapper_class` | `(hyperparams: dict[str, Any], key: str = "env_wrapper") -> Callable[[gym.Env], gym.Env] | None` | Returns a wrapper function that applies one or more wrapper classes in order, or `None`. | Looks up `env_wrapper` or `vec_env_wrapper`; each item is a dotted string, a class object in Python configs, or a one-key dict mapping class to kwargs. Dict items with more than one key raise an assertion about YAML indentation. |
| `rl_zoo3.utils.get_callback_list` | `(hyperparams: dict[str, Any]) -> list[BaseCallback]` | Imports and instantiates callbacks declared under `callback`. | Strings are instantiated with no kwargs; one-key dict entries pass kwargs; already-created `BaseCallback` objects are accepted in Python configs. Runtime-object callbacks are usually not suitable as plain YAML callbacks. |
| `rl_zoo3.utils.get_class_by_name` | `(name: str) -> type` | Imports and returns a class or object by dotted string. | Used for custom policies and callback classes. Raises import or attribute errors when the dotted path is wrong. |
| `rl_zoo3.utils.linear_schedule` | `(initial_value: float | str) -> SimpleLinearSchedule` | Returns a linear schedule object. | `initial_value` is coerced to `float`; invalid strings raise conversion errors. |
| `rl_zoo3.utils.SimpleLinearSchedule` | `__init__(initial_value: float | str)`; `__call__(progress_remaining: float) -> float`; `__repr__() -> str` | Computes `progress_remaining * initial_value`. | RL Zoo schedule strings normally use `lin_<value>` for selected numeric hyperparameters. |

Schedule preprocessing applies to `learning_rate`, `clip_range`, `clip_range_vf`, and `delta_std`. Strings are split on `_` and converted to `SimpleLinearSchedule(float(value))`; non-negative numeric values become constant schedules; negative numeric values are left unchanged.

## Wrapper APIs

| Wrapper | Signature | Behavior | Constraints and failure modes |
| --- | --- | --- | --- |
| `rl_zoo3.wrappers.YAMLCompatResizeObservation` | `(env: gym.Env, shape: list[int])` | Converts YAML list `shape` into the tuple expected by Gymnasium `ResizeObservation`. | `shape` must contain height and width. The wrapped observation must be compatible with resize operations. |
| `rl_zoo3.wrappers.TruncatedOnSuccessWrapper` | `(env: gym.Env, reward_offset: float = 0.0, n_successes: int = 1)` | Adds `reward_offset`, counts consecutive `info["is_success"]`, and truncates after `n_successes`. | Intended for goal/success environments. `reset(options=...)` is asserted unsupported. `compute_reward` is delegated to the wrapped env and offset. |
| `rl_zoo3.wrappers.ActionNoiseWrapper` | `(env: gym.Env, noise_std: float = 0.1)` | Adds Gaussian noise to each action and clips to action-space bounds. | `action_space` must be `spaces.Box`; assertion occurs when stepping a non-Box action space. |
| `rl_zoo3.wrappers.ActionSmoothingWrapper` | `(env: gym.Env, smoothing_coef: float = 0.0)` | Uses an exponential moving average of actions. | Assumes array-like continuous actions. `reset(options=...)` is asserted unsupported. |
| `rl_zoo3.wrappers.DelayedRewardWrapper` | `(env: gym.Env, delay: int = 10)` | Accumulates reward and emits it every `delay` steps or when the episode terminates/truncates. | `delay` should be positive. `reset(options=...)` is asserted unsupported. |
| `rl_zoo3.wrappers.HistoryWrapper` | `(env: gym.Env, horizon: int = 2)` | Concatenates `horizon` observations and `horizon` actions into one Box observation. | Requires `observation_space` and `action_space` to be `spaces.Box`. Use `HistoryWrapperObsDict` for Dict observations. |
| `rl_zoo3.wrappers.HistoryWrapperObsDict` | `(env: gym.Env, horizon: int = 2)` | Updates the Dict observation's `"observation"` subspace to contain history. | Requires `observation_space` to be `spaces.Dict`, `observation_space.spaces["observation"]` to be `spaces.Box`, and `action_space` to be `spaces.Box`. |
| `rl_zoo3.wrappers.FrameSkip` | `(env: gym.Env, skip: int = 4)` | Repeats each action for up to `skip` steps and sums rewards. | Stops early on termination/truncation. Large `skip` values change effective episode length. |
| `rl_zoo3.wrappers.MaskVelocityWrapper` | `(env: gym.Env)` | Multiplies selected observation indices by zero to remove velocities. | Requires `env.unwrapped.spec.id`; unsupported ids raise `NotImplementedError`. Supported ids are listed below. |
| `rl_zoo3.wrappers.TimeFeatureWrapper` | imported from `sb3_contrib.common.wrappers` for compatibility | Adds a time feature. | This is a re-export/backward-compatibility import; validate the installed `sb3_contrib` version when using it. |

### `MaskVelocityWrapper` supported ids

| Base env id | Masked velocity indices | Registered NoVel id |
| --- | --- | --- |
| `CartPole-v1` | `[1, 3]` | `CartPoleNoVel-v1` |
| `MountainCar-v0` | `[1]` | `MountainCarNoVel-v0` |
| `MountainCarContinuous-v0` | `[1]` | `MountainCarContinuousNoVel-v0` |
| `Pendulum-v1` | `[2]` | `PendulumNoVel-v1` |
| `LunarLander-v3` | `[2, 3, 5]` | `LunarLanderNoVel-v3` |
| `LunarLanderContinuous-v3` | `[2, 3, 5]` | `LunarLanderContinuousNoVel-v3` |

The NoVel ids are registered by the installed `rl_zoo3.import_envs` startup module. They still require the base environment package to be available; LunarLander variants depend on Box2D support in Gymnasium.

## Callback APIs

| Callback | Signature | Behavior | Constraints and routing |
| --- | --- | --- | --- |
| `rl_zoo3.callbacks.RawStatisticsCallback` | `(verbose=0)` | Logs raw episodic return and length to TensorBoard under `raw/rollouts/...`. | Requires TensorBoard logging to be active. Add `--tensorboard-log <dir>` or another setup that creates a TensorBoard output format. |
| `rl_zoo3.callbacks.ParallelTrainCallback` | `(gradient_steps: int = 100, verbose: int = 0, sleep_time: float = 0.0)` | Uses a background thread to train a copied off-policy model while the live model collects experience. | Asserts the model is `SAC` or `TQC`; normally paired with off-policy settings such as episode-based train frequency. Not for PPO/A2C/DQN/TD3/DDPG unless the implementation changes. |
| `rl_zoo3.callbacks.SaveVecNormalizeCallback` | `(save_freq: int, save_path: str, name_prefix: str | None = None, verbose: int = 0)` | Saves `vecnormalize.pkl` or `<prefix>_<timesteps>_steps.pkl` when a VecNormalize env exists. | RL Zoo also wires this internally into evaluation callbacks; manual use requires a valid path and model with VecNormalize. |
| `rl_zoo3.callbacks.TrialEvalCallback` | `(eval_env: VecEnv, trial: optuna.Trial, n_eval_episodes: int = 5, eval_freq: int = 10000, deterministic: bool = True, verbose: int = 0, best_model_save_path: str | None = None, log_path: str | None = None) -> None` | Evaluates an Optuna trial, reports rewards, and requests pruning. | HPO-specific; route tasks involving this callback to `../../tuning-optimization/SKILL.md`. It requires runtime `eval_env` and `trial` objects, so it is not a simple YAML callback. |

Stable-Baselines3 callbacks can also be referenced by dotted import string when their constructor kwargs can be provided from config, for example `stable_baselines3.common.callbacks.StopTrainingOnMaxEpisodes` with `max_episodes`.

## Environment startup and NoVel registration APIs

Installed RL Zoo startup imports `rl_zoo3.import_envs` in train/evaluation-related modules. Its public runtime effects are:

- Best-effort imports of optional environment packages: missing packages are ignored.
- Gymnasium registration of ALE/Atari when `ale_py` is installed.
- A compatibility alias for `highway_env` when that package is installed.
- Automatic import of a module named `custom_envs` if available.
- NoVel registration for all `MaskVelocityWrapper.velocity_indices` entries, using a factory that creates the base env and wraps it with `MaskVelocityWrapper`.

For explicit custom packages, prefer `--gym-packages` because it makes the registration dependency visible in the command.

## Algorithm registry API

`rl_zoo3.utils.ALGOS` and the exported `rl_zoo3.ALGOS` map algorithm names to SB3/SB3-Contrib-compatible classes. Current installed keys:

```text
a2c, ars, crossq, ddpg, dqn, ppo, ppo_lstm, qrdqn, sac, td3, tqc, trpo
```

Registry patching rules:

- Update the dictionary in-place before `train()` or `enjoy()` builds its parser.
- Also update module-level aliases in `rl_zoo3.train`, `rl_zoo3.enjoy`, and `rl_zoo3.exp_manager` for the process that will execute the command.
- Ensure the algorithm class has an SB3-like constructor/load interface and compatible hyperparameters.
- New algorithm names need config coverage; route config details to `../../config-hyperparams/SKILL.md`.
