# Evaluation and Callbacks

## Evaluate a policy

Use `stable_baselines3.common.evaluation.evaluate_policy` for post-training checks or inside custom tooling:

```python
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.monitor import Monitor

model = PPO.load("model.zip")
eval_env = Monitor(gym.make("CartPole-v1"))
mean_reward, std_reward = evaluate_policy(
    model,
    eval_env,
    n_eval_episodes=10,
    deterministic=True,
    render=False,
    warn=True,
)
print(mean_reward, std_reward)
```

Key behavior:

- `evaluate_policy()` accepts either a Gymnasium `Env` or an SB3 `VecEnv`; plain environments are wrapped in `DummyVecEnv` internally.
- With vectorized evaluation, requested episodes are statically divided across sub-envs to avoid bias from faster-finishing environments.
- The return is `(mean_reward, std_reward)` unless `return_episode_rewards=True`, which returns `([episode_rewards], [episode_lengths])`.
- `reward_threshold` raises an assertion when `mean_reward` is not greater than the threshold.
- `deterministic=True` uses deterministic policy outputs; use `False` when intentionally measuring stochastic exploration or stochastic policies.

## Monitor and wrapper caveats

Evaluation rewards are only as meaningful as the environment stack:

- Wrap evaluation envs with `Monitor` before reward/length-modifying wrappers when you need original episodic reward and length.
- If no `Monitor`/`VecMonitor` is present, SB3 warns by default because reward scaling, early resets, life-loss wrappers, or other wrappers can change reported returns.
- Match training and evaluation wrappers for image transpose, frame stacking, observation normalization, and reward normalization. `EvalCallback` warns or raises when vector normalization cannot be synchronized.
- For success-rate logging, final-step `info` dictionaries must include `is_success`; `EvalCallback` records `eval/success_rate` only when those flags are present.

## EvalCallback recipe

Use `EvalCallback` during training to evaluate on a separate environment, save the best model, and log evaluation results:

```python
import gymnasium as gym
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import EvalCallback, StopTrainingOnRewardThreshold
from stable_baselines3.common.monitor import Monitor

train_env_id = "CartPole-v1"
eval_env = Monitor(gym.make(train_env_id))
stop_when_good = StopTrainingOnRewardThreshold(reward_threshold=475.0, verbose=1)
eval_callback = EvalCallback(
    eval_env,
    callback_on_new_best=stop_when_good,
    best_model_save_path="runs/cartpole/best",
    log_path="runs/cartpole/eval",
    n_eval_episodes=10,
    eval_freq=10_000,
    deterministic=True,
    render=False,
    warn=True,
)
model = PPO("MlpPolicy", train_env_id, verbose=1)
model.learn(200_000, callback=eval_callback)
```

Outputs and behavior:

- `best_model_save_path` saves `best_model.zip` whenever mean reward improves.
- `log_path` writes `evaluations.npz` containing timesteps, per-episode rewards, episode lengths, and optionally successes.
- `callback_on_new_best` runs only on a new best mean reward; `callback_after_eval` runs after every evaluation.
- `EvalCallback` logs `eval/mean_reward`, `eval/mean_ep_length`, optionally `eval/success_rate`, and dumps at the evaluation timestep.

## CheckpointCallback recipe

Use `CheckpointCallback` to save periodic training snapshots:

```python
from stable_baselines3.common.callbacks import CheckpointCallback

n_envs = 4
target_save_freq = 50_000
checkpoint_callback = CheckpointCallback(
    save_freq=max(target_save_freq // n_envs, 1),
    save_path="runs/agent/checkpoints",
    name_prefix="rl_model",
    save_replay_buffer=True,
    save_vecnormalize=True,
    verbose=2,
)
model.learn(1_000_000, callback=checkpoint_callback)
```

Important details:

- `save_freq` is counted in callback calls, not raw total timesteps. With `n_envs` parallel envs, one env step advances `num_timesteps` by `n_envs`, so divide the target timestep frequency by `n_envs`.
- Model checkpoints use `.zip`; replay buffers and `VecNormalize` stats use `.pkl` sidecars.
- Off-policy algorithms can resume more faithfully when `save_replay_buffer=True` and the replay buffer is loaded before continued training.
- Normalized environments need `save_vecnormalize=True` and explicit `VecNormalize.load()` for later evaluation or continuation.

## Custom BaseCallback

Subclass `BaseCallback` to inspect rollout locals, log custom values, or stop training. `_on_step()` must return `True` to continue or `False` to abort:

```python
from stable_baselines3.common.callbacks import BaseCallback

class RewardGateCallback(BaseCallback):
    def __init__(self, max_steps: int, verbose: int = 0):
        super().__init__(verbose)
        self.max_steps = max_steps

    def _on_step(self) -> bool:
        self.logger.record("custom/num_timesteps", self.num_timesteps)
        return self.num_timesteps < self.max_steps
```

Available callback state includes:

- `self.model`: the SB3 algorithm instance.
- `self.training_env`: `model.get_env()`, asserted non-null.
- `self.logger`: the model logger.
- `self.n_calls`: number of callback invocations.
- `self.num_timesteps`: current model timestep count; with vector envs it increments by `n_envs` per environment step.
- `self.locals` and `self.globals`: rollout/train local variables, updated by SB3.
- `self.parent`: parent event callback when nested under `EvalCallback`, `EveryNTimesteps`, or `CallbackList`.

## Callback composition

- Pass a list of callbacks to `learn()`; SB3 converts it to `CallbackList`.
- Use `EveryNTimesteps(n_steps, callback)` when an event should trigger at a lower-bound timestep interval under vector envs.
- Use `LogEveryNTimesteps(n_steps)` to force periodic logger dumps.
- Use `StopTrainingOnNoModelImprovement` or `StopTrainingOnRewardThreshold` only as children of `EvalCallback`, because they inspect the parent callback's evaluation state.

## Frequency with multiple environments

When `n_envs > 1`, callbacks are called after each vectorized `env.step()`, while `model.num_timesteps` advances by `n_envs`. For comparable wall-clock training timesteps across vectorization settings:

```python
effective_freq = max(target_timesteps // n_envs, 1)
```

Apply this to `CheckpointCallback.save_freq`, `EvalCallback.eval_freq`, render/video callback frequencies, and custom callback counters based on `n_calls`.
