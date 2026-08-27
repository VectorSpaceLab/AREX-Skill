# Data and Replay Buffers

This sub-skill covers the data-side contract that Diffusion Policy uses everywhere: dataset adapters, ReplayBuffer storage, SequenceSampler windows, normalization, and the safe routes from raw recordings into replay-buffer-backed datasets.

## Core mental model

A ReplayBuffer is a time-major store. Every array in `data/` is concatenated across all steps, and `meta/episode_ends` stores the cumulative end index of each episode.

```
data/<key>      -> (T, ...)
meta/episode_ends -> (n_episodes,)
```

The last episode end must equal the total number of steps. Every `data/*` array must share that same first dimension.

## Dataset interface contract

### Low-dimensional datasets
Concrete classes inherit from `BaseLowdimDataset` and return samples shaped like:

```python
{
  "obs": Tensor[To, Do],
  "action": Tensor[Ta, Da],
}
```

### Image datasets
Concrete classes inherit from `BaseImageDataset` and return samples shaped like:

```python
{
  "obs": {
    "key0": Tensor[To, ...],
    "key1": Tensor[To, ...],
  },
  "action": Tensor[Ta, Da],
}
```

The dataset's `get_normalizer()` method must return a `LinearNormalizer` whose keys match the returned sample keys exactly.

## ReplayBuffer contract

### Storage forms
- in-memory numpy backend for lightweight inspection and tests
- on-disk zarr directory store
- on-disk zipped zarr store

### Required invariants
- `data` and `meta` groups exist
- `meta/episode_ends` exists and is monotonically increasing
- every data array has the same first dimension as `episode_ends[-1]`
- `add_episode()` requires all arrays in one episode to share the same length

### Useful operations
- create empty stores with `create_empty_numpy()` or `create_empty_zarr()`
- open an existing store with `create_from_path()`
- load or copy a subset with `copy_from_path()` / `copy_from_store()`
- add, drop, pop, and slice episodes with `add_episode()`, `drop_episode()`, `pop_episode()`, `get_episode()`, and `get_steps_slice()`
- inspect or change chunking with `get_chunks()`, `set_chunks()`, `get_compressors()`, and `set_compressors()`

### Boundary rules
`SequenceSampler` repeats the first or last available value when a sampled window crosses episode boundaries. That is expected padding behavior, not corruption.

## SequenceSampler contract

`SequenceSampler(replay_buffer, sequence_length, pad_before=0, pad_after=0, keys=None, key_first_k={}, episode_mask=None)` builds fixed-length windows from a ReplayBuffer.

### Parameter meanings
- `sequence_length`: total sampled horizon
- `pad_before` / `pad_after`: allow windows to start before or end after the in-episode range; values are clipped to the range `[0, sequence_length - 1]`
- `keys`: subset of replay-buffer keys to load
- `key_first_k`: only load the first `k` timesteps for selected keys; the remaining region is filled before final padding
- `episode_mask`: boolean mask over episodes; `True` episodes contribute samples

### Output shape
`sample_sequence(idx)` returns a dictionary whose arrays all have length `sequence_length` along axis 0.

### Helper utilities
- `get_val_mask(n_episodes, val_ratio, seed=0)` keeps train/validation splits stable and ensures at least one episode in each split when possible
- `downsample_mask(mask, max_n, seed=0)` subsamples a mask for smaller training sets
- `create_indices(...)` is the internal index builder and is useful for debugging padding math

## Normalization contract

### Main APIs
- `LinearNormalizer.fit(data, last_n_dims=1, mode='limits'|'gaussian', output_max=1, output_min=-1, range_eps=1e-4, fit_offset=True)`
- `SingleFieldLinearNormalizer.create_fit(data, ...)`
- `SingleFieldLinearNormalizer.create_manual(scale, offset, input_stats_dict)`
- `SingleFieldLinearNormalizer.create_identity()`

### Helper functions in `normalize_util`
- `array_to_stats(arr)`
- `get_range_normalizer_from_stat(stat)`
- `get_image_range_normalizer()`
- `get_identity_normalizer_from_stat(stat)`
- `robomimic_abs_action_normalizer_from_stat(stat, rotation_transformer)`
- `robomimic_abs_action_only_normalizer_from_stat(stat)`
- `robomimic_abs_action_only_dual_arm_normalizer_from_stat(stat)`

