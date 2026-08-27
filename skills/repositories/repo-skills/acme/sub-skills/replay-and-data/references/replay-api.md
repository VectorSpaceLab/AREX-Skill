# Replay API Reference

This reference summarizes the Acme replay/data APIs relevant to adders, Reverb-backed datasets, offline datasets, numpy iterators, image augmentation, and Reverb utility conversions.

## Package and Dependency Facts

- Distribution: `dm-acme` version `0.4.1`; import package: `acme`.
- Core install requirements include `absl-py`, `dm-env`, `dm-tree`, `numpy`, `pillow`, and `typing-extensions`.
- Reverb, TensorFlow, TFDS/RLDS, JAX, Haiku/Flax/Optax/RLax, Sonnet/TRFL, and Launchpad belong to optional runtime stacks. Do not assume real Reverb server, TensorFlow dataset, JAX, or TFDS execution works unless those extras are installed and smoke-tested.
- The APIs below are source-backed; core signatures were verified, but full Reverb/TFDS runtime execution was not verified.

## Base Adder Contract

All Acme adders implement `acme.adders.base.Adder`:

| Method | Signature | Contract |
| --- | --- | --- |
| `add_first` | `add_first(timestep: dm_env.TimeStep)` | Start a new trajectory from the first timestep. The timestep should satisfy `timestep.first()` for Reverb adders. |
| `add` | `add(action: types.NestedArray, next_timestep: dm_env.TimeStep, extras: types.NestedArray = ())` | Append the action taken at the previous observation and the resulting `next_timestep`; optional `extras` must keep the same nested structure as the table signature. |
| `reset` | `reset()` or Reverb variants with `timeout_ms` | Clear the local adder/writer buffer, ending any active episode. |

Important semantics:

- `add(action, next_timestep, extras)` receives the action and the resulting timestep after the environment step, not the previous timestep.
- Reverb adders enforce `add_first` before `add`; otherwise they raise a `ValueError`.
- At episode end, Reverb adders append a final zero-filled row for open fields so learner-side structures remain aligned.
- `extras` are optional. Empty tuple `()` means no extras; non-empty nested extras are written as the `extras` field and must match `extras_spec` when signatures are used.

## Adder Wrappers

| API | Purpose | Notes |
| --- | --- | --- |
| `acme.adders.wrappers.ForkingAdder(adders)` | Fan one actor stream into several adders. | Forwards `reset`, `add_first`, and `add` to every wrapped adder. Use when multiple replay tables need different representations. |
| `acme.adders.wrappers.IgnoreExtrasAdder(adder)` | Drop extras before forwarding. | Useful when an actor produces extras but a legacy adder/table signature does not accept them. |

## Reverb Common Types

`acme.adders.reverb` re-exports the main classes/functions:

- `DEFAULT_PRIORITY_TABLE = 'priority_table'`.
- `Step(observation, action, reward, discount, start_of_episode, extras=())`.
- `Trajectory` is currently an alias of `Step`.
- `PriorityFnInput(observations, actions, rewards, discounts, start_of_episode, extras)`.
- `PriorityFn` and `PriorityFnMapping`: mapping from table name to optional priority function. If omitted, Acme writes priority `1.0` into `DEFAULT_PRIORITY_TABLE`.
- `ReverbAdder(client, max_sequence_length, max_in_flight_items, delta_encoded=False, priority_fns=None, validate_items=True)` is the base for concrete Reverb adders.

`ReverbAdder.signature(environment_spec, extras_spec=())` returns a nested `Step` of `tf.TensorSpec` leaves derived from an `acme.specs.EnvironmentSpec` and an optional extras spec.

## Reverb Adder Families

### `NStepTransitionAdder`

Signature:

```python
from acme.adders import reverb as adders
adder = adders.NStepTransitionAdder(
    client,
    n_step: int,
    discount: float,
    priority_fns=None,
    max_in_flight_items=5,
)
```

Use for feed-forward transition learners. With `n_step == 1`, replay data has this logical shape:

```text
Transition(
  observation=s_t,
  action=a_t,
  reward=r_t,
  discount=d_t,
  next_observation=s_{t+1},
  extras=e_t,
)
```

With `n_step > 1`, the adder computes discounted returns and total discounts over up to `n_step` environment transitions. It also emits shorter transitions at episode starts and ends. Extras are the first extras in the transition window (`e_t`), not the extras at the final step.

`NStepTransitionAdder.signature(environment_spec, extras_spec=())` returns a `types.Transition` signature with `observation`, `action`, broadcasted `reward`, broadcasted `discount`, `next_observation`, and `extras`.

### `SequenceAdder`

Signature:

```python
adder = adders.SequenceAdder(
    client,
    sequence_length: int,
    period: int,
    delta_encoded=False,
    priority_fns=None,
    max_in_flight_items=2,
    end_of_episode_behavior=None,
    validate_items=True,
)
```

Use for recurrent learners and sequence losses. It writes fixed-length sequences every `period` actor steps:

- `period < sequence_length`: overlapping unrolls.
- `period == sequence_length`: non-overlapping chunks.
- `period > sequence_length`: gaps between written chunks; use only when intentional.

