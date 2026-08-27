# Replay and Data Troubleshooting

Use this guide when Acme replay insertion, Reverb datasets, offline demonstrations, TFDS loading, or learner iterator shapes fail.

## Missing Optional Dependencies

### `ModuleNotFoundError: No module named 'reverb'`

Likely cause: the TensorFlow/Reverb optional stack is not installed. Reverb-backed adders and `acme.datasets.reverb` import `reverb` at module import time.

Fixes:

- Install an Acme extra or environment that includes the TensorFlow/Reverb stack appropriate for the project.
- If the task is only offline array adaptation, avoid Reverb and yield `types.Transition` batches directly.
- If the learner expects `reverb.ReplaySample`, consider `acme.utils.reverb_utils.transition_to_replaysample` around already-batched transitions; this still requires the `reverb` Python package.

### `ModuleNotFoundError: No module named 'tensorflow'`

Likely cause: dataset utilities, table signatures, and image augmentation require TensorFlow.

Fixes:

- Install the TensorFlow-compatible Acme extra for the selected backend.
- For pure NumPy/JAX offline workflows, avoid `make_reverb_dataset`, `image_augmentation`, and `tf.data` wrappers unless TensorFlow is available.
- Keep table signature generation in the environment that has TensorFlow, because `ReverbAdder.signature` returns `tf.TensorSpec` leaves.

### `ModuleNotFoundError: No module named 'tensorflow_datasets'` or `No module named 'rlds'`

Likely cause: TFDS/RLDS offline dataset helpers need optional dataset packages.

Fixes:

- Install the environment/data extra that includes TFDS/RLDS.
- If demonstrations are local arrays or custom files, build a `tf.data.Dataset` or Python iterator directly instead of using `acme.datasets.tfds`.
- Check that the dataset name exists in the installed TFDS catalog and that local TFDS data directories are configured if no network download is allowed.

### `ModuleNotFoundError: No module named 'jax'` or `No module named 'flax'`

Likely cause: `acme.datasets.tfds.JaxInMemoryRandomSampleIterator` imports JAX/Flax utilities.

Fixes:

- Use a JAX-capable environment for JAX offline learners.
- For TensorFlow learners, skip `JaxInMemoryRandomSampleIterator` and use `tf.data.Dataset.batch(...).prefetch(...)` directly.
- If only inspecting data shapes, use the bundled `scripts/describe_replay_structure.py` helper because it has no backend imports.

## Table Signature Mismatch

Common symptoms:

- Reverb insert fails with shape or dtype validation errors.
- Learner receives a different nested structure than expected.
- Extras appear in actor code but not in replay samples.

Root causes and fixes:

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `extras` key missing or unexpected | `extras_spec` omitted but `adder.add(..., extras=...)` passes non-empty extras, or table signature includes extras but actor passes `()` | Make `extras_spec` mirror the runtime extras structure exactly, or wrap with `IgnoreExtrasAdder` if extras should be dropped. |
| Transition table sees sequence fields | Table signature built with `SequenceAdder.signature` but actor uses `NStepTransitionAdder`, or vice versa | Rebuild the table signature from the same adder family that writes items. |
| Reward/discount dtype mismatch | Environment spec reward/discount dtype differs from actual emitted values or n-step broadcasting changes dtype | Normalize environment reward/discount arrays to the spec dtype before insertion. |
| Shape mismatch after batching | Learner expects `[B, ...]` but sequence replay yields `[B, T, ...]`, or learner expects time axis but transition replay lacks it | Choose the correct adder family or add a dataset transform owned by the learner workflow. |
| Validation fails after changing extras | Reverb writer cached an old table signature | Restart the Reverb server/table and create a fresh client/writer with the new signature. |

Debug checklist:

