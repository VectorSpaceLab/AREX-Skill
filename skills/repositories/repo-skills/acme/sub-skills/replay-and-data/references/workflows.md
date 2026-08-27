# Replay and Data Workflows

This reference gives practical workflows for selecting Acme replay adders, creating Reverb datasets, adapting offline data, and connecting learner iterators.

## Workflow: Choose an Adder Family

1. Identify the learner input contract.
   - Feed-forward update over individual SARSA-style transitions: start with `NStepTransitionAdder`.
   - Recurrent network, burn-in, sequence loss, R2D2-style unroll, or overlapping windows: start with `SequenceAdder`.
   - Full-episode imitation, return computation, episode-level filtering, or variable-length demonstrations: start with `EpisodeAdder` or an offline dataset adapter.
   - Multiple tables/patterns from one actor stream, or structured-writer configs from an algorithm builder: start with `StructuredAdder`.
2. Identify the replay backend.
   - Online Acme agents commonly use Reverb tables and `make_reverb_dataset`.
   - Offline examples often use TFDS/RLDS datasets, batched TensorFlow datasets, `JaxInMemoryRandomSampleIterator`, or `reverb_utils.transition_to_replaysample` when a learner expects replay samples.
3. Make the table signature from the same family that will write the data.
   - Transition table: `NStepTransitionAdder.signature(environment_spec, extras_spec)`.
   - Sequence table: `SequenceAdder.signature(environment_spec, extras_spec, sequence_length)`.
   - Episode table: `EpisodeAdder.signature(environment_spec, extras_spec, sequence_length=max_sequence_length)`.
   - Structured table: `reverb.structured_writer.infer_signature(configs, step_spec)`.
4. Keep algorithm-specific table sizing, rate limiters, priorities, and iterator transformations with the relevant `jax-agents` or `tf-agents` sub-skill if the algorithm builder already owns those choices.

## Workflow: Transition Replay for Feed-Forward Learners

Use `NStepTransitionAdder` when the learner expects `types.Transition` items.

```python
import reverb
from acme.adders import reverb as adders
from acme.datasets import reverb as datasets

replay_table = reverb.Table(
    name=adders.DEFAULT_PRIORITY_TABLE,
    sampler=reverb.selectors.Uniform(),
    remover=reverb.selectors.Fifo(),
    max_size=100_000,
    rate_limiter=reverb.rate_limiters.MinSize(1),
    signature=adders.NStepTransitionAdder.signature(environment_spec, extras_spec),
)
server = reverb.Server([replay_table])
client = reverb.Client(f"localhost:{server.port}")
adder = adders.NStepTransitionAdder(client, n_step=1, discount=0.99)
dataset = datasets.make_reverb_dataset(
    server_address=f"localhost:{server.port}",
    batch_size=256,
    prefetch_size=4,
)
iterator = iter(dataset)
```

Decision notes:

- Use `n_step > 1` when the algorithm expects n-step returns to be computed at insert time.
- The `discount` argument is the agent's additional discount factor used in cumulative return/discount computation.
- Extras are from the first step in the n-step window. If the learner needs recurrent state at every time step, use sequences instead.
- Table priorities default to `1.0`; pass `priority_fns={table_name: fn}` if the adder, not the learner, must compute insert priorities.

## Workflow: Sequence Replay for Recurrent Learners

Use `SequenceAdder` when the learner consumes trajectory fields with a time axis.

```python
from acme.adders import reverb as adders

sequence_length = 80
period = 40
signature = adders.SequenceAdder.signature(
    environment_spec,
    extras_spec,
    sequence_length=sequence_length,
)
adder = adders.SequenceAdder(
    client,
    sequence_length=sequence_length,
    period=period,
    end_of_episode_behavior=adders.EndBehavior.ZERO_PAD,
)
```

Decision notes:

- `period < sequence_length` creates overlapping unrolls; use this for recurrent burn-in/learning overlap.
- `period == sequence_length` creates non-overlapping windows; use when each environment step should appear once.
- `ZERO_PAD` creates fixed-length final sequences but inserts zero-filled artificial tail steps.
- `TRUNCATE` avoids artificial steps but downstream code must accept shorter final trajectories or padding in the dataset pipeline.
- `CONTINUE` crosses episode boundaries; use only when the learner explicitly handles `start_of_episode` markers.
- If extras contain recurrent state, action log-probs, or behavior-policy metadata, define `extras_spec` exactly and pass the same nested structure on every `add` call.

### Difficult recurrent case: extras plus overlap