End behavior is controlled by `acme.adders.reverb.EndBehavior`:

| Value | Effect |
| --- | --- |
| `WRITE` | Write the current full buffer at episode end; drop episodes shorter than `sequence_length`. |
| `CONTINUE` | Keep the writer across episode boundaries and continue into the next episode. |
| `ZERO_PAD` | Default legacy behavior; pad the final item with zero-filled steps until `sequence_length`. |
| `TRUNCATE` | Write a shorter final item instead of zero-padding. |

Deprecated `pad_end_of_episode`/`break_end_of_episode` map to `ZERO_PAD`, `TRUNCATE`, or `CONTINUE`; prefer `end_of_episode_behavior` for new code.

`SequenceAdder.signature(environment_spec, extras_spec=(), sequence_length=None)` returns a `Trajectory` signature whose fields have leading time dimension `(sequence_length, ...)`, plus `start_of_episode` of shape `(sequence_length,)`.

### `EpisodeAdder`

Signature:

```python
adder = adders.EpisodeAdder(
    client,
    max_sequence_length: int,
    delta_encoded=False,
    priority_fns=None,
    max_in_flight_items=1,
    padding_fn=None,
)
```

Use when the learner consumes complete trajectories. The adder writes only when the episode ends. It raises `ValueError` if adding another transition would exceed `max_sequence_length - 1` actions / `max_sequence_length` observations. If `padding_fn` is provided and an episode is shorter than `max_sequence_length`, the adder pads fields before writing.

`EpisodeAdder.signature(environment_spec, extras_spec=(), sequence_length=None)` returns the same time-major `Trajectory` style as `SequenceAdder.signature`.

### `StructuredAdder`

Signature:

```python
from acme.adders.reverb import structured
step_spec = structured.create_step_spec(environment_spec, extras_spec)
configs = structured.create_sequence_config(step_spec, sequence_length, period)
adder = structured.StructuredAdder(
    client=client,
    max_in_flight_items=0,
    configs=configs,
    step_spec=step_spec,
)
```

Use when Reverb `structured_writer` configs are a better fit than the classic adders:

- One actor stream can write different item patterns into one or more tables without duplicating appended step data.
- The complete step structure must be known at construction time via `create_step_spec`.
- Items receive uniform priority `1.0`; custom priority functions are not supported by `StructuredAdder`.
- The adder does not precompute n-step returns. If using `create_n_step_transition_config`, convert raw trajectories with `n_step_from_trajectory(trajectory, agent_discount)` in the dataset pipeline.

Helpers:

| Helper | Signature | Purpose |
| --- | --- | --- |
| `create_step_spec` | `create_step_spec(environment_spec, extras_spec=())` | Build the full `Step` spec used by `StructuredAdder`. |
| `create_sequence_config` | `create_sequence_config(step_spec, sequence_length, period, table=DEFAULT_PRIORITY_TABLE, end_of_episode_behavior=EndBehavior.TRUNCATE, sequence_pattern=_last_n)` | Generate structured-writer configs equivalent to a sequence adder. `ZERO_PAD` and `CONTINUE` are not supported. |
| `create_n_step_transition_config` | `create_n_step_transition_config(step_spec, n_step, table=DEFAULT_PRIORITY_TABLE)` | Generate configs for raw trajectories that can later be converted to n-step transitions. |
| `n_step_from_trajectory` | `n_step_from_trajectory(trajectory, agent_discount)` | Convert a structured raw trajectory into a `types.Transition`. |

## Replay Table Signatures

Typical Reverb table construction pairs a table signature with the adder family:

```python
import reverb
from acme.adders import reverb as adders

table = reverb.Table(
    name=adders.DEFAULT_PRIORITY_TABLE,
    sampler=reverb.selectors.Uniform(),
    remover=reverb.selectors.Fifo(),
    max_size=100_000,
    rate_limiter=reverb.rate_limiters.MinSize(1),
    signature=adders.NStepTransitionAdder.signature(environment_spec, extras_spec),
)
```

Rules:

- The table signature must describe the item produced by the adder, not the raw environment step unless using `StructuredAdder` with a structured-writer inferred signature.
- `extras_spec` must exactly mirror the structure and leaf shapes/dtypes of `extras` passed to `adder.add`.
- If `validate_items=True`, the Reverb writer fetches and validates against the table signature; mismatches fail close to insertion time.

## Dataset APIs

### Reverb dataset

```python
from acme.datasets import reverb as datasets

dataset = datasets.make_reverb_dataset(
    server_address: str,
    batch_size=None,
    prefetch_size=None,
    table=adders.DEFAULT_PRIORITY_TABLE,
    num_parallel_calls=12,
    max_in_flight_samples_per_worker=None,
    postprocess=None,
)
```

Behavior:

- Returns a `tf.data.Dataset` backed by `reverb.TrajectoryDataset.from_table_signature`.
- `table` can be a string or a `{table_name: weight}` mapping. Non-positive weights are dropped; an all-non-positive mapping raises `ValueError`.
- If `batch_size` is set, the dataset batches with `drop_remainder=True`.
- `postprocess` is applied as `dataset.map(postprocess)` before batching.
- Deprecated kwargs such as `environment_spec`, `extra_spec`, `transition_adder`, and `sequence_length` should not be used; signatures now belong on `reverb.Table`.

