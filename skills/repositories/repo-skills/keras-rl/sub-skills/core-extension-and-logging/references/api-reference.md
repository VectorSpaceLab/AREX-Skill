# Core extension and logging API reference

This reference summarizes the shared keras-rl APIs that every concrete agent family uses. Use it with a legacy Keras 2.x installation and verify the selected backend before running expensive training.

## Compatibility baseline

- Package identity: keras-rl 0.4.x exposes the public package as `rl`.
- Primary dependency: standalone `keras>=2.0.7`, not modern Keras 3 and not `tf.keras` as a drop-in replacement.
- Public guidance: select and verify a legacy Keras backend before first importing Keras. Theano CPU is a conservative choice for compile-only checks. TensorFlow-era stacks can import yet still fail inside legacy symbolic-tensor checks during agent construction.
- Optional packages are not optional at every import boundary: `rl.callbacks` imports `wandb` at module import time in this code line, so missing W&B can break callback/core imports even when you did not instantiate `WandbLogger`.

## Shared `Agent` lifecycle API

All concrete keras-rl agents inherit the shared lifecycle from `rl.core.Agent`.

| API | Verified signature | Purpose |
| --- | --- | --- |
| `Agent.fit` | `fit(self, env, nb_steps, action_repetition=1, callbacks=None, verbose=1, visualize=False, nb_max_start_steps=0, start_step_policy=None, log_interval=10000, nb_max_episode_steps=None)` | Train for a fixed number of agent steps and return a Keras `History`. |
| `Agent.test` | `test(self, env, nb_episodes=1, action_repetition=1, callbacks=None, visualize=True, nb_max_episode_steps=None, nb_max_start_steps=0, start_step_policy=None, verbose=1)` | Run evaluation episodes and return a Keras `History`. |
| `Agent.compile` | `compile(self, optimizer, metrics=[])` | Compile the concrete agent and its internal Keras models. Concrete agents may specialize the signature. |
| `load_weights` | `load_weights(self, filepath)` | Load HDF5 weights through the concrete agent. |
| `save_weights` | `save_weights(self, filepath, overwrite=False)` | Save HDF5 weights through the concrete agent. |
| `layers` | property | Return the concrete agent's underlying Keras layers. |
| `metrics_names` | property | Names that correspond to values returned by `backward`; these feed loggers and `History`. |

### Compile gate

`fit` and `test` both check `self.compiled` and raise a `RuntimeError` if the concrete agent has not been compiled. Always call the concrete agent's `compile(...)` before `fit(...)`, `test(...)`, checkpointing workflows that require a model, or metric/logging workflows that depend on `metrics_names`.

### `fit` semantics

`fit` performs the following sequence:

1. Validate the compile gate and `action_repetition >= 1`.
2. Set `self.training = True`.
3. Copy user callbacks, then append built-ins based on flags:
   - `verbose == 1`: append `TrainIntervalLogger(interval=log_interval)`.
   - `verbose > 1`: append `TrainEpisodeLogger()`.
   - `visualize=True`: append `Visualizer()`.
   - Always append a Keras `History`.
4. Wrap callbacks in `rl.callbacks.CallbackList`, set the agent as the callback model, set the environment, set `params={'nb_steps': nb_steps}`, call agent `_on_train_begin()`, then `callbacks.on_train_begin()`.
5. For every episode: reset agent state, call `env.reset()`, deep-copy observations, then optionally run random start steps using either `env.action_space.sample()` or `start_step_policy(observation)`.
6. For every agent step: call `forward(observation)`, optionally process the action, repeat the same action `action_repetition` times, accumulate numeric `info` fields, optionally force terminal at `nb_max_episode_steps`, call `backward(reward, terminal=done)`, and emit callback step logs.
7. At terminal state, call one extra `forward(observation)` and `backward(0., terminal=False)` before episode-end callbacks. This convention lets the agent observe the terminal transition before reset.
8. Catch `KeyboardInterrupt`, mark `did_abort=True`, and still call train-end callbacks and agent `_on_train_end()`.

Important knobs:

- `nb_steps` counts agent decision/update steps, not raw environment actions when `action_repetition > 1`.
- `nb_max_episode_steps` force-terminates an episode after the configured number of episode steps.
- `nb_max_start_steps` samples a random count uniformly from `[0, nb_max_start_steps)` at the beginning of each episode.
- `start_step_policy` receives the current processed observation and returns an action used only during start steps.
- Old-style Gym environments are expected: `reset()` returns only an observation, and `step(action)` returns `(observation, reward, done, info)`.