1. Print or inspect the table signature before starting the Reverb server.
2. Compare the signature family against the adder class used by the actor.
3. Validate one example `extras` tree against `extras_spec` leaf-by-leaf for keys, shapes, and dtypes.
4. Confirm `add_first` receives a `dm_env.restart(...)`/first timestep and `add` receives the action plus resulting next timestep.
5. Temporarily keep `validate_items=True` so the writer catches mismatches early.

## `add_first` / Episode Boundary Errors

### `ValueError: adder.add_first must be called before adder.add`

Fix:

- Call `adder.add_first(timestep)` immediately after `environment.reset()`.
- After an episode ends and the adder resets, call `add_first` for the next episode before calling `add` again.
- For custom loops, keep the previous timestep/current action ordering clear: `action = policy(timestep.observation)`, `next_timestep = env.step(action)`, then `adder.add(action, next_timestep, extras)`.

### `adder.add_first` called with a non-first timestep

Fix:

- Use the timestep returned by `environment.reset()`.
- Check wrappers that may convert environment APIs; route wrapper/debugging issues to the core workflow guidance.

### Episode exceeds `EpisodeAdder.max_sequence_length`

Fix:

- Increase `max_sequence_length` to cover the maximum number of observations in an episode.
- Filter/truncate episodes before insertion if the learner can handle truncated data.
- Switch to `SequenceAdder` when full-episode replay is not required.

## Sequence Length and Period Pitfalls

| Problem | Explanation | Fix |
| --- | --- | --- |
| Too many near-duplicate samples | `period` is much smaller than `sequence_length`, creating heavy overlap | Increase `period`, or keep overlap only for recurrent burn-in needs. |
| Missing steps in replay | `period > sequence_length` creates gaps | Use `period <= sequence_length` unless intentionally downsampling. |
| Learner cannot handle final zero rows | `EndBehavior.ZERO_PAD` pads tails with zero-filled artificial steps | Use masks/start/end markers if learner supports them, or use `TRUNCATE` and pad in the dataset pipeline. |
| Learner gets variable time lengths | `TRUNCATE` writes shorter final items | Use `ZERO_PAD`, filter short items, or add dataset padding before batching. |
| Hidden state crosses episode unexpectedly | `EndBehavior.CONTINUE` does not reset writer at episode boundaries | Use `ZERO_PAD`, `TRUNCATE`, or `WRITE` unless the learner explicitly uses `start_of_episode` to reset recurrent state. |
| Structured sequence config rejects padding | `create_sequence_config` does not support `ZERO_PAD` | Use `TRUNCATE` with `StructuredAdder` and pad/mask in the learner pipeline. |

For recurrent learners with extras and overlap, use `SequenceAdder`, not `NStepTransitionAdder`; the transition adder stores only a single extras structure per transition and removes the time axis.

## Offline Demonstration Shape Problems

### Learner expects transitions but arrays are episode-shaped

Fix:

- Convert adjacent observations into transitions: `observation[:-1]`, `action[:-1]`, `reward[:-1]`, `discount[:-1]`, `next_observation=observation[1:]`.
- Drop the final observation unless constructing episode/sequence data.
- Set terminal transition discounts to `0.0` for terminal steps.

### Learner expects `reverb.ReplaySample` but offline data yields `types.Transition`

Fix:

- Wrap transition batches with `acme.utils.reverb_utils.transition_to_replaysample`.
- Confirm the learner uses `.data` fields and does not require meaningful Reverb sample priorities/probabilities from `.info`.

### Sequence replay converted to transitions has invalid final `next_observation`

Cause: `replay_sample_to_sars_transition(..., is_sequence=True)` forms `next_observation` by rolling observations along the sequence axis.

Fix:

- Pass `strip_last_transition=True` to remove the invalid final transition.
- Pass `flatten_batch=True` if the learner expects a flat transition batch rather than `[batch, time, ...]`.

### JAX random sample iterator runs out of memory

Cause: `JaxInMemoryRandomSampleIterator` loads the entire dataset into memory.

Fixes:

