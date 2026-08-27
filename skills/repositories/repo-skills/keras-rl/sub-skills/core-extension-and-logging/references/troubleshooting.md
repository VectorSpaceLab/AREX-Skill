# Core extension and logging troubleshooting

Use this guide for shared keras-rl lifecycle, processor, callback, logging, plotting, utility, and environment failures.

## `RuntimeError`: agent has not been compiled before `fit` or `test`

Symptom:

```text
Your tried to fit your agent but it hasn't been compiled yet. Please call `compile()` before `fit()`.
```

or the corresponding `test()` message.

Cause: `Agent.fit` and `Agent.test` require `self.compiled` to be true. Concrete agents set this inside their own `compile(...)` methods.

Fix:

1. Build the concrete agent fully.
2. Call the concrete agent's `compile(...)` with the required optimizer/metrics signature.
3. Only then call `fit`, `test`, `save_weights`/checkpoint callbacks, or metric loggers.

If `compile(...)` itself fails, route to the discrete or continuous sub-skill for algorithm-specific model-shape and optimizer requirements.

## `ValueError`: `action_repetition must be >= 1`

Cause: both `fit` and `test` reject zero or negative action repetition.

Fix:

- Use `action_repetition=1` for normal operation.
- Use `action_repetition>1` only when repeatedly applying the same action is valid for the environment.
- Remember that `nb_steps` counts agent decision steps, while the environment may receive up to `action_repetition` raw steps per agent step.

## Training or testing hangs in never-ending episodes

Cause: the environment does not emit `done=True`, or a modern Gym wrapper's `terminated`/`truncated` flags are not combined into old `done`.

Fix:

- Set `nb_max_episode_steps` during `fit`/`test`.
- Wrap modern Gym/Gymnasium environments so `step` returns `(observation, reward, done, info)` where `done = terminated or truncated`.
- Verify the adapter with a one-episode manual loop before training.

## Visualization opens no window or crashes in headless environments

Symptoms:

- `TclError`, `cannot connect to X server`, `No display name`, or similar GUI backend failures.
- `agent.test(..., visualize=True)` stalls on a remote/CI host.

Cause: `Visualizer` calls `env.render(mode='human')` after each action, and `Agent.test` defaults `visualize=True`.

Fix:

- Use `visualize=False` for headless training and testing.
- If plotting logs to a file, call the bundled visualizer with `--output`; it selects a noninteractive Matplotlib backend before importing `pyplot`.
- If you need interactive rendering, run where a display is available and the environment supports `render(mode='human')`.

## Missing Matplotlib when visualizing logs

Symptom:

```text
Failed to import matplotlib
```

Cause: the JSON log helper depends on Matplotlib, but keras-rl itself does not require it.

Fix:

- Install a Matplotlib version compatible with your Python/Keras stack.
- Re-run:

  ```bash
  python scripts/visualize_keras_rl_log.py run_log.json --output run_log.png
  ```

- For locked legacy Python environments, choose a Matplotlib release that still supports that Python version.

## `rl.callbacks` import fails because `wandb` is missing

Symptom:

```text
ModuleNotFoundError: No module named 'wandb'
```

Cause: this keras-rl line imports `wandb` at `rl.callbacks` module import time. Because `rl.core` imports callback classes, missing W&B can break core/agent imports even when you never instantiate `WandbLogger`.

Fix options:

1. Install a compatible `wandb` package in the same environment.
2. Use an environment known to satisfy legacy keras-rl callback imports.
3. If you intentionally avoid W&B network writes, set W&B offline/disabled behavior before constructing `WandbLogger`.

Do not diagnose this as a missing callback argument; it is an import-time optional dependency issue.

## `WandbLogger` starts network/account behavior unexpectedly

Cause: `WandbLogger(**kwargs)` calls `wandb.init(...)` in its constructor. Defaults include `project='keras-rl'` and `anonymous='allow'`.

Fix:

- Instantiate `WandbLogger` only when W&B logging is desired.
- Configure W&B offline/disabled settings before the Python process starts when network writes are not allowed.
- Prefer `FileLogger` for a local JSON artifact with no external service dependency.
- If W&B config serialization fails, check whether your environment wrapper exposes serializable `.env`, `.spec`, and `__dict__` fields; otherwise use `FileLogger` or subclass the logger.

## `FileLogger` JSON is missing the `episode` key

Symptom from the bundled visualizer:

```text
Log file does not contain the required "episode" key.
```

Causes:

- The file is not produced by `rl.callbacks.FileLogger`.
- Training ended before the first episode completed, so no episode-level data was saved.
- The file was truncated, overwritten by another process, or edited.

Fix:

1. Confirm the callback was attached to `fit`, not only to `test`:

   ```python
   callbacks = [FileLogger('run_log.json', interval=1)]
   agent.fit(env, nb_steps=..., callbacks=callbacks, visualize=False)
   ```