### When to use which helper
- low-dim positions and bounded state vectors -> `get_range_normalizer_from_stat()`
- images already in `[0, 1]` -> `get_image_range_normalizer()`
- already-normalized quaternions or bounded values -> `get_identity_normalizer_from_stat()`
- Robomimic absolute-action conversion -> the `robomimic_abs_action_*` helpers with `RotationTransformer`

## Dataset family map

| Family | Loader / class | Input assumptions | Returned sample | Notes |
|---|---|---|---|---|
| Push-T low-dim | `diffusion_policy.dataset.pusht_dataset.PushTLowdimDataset` | zarr store with `keypoint`, `state`, `action` | flat `obs` tensor plus `action` tensor | flattens keypoint and appends agent position |
| Push-T image | `diffusion_policy.dataset.pusht_image_dataset.PushTImageDataset` | zarr store with `img`, `state`, `action` | `obs.image` and `obs.agent_pos` | images are channel-first float32 in `[0, 1]` |
| Block pushing | `diffusion_policy.dataset.blockpush_lowdim_dataset.BlockPushLowdimDataset` | zarr store with `obs`, `action` | flat low-dim tensors | optional target masking and manual normalization |
| Kitchen | `diffusion_policy.dataset.kitchen_lowdim_dataset.KitchenLowdimDataset` and `KitchenMjlLowdimDataset` | `.npy` sequences or `.mjl` logs | low-dim tensors | builds episodes from sequence masks or MJL logs |
| Mujoco image | `diffusion_policy.dataset.mujoco_image_dataset.MujocoImageDataset` | zarr store with robot camera and pose/action keys | image dict plus low-dim state/action | uses `shape_meta`-style key selection |
| Robomimic replay | `diffusion_policy.dataset.robomimic_replay_lowdim_dataset.RobomimicReplayLowdimDataset` and `RobomimicReplayImageDataset` | HDF5 `data/demo_*` episodes | low-dim tensor or image dict | supports `abs_action`, `rotation_rep`, `use_cache`, `n_obs_steps`, and train/val splitting |
| Real Push-T recorded data | `diffusion_policy.dataset.real_pusht_image_dataset.RealPushTImageDataset` | recorded directory with replay-buffer data and videos | image dict plus low-dim actions | this is for already-recorded data; live capture belongs elsewhere |

## `shape_meta` convention for image-style datasets

When a dataset uses image keys, `shape_meta` typically looks like:

```python
{
  "obs": {
    "camera0": {"shape": [3, 224, 224], "type": "rgb"},
    "agent_pos": {"shape": [8], "type": "low_dim"},
  },
  "action": {"shape": [8]}
}
```

Rules:
- image keys are tagged with `type: "rgb"`
- non-image inputs are tagged with `type: "low_dim"`
- `n_obs_steps` limits how many observation steps are returned and, in some loaders, how many steps are loaded from disk
- `n_latency_steps` shortens returned actions after sampling when latency compensation is needed

## Conversion route map

The original package exposes a few dataset-oriented conversion helpers whose CLI shapes are worth remembering when you validate a store or adapt a converter.

| Helper family | Option names | What it does |
|---|---|---|
| Robomimic HDF5 action conversion | `--input/-i`, `--output/-o`, optional `--eval_dir/-e`, optional `--num_workers/-n` | rewrites Robomimic action conventions and can emit error statistics for inspection |
| Robomimic action comparison | `--input/-i`, `--output/-o` | compares paired HDF5 action conventions and reports position/rotation deltas |
| Recorded real-data compaction | `--input/-i`, `--output/-o`, `--resolution/-r`, `--n_decoding_threads/-nd`, `--n_encoding_threads/-ne` | converts recorded directories into replay-buffer zarr or zip output |
| Episode-length reporting | `--input/-i`, `--dt` | turns replay-buffer episode lengths into durations and summary stats |

Treat these helpers as data-layout routes, not as training or policy commands. The safe follow-up step after any conversion is to inspect the resulting store with the bundled inspector and confirm episode counts, step counts, and array shapes.

## Recommended validation order

1. Inspect the store with `scripts/inspect_replay_buffer.py`.
2. Confirm `episode_ends[-1]` matches every `data/*` leading dimension.
3. Verify the dataset class returns the right sample type: flat low-dim tensor or image dict.
4. Check that `get_normalizer()` returns keys that exactly match the sample keys.
5. Run the small native replay-buffer and shared-queue tests when the environment supports them.
