# Save, Load, and Export

## Checkpoint-style saving during training

Pass `saver` when constructing a trainable agent or agent spec:

```python
agent = dict(
    agent='ppo',
    network='auto',
    batch_size=10,
    saver=dict(directory='model', frequency=10, max_checkpoints=5),
)
```

When a `Runner` owns the agent, close the runner so Tensorforce flushes resources.

## Explicit save and load

```python
agent.save(directory='checkpoints', format='numpy')
restored = Agent.load(directory='checkpoints', format='numpy', environment=environment)
```

Load with the target environment when the saved spec lacks or must reconcile `states`, `actions`, or `max_episode_timesteps`. If a saver dict is in the spec, Tensorforce may restore from checkpoint automatically; otherwise `Agent.load(...).restore(...)` behavior is used internally.

Formats:

| Format | Use for | Notes |
|---|---|---|
| TensorFlow checkpoint/default | Full TensorFlow model state | Best for continuing training in Python/Tensorforce. |
| `numpy` | Lightweight weights archive | Requires matching architecture/spec. |
| `hdf5` | HDF5 weight persistence | Requires h5py and matching architecture/spec. |
| `saved-model` | TensorFlow act-only serving/export | Not a full training checkpoint. Use for inference/serving. |

## SavedModel export

`agent.save(directory='saved-model', format='saved-model')` exports an optimized act-only TensorFlow SavedModel. Treat it as deployment/inference-only unless Tensorforce documentation for the selected version says otherwise.

When loading with TensorFlow directly, batch inputs and unbatch outputs. For internal/recurrent states, carry `internals` through the SavedModel `act` signature. For action masks, pass an auxiliaries dict with mask arrays.

## Save best agent through Runner

`Runner.run(..., save_best_agent='directory')` is tied to evaluation score. Use it only when `Runner` has an evaluation setup and enough episodes to produce meaningful scores.
