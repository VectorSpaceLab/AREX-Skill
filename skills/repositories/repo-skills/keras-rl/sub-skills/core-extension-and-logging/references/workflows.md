# Core extension and logging workflows

Use these workflows for shared keras-rl surfaces. For concrete agent construction, route to the discrete or continuous sub-skill first, then return here for lifecycle, processor, callback, utility, and compatibility details.

## Workflow: run a safe `fit` or `test` lifecycle

1. Verify package/backend compatibility before building the agent:

   ```bash
   python scripts/check_keras_rl_env.py --no-smoke
   ```

   If you already selected a legacy backend, set the backend before the first Keras import in the process.

2. Build the concrete agent through the appropriate algorithm sub-skill.
3. Call the concrete agent's `compile(...)` exactly as that agent requires.
4. Prepare an old-Gym-compatible environment:
   - `reset()` returns only an observation.
   - `step(action)` returns `(observation, reward, done, info)`.
   - `action_space.sample()` exists if you use random start steps without a custom `start_step_policy`.
5. Choose lifecycle options deliberately:
   - Use `visualize=False` for headless/CI runs.
   - Keep `action_repetition >= 1`.
   - Use `nb_max_episode_steps` to cap runaway episodes.
   - Use `nb_max_start_steps` with either a safe `start_step_policy` or a valid environment action space.
6. Add callbacks only after confirming optional dependencies:

   ```python
   from rl.callbacks import FileLogger, ModelIntervalCheckpoint

   callbacks = [
       FileLogger('training_log.json', interval=10),
       ModelIntervalCheckpoint('weights_{step}.h5f', interval=10000, verbose=1),
   ]
   history = agent.fit(env, nb_steps=50000, callbacks=callbacks, verbose=1, visualize=False)
   ```

7. Evaluate with visualization disabled unless you have a real display:

   ```python
   history = agent.test(env, nb_episodes=5, visualize=False, verbose=1)
   ```

## Workflow: adapt a modern Gym/Gymnasium environment

keras-rl expects the older Gym API. Use a small adapter instead of modifying the agent.

```python
class OldGymAPIWrapper(object):
    def __init__(self, env):
        self.env = env
        self.action_space = env.action_space
        self.observation_space = getattr(env, 'observation_space', None)
        self.reward_range = getattr(env, 'reward_range', (-float('inf'), float('inf')))

    def reset(self):
        result = self.env.reset()
        if isinstance(result, tuple) and len(result) == 2:
            observation, info = result
            return observation
        return result

    def step(self, action):
        result = self.env.step(action)
        if len(result) == 5:
            observation, reward, terminated, truncated, info = result
            return observation, reward, bool(terminated or truncated), info
        if len(result) == 4:
            return result
        raise ValueError('Expected old 4-tuple or new 5-tuple step result, got {}'.format(len(result)))

    def render(self, mode='human', close=False):
        if close:
            return self.close()
        try:
            return self.env.render(mode=mode)
        except TypeError:
            return self.env.render()

    def close(self):
        return self.env.close()

    def seed(self, seed=None):
        if hasattr(self.env, 'seed'):
            return self.env.seed(seed)
        if hasattr(self.env, 'reset'):
            try:
                self.env.reset(seed=seed)
            except TypeError:
                pass
        return None

    def configure(self, *args, **kwargs):
        if hasattr(self.env, 'configure'):
            return self.env.configure(*args, **kwargs)
        return None
```

Use the wrapper before passing the environment to `fit`/`test`:

```python
env = OldGymAPIWrapper(raw_env)
agent.fit(env, nb_steps=10000, visualize=False)
```

## Workflow: write a custom `Processor`

Use a processor when the agent model and environment disagree about observations, actions, rewards, or batched states.

```python
import numpy as np
from rl.core import Processor

class MyProcessor(Processor):
    def process_observation(self, observation):
        # Example: cast to model-friendly dtype without changing semantics.
        return np.asarray(observation, dtype='float32')

    def process_state_batch(self, batch):
        # Replay memory passes a batch of state windows here.
        batch = np.asarray(batch, dtype='float32')
        return batch / 255.0 if batch.max() > 1.0 else batch

    def process_reward(self, reward):
        return float(np.clip(reward, -1.0, 1.0))

    def process_action(self, action):
        return int(action)
```

Guidelines:

- Put cheap per-observation conversions in `process_observation`.
- Put model-input batch conversions in `process_state_batch` to avoid storing large float replay memories when uint8/int observations are enough.
- Keep `process_action` consistent with the environment's action space.
- If you expose processor metrics, return the same number of values and names through `metrics` and `metrics_names`.

## Workflow: handle multi-input observations

Use `MultiInputProcessor(nb_inputs)` when each environment observation is a tuple/list of modalities and the Keras model has one input per modality.

Expected state-batch shape conceptually:

```python
state_batch = [
    [  # one state window
        (camera_t0, proprio_t0),
        (camera_t1, proprio_t1),
    ],
    [
        (camera_t2, proprio_t2),
        (camera_t3, proprio_t3),
    ],
]
```