### Numpy iterator

```python
from acme.datasets.numpy_iterator import NumpyIterator
iterator = NumpyIterator(tf_dataset)
```

`NumpyIterator` wraps a TensorFlow dataset iterator and converts every nested tensor leaf to a read-only NumPy array via `np.asarray(memoryview(tensor))`. Tests cover scalar datasets and nested dict/tuple/namedtuple structures.

### TFDS / RLDS datasets

```python
from acme.datasets import tfds

episodes = tfds.load_tfds_dataset(dataset_name, num_episodes=None, env_spec=None)
transitions = tfds.get_tfds_dataset(dataset_name, num_episodes=None, env_spec=None)
iterator = tfds.JaxInMemoryRandomSampleIterator(
    transitions,
    key,
    batch_size,
    shard_dataset_across_devices=False,
)
```

Behavior:

- `load_tfds_dataset` loads `tfds.load(dataset_name)['train']` and optionally takes the first `num_episodes`.
- `get_tfds_dataset` converts RLDS episodes into adjacent two-step batches and maps them into `types.Transition` with `observation`, `action`, `reward`, `discount`, and `next_observation`.
- `JaxInMemoryRandomSampleIterator` loads the full dataset into memory, samples batches with replacement, and can optionally shard storage across JAX devices. `batch_size` must be divisible by the number of devices when sharding.

### Image augmentation

```python
from acme.datasets import image_augmentation

aug = image_augmentation.make_transform(
    lambda image: image_augmentation.pad_and_crop(
        image, pad_size=4, method=image_augmentation.CropType.ALIGNED),
    transform_next_observation=True,
)
dataset = make_reverb_dataset(..., postprocess=aug)
```

APIs:

- `CropType.ALIGNED`: random crop aligned to the input image pixel grid.
- `CropType.BILINEAR`: random crop with bilinear resize.
- `pad_and_crop(img, pad_size=4, method=CropType.ALIGNED)` expects image tensors shaped `[..., H, W, C]` and applies symmetric padding on height/width before random cropping.
- `make_transform(observation_transform, transform_next_observation=True)` returns a transform for `reverb.ReplaySample` transition data. If `transform_next_observation=False`, only `observation` is transformed.

## Reverb Utility APIs

| API | Signature | Purpose |
| --- | --- | --- |
| `make_replay_table_from_info` | `make_replay_table_from_info(table_info)` | Rebuild a `reverb.Table` from `reverb_types.TableInfo`, preserving selector, remover, max size, rate limiter, max-times-sampled, and signature. |
| `replay_sample_to_sars_transition` | `replay_sample_to_sars_transition(sample, is_sequence, strip_last_transition=False, flatten_batch=False)` | Convert a `reverb.ReplaySample` into `types.Transition`. For sequence samples, rolls observations along axis 1 to form `next_observation`; optionally strips the invalid final transition and/or flattens batch/time axes. |
| `transition_to_replaysample` | `transition_to_replaysample(transitions)` | Wrap a `types.Transition` in a `reverb.ReplaySample` with dummy `SampleInfo`. Useful when an online algorithm expects replay samples but offline data is already in transition form. |

Sequence conversion caveat: for `is_sequence=True`, the last `next_observation` is produced by rolling the sequence and is not a valid next observation. Use `strip_last_transition=True` if the learner should not see that final invalid transition.

## Expected Shapes by Family

| Family | Replay item data | Typical leading dimensions after batching |
| --- | --- | --- |
| `NStepTransitionAdder` | `types.Transition(observation, action, reward, discount, next_observation, extras)` | Batch dimension added by `tf.data.Dataset.batch`; no time axis unless leaves themselves have one. |
| `SequenceAdder` | `Trajectory/Step` fields: `observation`, `action`, `reward`, `discount`, `start_of_episode`, `extras` | Batch then time: `[B, T, ...]` for leaves after `make_reverb_dataset(..., batch_size=B)`. |
| `EpisodeAdder` | Same `Trajectory/Step` fields across full episode or padded `max_sequence_length` | Batch then episode/time: `[B, T, ...]`; `T` may be fixed by padding or signature. |
| `StructuredAdder` sequence configs | Pattern-defined trajectory from `structured_writer` | Depends on `sw.infer_signature(configs, step_spec)`; common sequence configs match `Trajectory` style. |
| TFDS transition dataset | `types.Transition` from adjacent RLDS steps | Before random sampling, one transition per element; random iterator returns batch leaves. |

## Minimal Collection Loop Skeleton

```python
timestep = environment.reset()
adder.add_first(timestep)

while not timestep.last():
    action = policy(timestep.observation)
    next_timestep = environment.step(action)
    adder.add(action, next_timestep, extras=extras_for_action)
    timestep = next_timestep
```

Keep the basic environment-loop/wrapper details in the root/core workflow guidance. Use this sub-skill for the adder, replay table, dataset, and shape decisions around that loop.