For a recurrent learner with hidden-state extras and `sequence_length=80`, `period=40`:

1. Keep hidden-state extras in the per-step `extras` argument only if the learner expects them in replay.
2. Build `extras_spec` with the same nested keys and leaf shapes/dtypes as the hidden-state extras.
3. Use `SequenceAdder.signature(..., extras_spec, sequence_length=80)` for the table.
4. Choose `period=40` to produce 50% overlap. Do not use `NStepTransitionAdder`; it keeps only the first extras in each n-step transition and does not preserve a time axis.
5. Prefer `ZERO_PAD` when the learner requires fixed `T=80`; prefer `TRUNCATE` when the dataset pipeline pads/masks variable tails.
6. Check the learner's expected input under the relevant algorithm sub-skill before changing period or end behavior, because those are usually algorithm-specific.

## Workflow: Episode Replay

Use `EpisodeAdder` for complete trajectories:

```python
from acme.adders import reverb as adders

max_sequence_length = 1001
signature = adders.EpisodeAdder.signature(
    environment_spec,
    extras_spec,
    sequence_length=max_sequence_length,
)
adder = adders.EpisodeAdder(
    client,
    max_sequence_length=max_sequence_length,
)
```

Decision notes:

- `max_sequence_length` counts observations in the episode trajectory. Adding a transition that would exceed the limit raises `ValueError`.
- Provide `padding_fn(shape, dtype) -> np.ndarray` if the table/learner requires fixed-length episodes and short episodes need non-default padding.
- Episodes are written at episode end; no replay items are available mid-episode from this adder.

## Workflow: Structured Writer Replay

Use `StructuredAdder` when one appended step stream should produce custom trajectory patterns.

```python
from acme.adders import reverb as adders
from reverb import structured_writer as sw

step_spec = adders.create_step_spec(environment_spec, extras_spec)
configs = adders.create_sequence_config(
    step_spec=step_spec,
    sequence_length=sequence_length,
    period=period,
    table=adders.DEFAULT_PRIORITY_TABLE,
    end_of_episode_behavior=adders.EndBehavior.TRUNCATE,
)
signature = sw.infer_signature(configs, step_spec)
adder = adders.StructuredAdder(
    client=client,
    max_in_flight_items=0,
    configs=configs,
    step_spec=step_spec,
)
```

Decision notes:

- `StructuredAdder` validates configs at construction by inferring signatures.
- `create_sequence_config` does not support `ZERO_PAD` or `CONTINUE`; use `TRUNCATE` and pad/mask in the learner pipeline when needed.
- `create_n_step_transition_config` writes raw reward/discount trajectories, not precomputed n-step returns. Convert with `n_step_from_trajectory` in `postprocess` or another dataset transform.
- Use structured configs when the algorithm already supplies Reverb `structured_writer` patterns; otherwise the classic adders are simpler.

## Workflow: Build a Reverb Dataset Iterator

1. Create a Reverb table with a signature matching the inserted item.
2. Start a `reverb.Server` or connect to a server address provided by the experiment layout.
3. Write actor data through the matching adder.
4. Build the learner dataset:

```python
from acme.datasets import reverb as datasets

dataset = datasets.make_reverb_dataset(
    server_address=server_address,
    batch_size=batch_size,
    prefetch_size=4,
    table=adders.DEFAULT_PRIORITY_TABLE,
    postprocess=optional_transform,
)
iterator = iter(dataset)
```

5. Pass `iterator` or `dataset` to the learner according to the algorithm builder.

Use `table={"online": 0.7, "offline": 0.3}` to mix Reverb tables. Acme filters non-positive weights and normalizes the rest; at least one positive weight is required.

## Workflow: Add Image Augmentation to Replay Samples

For transition-shaped samples:

```python
from acme.datasets import image_augmentation

transform = image_augmentation.make_transform(
    lambda image: image_augmentation.pad_and_crop(
        image,
        pad_size=4,
        method=image_augmentation.CropType.ALIGNED,
    ),
    transform_next_observation=True,
)
dataset = make_reverb_dataset(..., postprocess=transform)
```

Use `transform_next_observation=False` only when the learner intentionally augments current observations but not next observations. `pad_and_crop` expects image leaves shaped `[..., H, W, C]`.

## Workflow: Adapt Offline Demonstrations from Arrays

When demonstrations are already in arrays or a TensorFlow dataset, shape them into the learner's expected item type rather than forcing them through Reverb.

For feed-forward learners expecting `types.Transition` batches:

```python
from acme import types
import tensorflow as tf

transitions = types.Transition(
    observation=observations[:-1],
    action=actions[:-1],
    reward=rewards[:-1],
    discount=discounts[:-1],
    next_observation=observations[1:],
    extras=extras[:-1] if extras is not None else (),
)
dataset = tf.data.Dataset.from_tensor_slices(transitions)
dataset = dataset.batch(batch_size, drop_remainder=True).prefetch(tf.data.AUTOTUNE)
iterator = iter(dataset)
```

For a JAX learner that benefits from host-side random sampling:

```python
from acme.datasets import tfds as acme_tfds

random_iterator = acme_tfds.JaxInMemoryRandomSampleIterator(
    dataset,
    key=random_key,
    batch_size=batch_size,
)
```

For a learner that expects `reverb.ReplaySample` even in offline mode:

```python
from acme.utils import reverb_utils
sample_iterator = (reverb_utils.transition_to_replaysample(batch) for batch in transition_iterator)
```

Array adaptation checklist:

- The first dimension is the sample/time dimension for `from_tensor_slices`.
- `observation[i + 1]` is the `next_observation` for transition `i`.
- Terminal transitions should have `discount=0.0` unless the algorithm's environment convention differs.
- Keep extras nested structure stable for every sample.
- Batch with `drop_remainder=True` when JAX compilation or sharded training requires fixed leading dimensions.

## Workflow: Load TFDS/RLDS Demonstrations

Use Acme's TFDS helpers for RLDS datasets such as D4RL-style examples:

```python
from acme.datasets import tfds as acme_tfds

transitions = acme_tfds.get_tfds_dataset(
    dataset_name,
    num_episodes=num_demonstrations,
    env_spec=environment_spec,
)
demonstrations = acme_tfds.JaxInMemoryRandomSampleIterator(
    transitions,
    key=random_key,
    batch_size=batch_size,
)
```

Notes:

- `env_spec` is accepted for compatibility but not used by `load_tfds_dataset` in this version.
- `get_tfds_dataset` maps adjacent RLDS steps into `types.Transition` and computes `discount` as `1.0 - is_terminal(next_step)`.
- `JaxInMemoryRandomSampleIterator` loads the entire dataset into memory. For large datasets, prefer streaming `tf.data` pipelines or algorithm-specific offline data loaders if available.
- If using device sharding, ensure `batch_size` is divisible by the number of devices and accept that some final elements may be dropped to make shards even.

## Workflow: Convert Sequence Samples to Transitions

When a learner wants transitions but replay data is sequence-shaped:

```python
from acme.utils import reverb_utils

transition_batch = reverb_utils.replay_sample_to_sars_transition(
    sample,
    is_sequence=True,
    strip_last_transition=True,
    flatten_batch=True,
)
```

Use `strip_last_transition=True` because sequence conversion forms `next_observation` by rolling the observation time axis; the final rolled next observation is invalid. Use `flatten_batch=True` to merge batch and time dimensions after stripping.

## Workflow: Connect the Learner Iterator

Acme learners are designed to consume dataset iterators, typically TensorFlow dataset iterators or Python iterators that yield transition/sequence batches.

1. Inspect the learner or builder constructor for names like `dataset`, `iterator`, `demonstrations`, `demonstration_dataset`, or `make_demonstrations`.
2. Match the yielded element type:
   - `types.Transition`: transition batch.
   - `reverb.ReplaySample`: sample wrapper with `.data` and `.info`.
   - `Step`/`Trajectory`: sequence or episode fields.
3. Ensure batch/static shape expectations align with the learner backend.
   - JAX/XLA usually prefers fixed batch sizes and stable nested structures.
   - TensorFlow graph mode usually needs stable dtypes and rank.
4. Keep algorithm-specific iterator transforms with `jax-agents` or `tf-agents` if the transform is tied to a particular learner implementation.

## Use the Bundled Structure Helper

Before choosing an adder for custom data, describe the data and learner hints in JSON:

```json
{
  "observation": {"pixels": {"shape": [84, 84, 3], "dtype": "uint8"}},
  "action": {"shape": [], "dtype": "int32"},
  "reward": {"shape": [], "dtype": "float32"},
  "discount": {"shape": [], "dtype": "float32"},
  "extras": {"core_state": {"shape": [512], "dtype": "float32"}},
  "learner": {"recurrent": true, "sequence_length": 80, "period": 40}
}
```

Run:

```bash
python scripts/describe_replay_structure.py replay_description.json
```

The helper validates the nested leaves and prints a recommended family. It does not import Reverb, TensorFlow, JAX, or Acme, so it is safe in minimal environments.
