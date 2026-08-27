# Troubleshooting Evaluation and Persistence

## Evaluation rewards look wrong

Likely causes:

- Evaluation env is missing `Monitor`/`VecMonitor`.
- Reward wrappers, early-reset wrappers, life-loss wrappers, or normalization wrappers alter reward/length before SB3 counts episodes.
- Train and eval wrapper stacks differ.

Fixes:

- Wrap evaluation envs with `Monitor` before reward/length-modifying wrappers when original returns matter.
- Use the same observation wrappers in train and eval, especially image transpose/frame-stack wrappers.
- For `VecNormalize`, load/sync stats and set `eval_env.training = False`; set `eval_env.norm_reward = False` for original reward scale.
- Keep `warn=True` on `evaluate_policy()` and `EvalCallback` until the evaluation stack is verified.

## Deterministic and stochastic predictions differ

This is expected:

- `deterministic=True` selects deterministic policy actions and is the default for `evaluate_policy()` and `EvalCallback`.
- `deterministic=False` samples stochastic actions when supported; DQN can use epsilon-greedy exploration when its exploration rate is nonzero.
- Deterministic action reproducibility requires the same model weights, preprocessing/wrappers, observation values, and device-compatible numerics.

If inference crashes after `env.reset()`, ensure only the observation is passed to `predict()`, not Gymnasium's `(obs, info)` tuple.

## Callback frequencies fire too often or too rarely

SB3 callback calls happen after vectorized `env.step()` calls, while `model.num_timesteps` advances by `n_envs`. For comparable frequencies:

```python
callback_freq = max(target_timesteps // n_envs, 1)
```

Apply this to:

- `EvalCallback(eval_freq=...)`
- `CheckpointCallback(save_freq=...)`
- `EveryNTimesteps(n_steps=...)` when you want comparable lower-bound intervals
- custom callbacks that compare `self.n_calls`

Prefer comparing `self.num_timesteps` in custom callbacks when possible.

## Progress bar import error

`progress_bar=True` and `ProgressBarCallback` require both `tqdm` and `rich`. Install SB3 with extras or add those packages to the environment. If progress bars interact poorly with logs, disable them and rely on stdout/csv/TensorBoard logger outputs.

## TensorBoard logs are missing or split

Check:

- TensorBoard dependencies are installed.
- The model was created with `tensorboard_log="..."` or a custom logger includes `"tensorboard"`.
- `model.set_logger(custom_logger)` did not accidentally replace a constructor-configured TensorBoard logger with formats that omit `"tensorboard"`.
- Repeated `learn()` calls use the same `tb_log_name` and `reset_num_timesteps=False` for continuous curves.
- Custom image/figure/video/hparam values exclude unsupported formats.

## Loaded model did not update my existing model

SB3 `Algorithm.load()` is a class method that returns a new model instance. Replace the variable:

```python
model = PPO.load("model.zip", env=env)
```

For in-place weight transfer into an existing architecture, use `get_parameters()` and `set_parameters()` instead.

## Loading fails with custom objects or pickle errors

Use a controlled load:

```python
model = PPO.load(
    "model.zip",
    env=env,
    device="cpu",
    custom_objects={"learning_rate": 3e-4},
    print_system_info=True,
)
```

Guidance:

- `custom_objects` keys must match saved data keys.
- Start with CPU to rule out CUDA/device issues.
- Compare printed system info from the save archive and current environment.
- If a custom policy or env class is genuinely required, make that class importable before loading, or replace the serialized field when safe.

## CUDA, CPU, and device portability

Symptoms include CUDA unavailable errors, tensor device mismatches, or load succeeding on one machine but not another.

Fixes:

- Load with `device="cpu"` for maximum portability.
- Use `device="auto"` only when CUDA availability is acceptable and tested.
- After load, check `model.device` and `model.policy.device`.
- Replay buffers loaded after device changes should be loaded through SB3's `load_replay_buffer()` so buffer tensors/device fields are updated.

## VecNormalize evaluation is unstable

Common mistakes:

- Saving only `model.zip` but not `vecnormalize.pkl`.
- Recreating a fresh `VecNormalize` instead of loading the training stats.
- Leaving `training=True` during evaluation.
- Normalizing rewards during evaluation when reporting original reward scale.

Fix:

```python
base_eval_env = DummyVecEnv([lambda: make_env()])
eval_env = VecNormalize.load("vecnormalize.pkl", base_eval_env)
eval_env.training = False
eval_env.norm_reward = False
model = PPO.load("model.zip", env=eval_env)
```

## Checkpoint resume is incomplete

For off-policy algorithms, a model checkpoint alone does not include the replay buffer. Use either:

- `CheckpointCallback(save_replay_buffer=True, save_vecnormalize=True)`, or
- manual `model.save_replay_buffer()` and `vec_env.save()` sidecars.

On resume, load sidecars before continuing training and set `reset_num_timesteps=False` if you want continuous counters/logging.

## Zip archive inspection concerns

SB3 zip archives include JSON metadata and PyTorch/cloudpickle payloads. Listing filenames and reading `_stable_baselines3_version` or `system_info.txt` with `zipfile` is safe. Loading arbitrary pickled objects from untrusted archives is not safe; only load checkpoints from trusted sources or use isolated inspection environments.