After `process_state_batch`, the model receives:

```python
[
    np.array([[camera_t0, camera_t1], [camera_t2, camera_t3]]),
    np.array([[proprio_t0, proprio_t1], [proprio_t2, proprio_t3]]),
]
```

Checklist:

1. `nb_inputs` equals the number of modalities per observation.
2. Every observation in every state window has the same modality count.
3. Your Keras model has the same number of inputs, in the same order.
4. Each modality array can be stacked by NumPy into a rectangular batch.
5. If using replay memory, window length and model input shapes account for the added time/window axis.

## Workflow: use whitening safely

`WhiteningNormalizerProcessor` creates and updates a `WhiteningNormalizer` on the first state batch.

```python
from rl.processors import WhiteningNormalizerProcessor

processor = WhiteningNormalizerProcessor()
agent = SomeAgent(..., processor=processor)
```

Because whitening statistics affect inference, save them separately from model weights:

```python
import pickle

# after training
with open('normalizer.pkl', 'wb') as f:
    pickle.dump(processor.normalizer, f)

# before evaluation
with open('normalizer.pkl', 'rb') as f:
    processor.normalizer = pickle.load(f)
```

Use a stable serialization format you control if long-term compatibility matters. At minimum, persist `mean`, `std`, `_sum`, `_sumsq`, `_count`, `shape`, `eps`, and `dtype`.

## Workflow: capture JSON logs and checkpoints

```python
from rl.callbacks import FileLogger, ModelIntervalCheckpoint

callbacks = [
    FileLogger('run_log.json', interval=5),
    ModelIntervalCheckpoint('weights_{step}.h5f', interval=1000, verbose=1),
]
agent.fit(env, nb_steps=20000, callbacks=callbacks, verbose=1, visualize=False)
```

Tips:

- Use `{step}` in checkpoint filenames. Other placeholders come from step logs and may contain arrays or objects unsuitable for filenames.
- `FileLogger(interval=N)` writes at train end and also on episode numbers divisible by `N`; episode numbering starts at `0`.
- `FileLogger` records episode-level aggregates. It is not a per-step trace logger.
- Keep the log path and checkpoint path in a writable directory.

## Workflow: visualize a `FileLogger` JSON

Use the bundled helper instead of depending on the original examples tree:

```bash
python scripts/visualize_keras_rl_log.py run_log.json --output run_log.png
```

For interactive display, omit `--output` only when a display is available:

```bash
python scripts/visualize_keras_rl_log.py run_log.json
```

The helper validates that:

- the file is JSON,
- the top-level value is an object,
- the object has an `episode` list,
- selected metrics have the same length as `episode`, and
- there is at least one metric key to plot.

## Workflow: use W&B logging without surprise side effects

`WandbLogger` initializes W&B when constructed, and `rl.callbacks` imports `wandb` when the module loads. If you need W&B logging:

```python
from rl.callbacks import WandbLogger

callbacks = [WandbLogger(project='my-project', anonymous='allow')]
agent.fit(env, nb_steps=50000, callbacks=callbacks, visualize=False)
```

If you need no network writes, configure W&B offline/disabled according to W&B's environment variables before Python starts. If you do not need W&B but imports fail, install a compatible `wandb` package or use an environment where `rl.callbacks` can import.

## Workflow: clone models and optimizers safely

```python
from rl.util import clone_model, clone_optimizer

model_clone = clone_model(model, custom_objects={'MyLayer': MyLayer})
model_clone.compile(optimizer='sgd', loss='mse')

optimizer_clone = clone_optimizer(optimizer)
```

Notes:

- `clone_model` copies model weights but not compile state.
- `clone_optimizer` copies optimizer configuration, not accumulated optimizer state.
- Custom layers/losses/activations need `custom_objects` for model cloning.

## Workflow: use `huber_loss`

```python
import numpy as np
from rl.util import huber_loss

loss_tensor = huber_loss(y_true, y_pred, clip_value=1.0)
squared_tensor = huber_loss(y_true, y_pred, clip_value=np.inf)
```

`clip_value` must be positive. Unknown Keras backends raise `RuntimeError`; choose a legacy TensorFlow or Theano backend when using this helper.

## Workflow: check environment compatibility

Run the bundled environment checker in the environment where you plan to use keras-rl:

```bash
python scripts/check_keras_rl_env.py
```

For import-only checks:

```bash
python scripts/check_keras_rl_env.py --no-smoke
```

For machine-readable output:

```bash
python scripts/check_keras_rl_env.py --json
```

Interpretation:

- Import failures before smoke usually mean missing/modern dependencies, missing `wandb`, or incompatible Keras/backend versions.
- Smoke failures under TensorFlow can be a legacy symbolic Tensor issue rather than a model-design error.
- If the smoke fails under a modern Keras stack, do not continue to long training until you have proven a compatible legacy Keras 2.x environment.