- Reduce `num_episodes`, sample size, or observation resolution.
- Use a streaming `tf.data` pipeline when the learner accepts it.
- Use algorithm-specific offline loaders if they support disk-backed sampling.

### JAX sharding assertions fail

Likely causes:

- `batch_size` is not divisible by the number of devices.
- Dataset size is not evenly divisible by devices; Acme drops final elements to make shards even.

Fixes:

- Choose a batch size divisible by the device count.
- Disable `shard_dataset_across_devices` for small debugging runs.

## Invalid Dataset Paths or Names

### Local offline files

Fix checklist:

- Verify that the file/directory exists from the process working directory.
- Normalize paths before passing them into data-loading code.
- Check shard naming conventions if adapting Atari/RL Unplugged-style datasets.
- For custom arrays, load once and print leaf shapes before building a dataset.

### TFDS dataset names

Fix checklist:

- Use a full TFDS dataset name such as `d4rl_mujoco_halfcheetah/v2-medium` when required.
- Ensure TFDS data is downloaded or the runtime is allowed to download it.
- Pass `num_episodes` for small smoke tests before loading full datasets.
- Check that the dataset uses RLDS fields (`observation`, `action`, `reward`, `is_terminal`) expected by Acme's helper.

## Reverb Dataset Construction Problems

### `ValueError: No positive weights in input tables`

Cause: `make_reverb_dataset(table={...})` filters out weights `<= 0` and found none.

Fix:

- Pass a table string for one table, or make at least one mapping value positive.
- Check online/offline mix ratios after config interpolation.

### Dataset blocks forever or produces no samples

Likely causes:

- Reverb rate limiter requires more inserts before sampling.
- Actor is not writing to the table name the learner samples.
- `NStepTransitionAdder` or `EpisodeAdder` has not reached a write condition yet.
- Reverb server address points at the wrong process.

Fixes:

- Use a permissive `MinSize(1)` rate limiter for smoke tests.
- Confirm `priority_fns` table names match sampled table names.
- For `EpisodeAdder`, complete an episode before expecting samples.
- For `SequenceAdder`, step at least `sequence_length` actor steps unless final behavior writes shorter items.

### Deprecated kwargs passed to `make_reverb_dataset`

Symptoms: `ValueError` when `environment_spec` or `extra_spec` is set.

Fix:

- Put specs on the `reverb.Table(signature=...)` instead.
- Call `make_reverb_dataset(server_address, batch_size=..., table=...)` without deprecated signature kwargs.

## Image Augmentation Problems

| Symptom | Cause | Fix |
| --- | --- | --- |
| Rank/shape error in `pad_and_crop` | Image leaf is not shaped `[..., H, W, C]` | Move channels to the last dimension or write a custom observation transform. |
| `BILINEAR` crop fails on unbatched image | The implementation uses `tf.shape(padded_img)[0]` as batch size | Prefer `ALIGNED` for unbatched images or add a batch dimension before bilinear augmentation. |
| Next observations not augmented | `transform_next_observation=False` | Set `transform_next_observation=True` for transition learners that compare current and next observations. |
| Non-image observations transformed accidentally | Transform applied to the whole observation tree | Write a tree-aware transform that only applies `pad_and_crop` to pixel leaves. |

## Quick Diagnostic Flow

1. Classify the data item: transition, fixed sequence, full episode, or custom structured pattern.
2. Confirm the writer family, table signature, and learner iterator all expect the same item type.
3. Check optional dependencies for the selected path: Reverb/TensorFlow for online replay, TFDS/RLDS/JAX for Acme TFDS random sampling.
4. Inspect one unbatched element and one batched element for nested keys, shapes, dtypes, and leading dimensions.
5. For sequence data, decide what happens to final partial sequences before training: pad, truncate, drop, or mask.
6. Use `scripts/describe_replay_structure.py` for a dependency-free sanity check of data nesting and adder-family choice.
