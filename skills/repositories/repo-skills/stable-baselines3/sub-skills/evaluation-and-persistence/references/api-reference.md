# API Reference

This page summarizes the SB3 APIs most often needed for evaluation, callbacks, logging, and persistence.

## Evaluation

```python
from stable_baselines3.common.evaluation import evaluate_policy

evaluate_policy(
    model,
    env,
    n_eval_episodes=10,
    deterministic=True,
    render=False,
    callback=None,
    reward_threshold=None,
    return_episode_rewards=False,
    warn=True,
)
```

Returns `(mean_reward, std_reward)` or `(episode_rewards, episode_lengths)` when `return_episode_rewards=True`.

## Callback imports

```python
from stable_baselines3.common.callbacks import (
    BaseCallback,
    CallbackList,
    CheckpointCallback,
    EvalCallback,
    EveryNTimesteps,
    LogEveryNTimesteps,
    ProgressBarCallback,
    StopTrainingOnMaxEpisodes,
    StopTrainingOnNoModelImprovement,
    StopTrainingOnRewardThreshold,
)
```

## EvalCallback constructor

```python
EvalCallback(
    eval_env,
    callback_on_new_best=None,
    callback_after_eval=None,
    n_eval_episodes=5,
    eval_freq=10000,
    log_path=None,
    best_model_save_path=None,
    deterministic=True,
    render=False,
    verbose=1,
    warn=True,
)
```

Notes:

- Converts a plain Gymnasium env to `DummyVecEnv` internally.
- Saves best model as `best_model.zip` under `best_model_save_path`.
- Writes `evaluations.npz` under `log_path`.
- Synchronizes `VecNormalize` stats when train and eval envs are compatible.

## CheckpointCallback constructor

```python
CheckpointCallback(
    save_freq,
    save_path,
    name_prefix="rl_model",
    save_replay_buffer=False,
    save_vecnormalize=False,
    verbose=0,
)
```

Saved filenames follow these patterns:

- `{name_prefix}_{num_timesteps}_steps.zip`
- `{name_prefix}_replay_buffer_{num_timesteps}_steps.pkl`
- `{name_prefix}_vecnormalize_{num_timesteps}_steps.pkl`

## BaseCallback hooks

Implement private hooks in subclasses:

```python
class MyCallback(BaseCallback):
    def _on_training_start(self) -> None: ...
    def _on_rollout_start(self) -> None: ...
    def _on_step(self) -> bool: return True
    def _on_rollout_end(self) -> None: ...
    def _on_training_end(self) -> None: ...
```

`_on_step()` is abstract and controls training continuation.

## Logger

```python
from stable_baselines3.common.logger import configure

logger = configure(folder="runs/logs", format_strings=["stdout", "csv", "json", "tensorboard"])
model.set_logger(logger)
```

Media wrappers:

```python
from stable_baselines3.common.logger import Figure, HParam, Image, Video
```

When recording media, exclude unsupported formats such as `stdout`, `log`, `json`, and `csv`.

## Model persistence

Every concrete algorithm class exposes class methods and instance methods such as:

```python
model.save("model.zip")
model = PPO.load("model.zip", env=env, device="auto", custom_objects=None, print_system_info=False)
model.get_parameters()
model.set_parameters(params, exact_match=True)
model.predict(obs, state=None, episode_start=None, deterministic=False)
```

Important semantics:

- `load()` returns a new model instance.
- `device` accepts `"auto"`, `"cpu"`, `"cuda"`, or a PyTorch device string.
- `predict()` returns `(actions, next_state)`; recurrent-compatible arguments are accepted even though core SB3 algorithms are usually non-recurrent.
- SB3 raises a helpful `ValueError` if a Gymnasium `(obs, info)` reset tuple is passed directly to `predict()` instead of only `obs`.

## Replay buffer and VecNormalize

```python
model.save_replay_buffer("replay_buffer.pkl")
model.load_replay_buffer("replay_buffer.pkl")
```

```python
from stable_baselines3.common.vec_env import VecNormalize

vec_env.save("vecnormalize.pkl")
vec_env = VecNormalize.load("vecnormalize.pkl", base_vec_env)
vec_env.training = False
vec_env.norm_reward = False
```

Use these sidecars together with model `.zip` files when resuming off-policy training or evaluating normalized observations.