2. Run enough steps for at least one episode to finish.
3. Inspect the JSON top-level object and verify that every plotted key has a list with the same length as `episode`.
4. Use the bundled helper's clear validation errors to locate malformed keys.

## Log visualizer says a metric length does not match `episode`

Cause: every plotted key must have the same number of values as `episode`. Mixed manual edits, partial writes, or non-`FileLogger` JSON can violate this.

Fix:

- Recreate the log with `FileLogger`.
- Select only valid keys with `--keys` if some extra keys are malformed.
- Avoid reading a log while another process is actively writing it; copy the file first for analysis.

## Checkpoint filenames fail to format or create unusable paths

Cause: `ModelIntervalCheckpoint(filepath, interval, verbose=0)` formats the filepath with `step` and every step-log field. Fields such as `observation` or `action` may be arrays/objects, and missing placeholders raise formatting errors.

Fix:

- Use `{step}` as the primary placeholder:

  ```python
  ModelIntervalCheckpoint('weights_{step}.h5f', interval=10000)
  ```

- Ensure the parent directory exists and is writable.
- Avoid placeholders that depend on environment-specific objects.

## Keras backend incompatibility or symbolic Tensor errors

Symptoms:

- DQN/NAF/DDPG construction fails after Keras import even though package imports succeeded.
- Errors mention symbolic tensors, `__len__`, unknown backend, or missing old Keras attributes such as `_keras_shape`.
- Modern Keras 3 or `tf.keras` APIs do not match standalone Keras 2.x expectations.

Cause: keras-rl is legacy standalone-Keras code. Some paths assume old backend behavior and old tensor attributes.

Fix:

1. Select a legacy Keras 2.x-compatible environment.
2. Set the backend before importing Keras, for example via `KERAS_BACKEND` in the process environment.
3. Prefer a proven legacy backend for compile-only validation; Theano CPU is often safer for this code family than TensorFlow-era symbolic tensors.
4. Run:

   ```bash
   python scripts/check_keras_rl_env.py
   ```

5. If imports pass but the smoke fails under TensorFlow, treat that as backend incompatibility and switch backend/environment before debugging model architecture.

## Gym reset/step API version mismatch

Symptoms:

- `ValueError: too many values to unpack` around `env.step(action)`.
- Observations become `(observation, info)` tuples unexpectedly.
- Episodes never terminate because `terminated` and `truncated` were not combined.

Cause: keras-rl expects old Gym API returns: `reset() -> observation` and `step() -> (observation, reward, done, info)`. Modern Gym/Gymnasium uses `reset() -> (observation, info)` and `step() -> (observation, reward, terminated, truncated, info)`.

Fix:

- Wrap the environment with an adapter that returns old shapes.
- Do not rely on a `Processor` alone for five-value `step` returns; `Agent.fit/test` unpacks the result before processor hooks can fix it.
- Use `done = terminated or truncated`.
- If `render(mode='human')` no longer accepts `mode`, adapt `render` in the wrapper.

## Multi-input processor shape mistakes

Symptoms:

- `AssertionError` inside `MultiInputProcessor`.
- Keras says it expected a different number of input arrays.
- NumPy creates object arrays instead of numeric tensors.

Causes:

- `nb_inputs` does not equal the number of modalities per observation.
- Some observations in the replay state window have missing/extra modalities.
- The model input order differs from the observation tuple order.
- Modalities have variable shapes that cannot be stacked into rectangular arrays.
- The model forgot the replay window/time dimension.

Fix:

1. Print one raw observation and one replay state window shape before model training.
2. Ensure every observation is a tuple/list of exactly `nb_inputs` elements.
3. Match Keras model inputs to modalities in the same order.
4. Add padding/resizing in `process_observation` when modality shapes vary.
5. Account for `window_length` in each model input shape.
6. Use a tiny `process_state_batch` fixture before full training:

   ```python
   processed = processor.process_state_batch([state_window_a, state_window_b])
   assert len(processed) == nb_inputs
   ```

## Whitening normalizer gives inconsistent evaluation results

Cause: `WhiteningNormalizerProcessor` updates running statistics during `process_state_batch`, but model weights do not include those statistics.

Fix:

- Save the normalizer state alongside weights.
- Load the normalizer state before `test` or deployment.
- Avoid updating whitening statistics during evaluation if you need a frozen training distribution; subclass or control the processor accordingly.

## `huber_loss` raises unknown backend

Cause: the helper implements TensorFlow and Theano branches only.

Fix:

- Use a legacy TensorFlow or Theano backend.
- If running on a different backend, provide an equivalent loss implementation in your project code rather than relying on `rl.util.huber_loss`.

## `clone_model` fails with custom layers or losses

Cause: Keras model config deserialization cannot resolve custom objects.

Fix:

```python
clone = clone_model(model, custom_objects={'MyLayer': MyLayer, 'my_loss': my_loss})
```

Then compile the clone separately if needed. Remember that optimizer training state is not copied by `clone_optimizer`.