### `test` semantics

`test` mirrors the train loop with these differences:

- Validates compile gate and `action_repetition >= 1`.
- Sets `self.training = False` and resets `self.step = 0`.
- Uses `params={'nb_episodes': nb_episodes}`.
- Appends `TestLogger()` when `verbose >= 1`.
- Defaults `visualize=True`, so disable it explicitly in headless or CI contexts: `agent.test(env, nb_episodes=..., visualize=False)`.
- Calls `callbacks.on_train_begin()`/`on_train_end()` for callback compatibility even though the method is evaluation.
- Runs exactly `nb_episodes` episodes unless the environment or callback raises.

## Processor API

`rl.core.Processor` is the coupling layer between an environment and an agent. Pass a processor to a concrete agent constructor with `processor=...` when the agent accepts standard `Agent` kwargs.

| Hook/property | Default behavior | When to override |
| --- | --- | --- |
| `process_observation(self, observation)` | Return observation unchanged. | Convert images, normalize scalars, unwrap modern Gym reset tuples, reorder axes, or cast dtypes before memory/model use. |
| `process_reward(self, reward)` | Return reward unchanged. | Clip rewards, rescale rewards, or convert backend-specific scalar types. |
| `process_info(self, info)` | Return info unchanged. | Remove non-numeric values that break log aggregation or expose only selected diagnostics. |
| `process_action(self, action)` | Return action unchanged. | Convert discrete indexes to environment-native actions or clip/scale continuous actions. |
| `process_step(self, observation, reward, done, info)` | Calls `process_observation`, `process_reward`, and `process_info`, then returns `(observation, reward, done, info)`. | Override only when fields must be coupled, such as adapting Gymnasium's terminated/truncated split before keras-rl sees it. |
| `process_state_batch(self, batch)` | Return batch unchanged. | Convert replay-memory windows to model-ready arrays, normalize/whiten batches, or split multi-input observations. |
| `metrics` | Empty list. | Add metric functions computed by the processor and returned by the concrete agent. |
| `metrics_names` | Empty list. | Provide names for processor metrics so callbacks can label them. |

### Built-in processors

| Class | Verified signature | Behavior | Pitfalls |
| --- | --- | --- | --- |
| `rl.processors.MultiInputProcessor` | `MultiInputProcessor(nb_inputs)` | Converts a batch of state windows from per-time-step tuples into one NumPy array per model input. | Each observation in each state window must be a tuple/list of exactly `nb_inputs` modalities. The model must have the same number of Keras inputs. |
| `rl.processors.WhiteningNormalizerProcessor` | `WhiteningNormalizerProcessor()` | Lazily creates a `WhiteningNormalizer` for `batch.shape[1:]`, updates it with every processed state batch, then returns whitened values. | The normalizer state is not automatically saved with model weights; persist it yourself if needed for reproducible evaluation. |

## Environment API

`rl.core.Env` and `rl.core.Space` are thin abstract classes modeled after the older OpenAI Gym API.

| Class/API | Expected contract |
| --- | --- |
| `Env.step(action)` | Return exactly `(observation, reward, done, info)`. |
| `Env.reset()` | Return exactly the initial observation, not `(observation, info)`. |
| `Env.render(mode='human', close=False)` | Render side effects; `Visualizer` calls `render(mode='human')` after each action. |
| `Env.close()` | Release resources. |
| `Env.seed(seed=None)` | Seed the environment and return/record seed information if needed. |
| `Env.configure(*args, **kwargs)` | Optional runtime configuration. |
| `Space.sample(seed=None)` | Return one valid random element. Used by random start steps when no `start_step_policy` is supplied. |
| `Space.contains(x)` | Return whether `x` is a valid element. |

For modern Gym/Gymnasium environments, wrap the environment so keras-rl sees the old return shapes.

## Callback and logging API

### Callback dispatch

`rl.callbacks.Callback` extends Keras callbacks with environment and RL-specific hooks:

- `_set_env(self, env)`
- `on_episode_begin(self, episode, logs={})`
- `on_episode_end(self, episode, logs={})`
- `on_step_begin(self, step, logs={})`
- `on_step_end(self, step, logs={})`
- `on_action_begin(self, action, logs={})`
- `on_action_end(self, action, logs={})`

