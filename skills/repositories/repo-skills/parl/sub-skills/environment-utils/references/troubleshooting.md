# Environment utility troubleshooting

Use this guide when PARL wrapper, replay-buffer, scheduler, CSV, logger, or summary behavior fails before or during a small RL workflow.

## Gym reset/step API mismatch

Symptoms:

- `ValueError: too many values to unpack` or `not enough values to unpack` around `env.reset()` or `env.step()`.
- Code expects `(obs, reward, done, info)` but receives `(obs, reward, terminated, truncated, info)`.
- Code expects `obs` but receives `(obs, info)`.

Fixes:

1. Wrap ordinary Gym envs with `CompatWrapper` before PARL-style training code:

   ```python
   env = CompatWrapper(gym.make(env_name))
   ```

2. Keep only one API convention inside a loop. After `CompatWrapper`, call:

   ```python
   obs = env.reset()
   next_obs, reward, done, info = env.step(action)
   ```

3. Seed through the wrapper when targeting Gym >=0.26 compatibility:

   ```python
   env.seed(seed)
   obs = env.reset()
   ```

4. Do not pass Gymnasium objects without a compatibility check. PARL imports `gym` and its version helper reads `gym.__version__`.

## Continuous action mapping errors

Symptoms:

- Assertion: `action space should be instance of gym.spaces.Box`.
- Assertion: `the action should be in range [-1.0, 1.0]`.
- Saturated or oddly scaled continuous-control behavior.

Fixes:

- Use `ActionMappingWrapper` only for continuous `Box` actions.
- Ensure the policy's final activation or post-processing produces values in `[-1, 1]`.
- Check whether all action dimensions share the same low/high scalar. PARL's wrapper stores `low[0]` and `high[0]`; for per-dimension action ranges, write or verify a custom mapper.
- Wrap order commonly used by PARL continuous-control examples is:

  ```python
  env = CompatWrapper(env)
  env = ActionMappingWrapper(env)
  ```

## Vector environment surprises

Symptoms:

- The observation returned for a finished environment already looks like a reset observation.
- `IndexError` in `VectorEnv.step`.
- Agent batch conversion fails.

Fixes:

- `VectorEnv.step` auto-resets an env when it returns `done=True`. Preserve `done_batch` separately if the learner needs terminal flags.
- Pass exactly one action per env.
- Convert Python lists to arrays after `VectorEnv` if your agent expects array batches:

  ```python
  obs_array = np.asarray(obs_batch)
  ```

- `VectorEnv` is synchronous and local. Use xparl guidance only if the task explicitly needs remote actors.

## Atari wrapper dependency or environment failures

Symptoms:

- `ImportError` for `cv2` or Gym Atari extras.
- Assertion failures around `NOOP`, `FIRE`, action meanings, ALE lives, or `NoFrameskip` ids.
- Shape mismatch between model and observations.

Fixes:

- Treat `wrap_deepmind` as an Atari-specific wrapper stack, not a generic image-env adapter.
- Install and verify OpenCV/Gym Atari dependencies in the target environment before use.
- Set `obs_format="NCHW"` when the model expects channel-first image tensors; default is `NHWC`.
- Use `get_wrapper_by_cls(env, MonitorEnv)` to retrieve episode statistics from a nested Atari wrapper stack.

## MuJoCo/RMS wrapper issues

Symptoms:

- Missing MuJoCo/Gym environment imports.
- Observation normalization shape errors.
- `bad_transition` is missing or incorrect.

Fixes:

- MuJoCo is optional; install it intentionally for the target environment.
- `wrap_rms` expects one-dimensional numeric observations. Recheck or customize for dict, image, or nested observation spaces.
- Use training observation statistics for evaluation:

  ```python
  ob_rms = get_ob_rms(train_env)
  eval_env = wrap_rms(eval_env, gamma=None, test=True, ob_rms=ob_rms)
  ```

- The time-limit mask depends on `_max_episode_steps` and `_elapsed_steps` from the underlying env.

## Multi-agent wrapper dependency or action issues

Symptoms:

- Import error suggesting PettingZoo/Gym versions.
- Scenario assertion failure.
- Discrete actions are not what the environment expects.
- Continuous action range assertion failure.

Fixes:

- Use only supported scenario names listed in `references/wrappers-and-data.md`.
- For modern MPE, install a compatible PettingZoo MPE stack intentionally; it is not a default PARL dependency.
- For discrete multi-agent actions, pass per-agent logits/probabilities or one-hot-like vectors; PARL chooses `argmax`.
- For continuous multi-agent actions, pass per-agent arrays in `[-1, 1]`; the wrapper maps to each action space range.
- Prefer `parl.env.multiagent_env.MAenv`; the legacy `multiagent_simple_env` wrapper is deprecated and depends on older multiagent-particle-envs.

## ReplayMemory shape, dtype, or sampling failures

Symptoms:

- `TypeError` during `ReplayMemory(...)` construction with tuple/list dimensions.
- Broadcast errors in `append`.
- `ValueError: high <= 0` or similar from `np.random.randint` during sampling.
- Loaded replay memory has unexpected capacity or dtypes.

Fixes:

- Use flat integer `obs_dim` and continuous integer `act_dim`; flatten complex observations before storing or use a custom buffer.
- For discrete actions, pass `act_dim=0` and append scalar integer actions.
- For continuous actions, pass a positive action dimension and append arrays shaped `(act_dim,)`.
- Do not call `sample_batch` until at least one item has been appended; most training loops should wait for a warm-up size greater than or equal to the batch size.
- Remember that sampling is with replacement. A batch size larger than the current buffer size is allowed statistically, but may not be what the algorithm expects.
- When loading from `.npz`, create a destination buffer with capacity at least as large as the intended restored sample count.
- `load_from_d4rl` expects keys `observations`, `next_observations`, `actions`, `rewards`, and `terminals`; check each shape and dtype before adopting a dataset.

## Scheduler surprises

Symptoms:

- Piecewise values do not update as expected after a large `step_num`.
- Assertion failure for scheduler steps.
- Linear decay goes negative or never reaches zero in user code.

Fixes:

- `PiecewiseScheduler` requires strictly increasing boundary steps and advances at most one boundary per call. Use repeated calls or inspect current behavior before using very large jumps.
- `LinearDecayScheduler` saturates internal `cur_step` at `max_steps`, so it should return zero after the schedule is exhausted.
- Always pass positive integer `step_num` values.

## CSVLogger failures

Symptoms:

- Assertion: input should be a dict.
- Assertion: keys must be the same as before.
- Empty CSV file until the process exits.
- An existing file was overwritten.

Fixes:

- Use a stable dict schema for every `log_dict` call.
- Call `flush()` after important writes and `close()` at the end.
- Create the logger with a deliberate output path. It opens in write mode and truncates existing files.
- Use one writer per output file. The lock is thread-local to one `CSVLogger` instance and does not coordinate multiple processes.

## Logger and summary output path problems

Symptoms:

- A previous training-log directory disappeared.
- Summary files were written under an unexpected default directory.
- `ImportError` for `visualdl` or `tensorboardX`.
- Multiprocess logs/events are corrupted or confusing.

Fixes:

- Treat `logger.set_dir(dirname)` as destructive for an existing `dirname`; it removes and recreates the directory.
- Set `logger.set_dir` explicitly before calling `summary.add_scalar` or `summary.add_histogram`.
- If you use `logger.auto_set_dir`, pass an explicit action in automation and understand `d` deletes, `k` keeps, and `n` chooses a new directory.
- Install either VisualDL or TensorBoardX intentionally. `parl.utils.summary` prefers VisualDL and falls back to TensorBoardX only if VisualDL import fails.
- In distributed examples, write summaries from the learner or a designated logging process rather than from every actor.

## Optional dependencies are not default verification

Atari/OpenCV, MuJoCo, PettingZoo MPE, legacy multiagent-particle-envs, VisualDL, and TensorBoardX are optional surfaces. A successful PARL base import or Torch backend smoke does not prove those optional wrappers. Use `scripts/check_env_utils.py --optional-wrappers` for a safe import classification, then perform a tiny environment-specific smoke in the target environment before training.
