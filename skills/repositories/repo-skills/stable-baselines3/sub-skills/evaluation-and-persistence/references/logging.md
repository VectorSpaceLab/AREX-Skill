# Logging, TensorBoard, and Progress Bars

## Default logger behavior

SB3 configures logging from `verbose`, `tensorboard_log`, and optional environment variables:

- `verbose=0` usually disables human stdout logging unless a logger is explicitly set.
- `verbose=1` enables human-readable stdout tables.
- `tensorboard_log="folder"` adds TensorBoard output when TensorBoard dependencies are installed.
- `SB3_LOGDIR` can provide the default logger folder when `configure(None, ...)` is used.
- `SB3_LOG_FORMAT` can provide comma-separated formats, defaulting to `stdout,log,csv` in `configure()`.

Available output formats include `stdout`, `log`, `csv`, `json`, and `tensorboard`.

## Custom logger recipe

Use `stable_baselines3.common.logger.configure` and `model.set_logger()` to control output formats:

```python
from stable_baselines3 import A2C
from stable_baselines3.common.logger import configure

logger = configure("runs/a2c_logs", ["stdout", "csv", "tensorboard"])
model = A2C("MlpPolicy", "CartPole-v1", verbose=1)
model.set_logger(logger)
model.learn(100_000)
```

Important caveat: passing a custom logger overwrites the constructor's `tensorboard_log` and `verbose` logger setup. Configure every output you need explicitly.

## Common log namespaces

Typical logger keys include:

- `eval/mean_reward`, `eval/mean_ep_length`, `eval/success_rate`: written by `EvalCallback`.
- `rollout/ep_rew_mean`, `rollout/ep_len_mean`, `rollout/success_rate`: training rollout summaries; episodic reward/length require `Monitor` data.
- `time/fps`, `time/iterations`, `time/time_elapsed`, `time/total_timesteps`: training progress.
- `train/learning_rate`, `train/loss`, `train/value_loss`, `train/policy_gradient_loss`, `train/entropy_loss`, `train/approx_kl`, and algorithm-specific keys.

## TensorBoard recipe

Basic TensorBoard logging:

```python
from stable_baselines3 import PPO

model = PPO("MlpPolicy", "CartPole-v1", tensorboard_log="runs/tensorboard", verbose=1)
model.learn(100_000, tb_log_name="ppo_cartpole")
```

Then run:

```bash
tensorboard --logdir runs/tensorboard
```

For continuous curves across multiple `learn()` calls:

```python
model.learn(100_000, tb_log_name="ppo_cartpole")
model.learn(100_000, tb_log_name="ppo_cartpole", reset_num_timesteps=False)
```

Keep `tb_log_name` constant and `reset_num_timesteps=False`; changing names or resetting timesteps creates split curves.

## Logging custom values from callbacks

Use `self.logger.record()` inside a `BaseCallback`; call `self.logger.dump(self.num_timesteps)` only when you need logs more often than SB3's default dumping cadence:

```python
from stable_baselines3.common.callbacks import BaseCallback

class TensorboardScalarCallback(BaseCallback):
    def _on_step(self) -> bool:
        self.logger.record("custom/my_metric", 1.0)
        return True
```

For non-scalar media, use SB3 logger wrapper classes and exclude unsupported output formats:

```python
from stable_baselines3.common.logger import Image

self.logger.record(
    "trajectory/image",
    Image(image_array, "HWC"),
    exclude=("stdout", "log", "json", "csv"),
)
```

Supported TensorBoard helper classes include `Image`, `Figure`, `Video`, and `HParam`. stdout/log/json/csv cannot write those media types and raise `FormatUnsupportedError` unless excluded.

## Progress bars

Two equivalent ways to show progress:

```python
model.learn(100_000, progress_bar=True)
```

or:

```python
from stable_baselines3.common.callbacks import ProgressBarCallback
model.learn(100_000, callback=ProgressBarCallback())
```

Progress bars require `tqdm` and `rich`. They are installed by the SB3 extra package (`stable-baselines3[extra]`). Without those packages, constructing or using the progress bar raises an import error.

## Plotting evaluation results

When `EvalCallback(log_path=...)` is used, SB3 writes `evaluations.npz` with timesteps, episode rewards, episode lengths, and optionally successes. Load it with NumPy or use SB3 plotting helpers in an analysis script. Keep plotting outputs in experiment directories, not in runtime skills.