`CallbackList` dispatches these hooks to every callback. If a callback lacks `on_episode_*`, it falls back to Keras `on_epoch_*`. If it lacks `on_step_*`, it falls back to Keras `on_batch_*`. This lets you mix keras-rl callbacks and ordinary Keras callbacks.

### Built-in callbacks

| Callback | Verified signature | Use |
| --- | --- | --- |
| `TestLogger` | `TestLogger()` | Print reward and steps after each test episode. Added by `Agent.test(..., verbose>=1)`. |
| `TrainEpisodeLogger` | `TrainEpisodeLogger()` | Print detailed per-episode training summaries when `fit(..., verbose>1)`. |
| `TrainIntervalLogger` | `TrainIntervalLogger(interval=10000)` | Print interval progress and mean reward/metrics when `fit(..., verbose=1)`. |
| `FileLogger` | `FileLogger(filepath, interval=None)` | Accumulate episode-level metrics and save them as JSON at train end and optionally during training. |
| `Visualizer` | `Visualizer()` | Call `env.render(mode='human')` after each action. Added by `visualize=True`. |
| `ModelIntervalCheckpoint` | `ModelIntervalCheckpoint(filepath, interval, verbose=0)` | Every `interval` environment steps, call `self.model.save_weights(formatted_filepath, overwrite=True)`. |
| `WandbLogger` | `WandbLogger(**kwargs)` | Initialize W&B and log episode metrics. Defaults include `project='keras-rl'` and `anonymous='allow'`. |

### Callback logs

Training step logs include:

- `action`
- `observation`
- `reward`
- `metrics`
- `episode`
- `info` with numeric values accumulated across repeated actions

Training episode logs include:

- `episode_reward`
- `nb_episode_steps`
- `nb_steps`

Test step logs include:

- `action`
- `observation`
- `reward`
- `episode`
- `info`

Test episode logs include:

- `episode_reward`
- `nb_steps`

### `FileLogger` JSON schema expectations

`FileLogger` writes one JSON object. Each key maps to a list sorted by episode. The required x-axis key is:

```json
{
  "episode": [0, 1],
  "episode_reward": [1.0, 1.5],
  "nb_episode_steps": [10, 12],
  "nb_steps": [10, 22],
  "duration": [0.1, 0.2]
}
```

Additional keys come from `model.metrics_names` and episode logs. Every list should have the same length as `episode`. NumPy scalar values are converted to native JSON-compatible values by converting through arrays. The bundled visualizer requires this `episode` key.

### `ModelIntervalCheckpoint` filepath formatting

`ModelIntervalCheckpoint` formats `filepath` with `step=self.total_steps` and all entries from the current step logs:

```python
ModelIntervalCheckpoint('weights_{step}.h5f', interval=10000, verbose=1)
```

Use only fields that are present and safe to format. `{step}` is the most stable placeholder. Complex objects such as observations/actions may not make useful filenames.

### `WandbLogger` behavior

`WandbLogger` calls `wandb.init(**kwargs)` in its constructor and logs in `on_episode_end`. It also attempts to store environment and agent internals in W&B config at train begin. Use it only when `wandb` is installed and the environment object exposes metadata that W&B can serialize. Set W&B offline/disabled environment variables when you need no network side effects.

## Utility functions

| API | Verified signature | Behavior | Notes |
| --- | --- | --- | --- |
| `rl.util.clone_model` | `clone_model(model, custom_objects={})` | Reconstruct a Keras model from config and copy weights. | Compile the clone separately if you need training/evaluation methods. Pass `custom_objects` for custom layers/losses. |
| `rl.util.clone_optimizer` | `clone_optimizer(optimizer)` | If given a string, returns `keras.optimizers.get(...)`; otherwise serializes/deserializes the optimizer config. | Optimizer state such as accumulated moments is not copied; this is a config clone. |
| `rl.util.huber_loss` | `huber_loss(y_true, y_pred, clip_value)` | Return a backend tensor for Huber loss. `clip_value` must be positive; `np.inf` selects squared loss. | Supports TensorFlow and Theano backends in this legacy code. Unknown backends raise `RuntimeError`. |
| `rl.util.WhiteningNormalizer` | `WhiteningNormalizer(shape, eps=0.01, dtype=np.float64)` | Tracks running mean/std, and provides `normalize`, `denormalize`, and `update`. | `update(x)` accepts `x` shaped either as one sample or as a batch whose trailing shape equals `shape`. |

`WhiteningNormalizer` stores `_sum`, `_sumsq`, `_count`, `mean`, and `std`. Persist these fields yourself when a trained policy depends on whitening.
