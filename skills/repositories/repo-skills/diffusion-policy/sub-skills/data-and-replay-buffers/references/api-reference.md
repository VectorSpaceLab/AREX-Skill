# API Reference

This reference is a compact contract sheet for the data-side APIs used by Diffusion Policy.

## ReplayBuffer

**Signature**

```python
ReplayBuffer(root: Union[zarr.hierarchy.Group, Dict[str, dict]])
```

### Required layout
- `root['data']` contains one array per field
- `root['meta']['episode_ends']` stores cumulative episode ends
- every `data/*` array must have the same first dimension as `episode_ends[-1]`

### Constructors and loaders
| API | Purpose | Notes |
|---|---|---|
| `create_empty_numpy()` | Create an in-memory numpy-backed buffer | useful for tests and small synthetic datasets |
| `create_empty_zarr(storage=None, root=None)` | Create an empty zarr-backed buffer | stores `data/` and `meta/` groups |
| `create_from_group(group, **kwargs)` | Wrap an existing zarr group | creates a new layout if `data/` is missing |
| `create_from_path(zarr_path, mode='r', **kwargs)` | Open a zarr directory or store path | read-only by default |
| `copy_from_store(src_store, store=None, keys=None, chunks={}, compressors={}, if_exists='replace', **kwargs)` | Copy from one store into memory or another store | can select a subset of keys |
| `copy_from_path(zarr_path, backend=None, store=None, keys=None, chunks={}, compressors={}, if_exists='replace', **kwargs)` | Convenience copy from a path | recommended for materializing a smaller in-memory copy |

### Reading and slicing
| API | Returns | Notes |
|---|---|---|
| `keys()`, `values()`, `items()` | dict-like views | backed by `data/` |
| `__getitem__(key)` | array for a field | `buffer['action']` is valid |
| `n_steps` | total step count | equal to the last `episode_end` |
| `n_episodes` | episode count | length of `episode_ends` |
| `episode_lengths` | array of episode lengths | computed from cumulative ends |
| `get_episode(idx, copy=False)` | dict for one episode | negative indexing is supported through list semantics |
| `get_episode_slice(idx)` | `slice(start, stop)` | useful for debugging a specific episode |
| `get_steps_slice(start, stop, step=None, copy=False)` | dict for a step range | safe read-only slicing |
| `get_episode_idxs()` | step-to-episode index map | helpful for debugging alignment |

### Writing and store management
| API | Purpose | Notes |
|---|---|---|
| `add_episode(data, chunks={}, compressors={})` | Append one episode | every array in `data` must share the same length |
| `drop_episode()` | Remove the last episode | mutates the underlying store |
| `pop_episode()` | Return and remove the last episode | convenience wrapper |
| `extend(data)` | Alias for `add_episode()` | |
| `save_to_store(store, chunks={}, compressors={}, if_exists='replace', **kwargs)` | Write to a store | zarr-only when the backing store is zarr |
| `save_to_path(zarr_path, chunks={}, compressors={}, if_exists='replace', **kwargs)` | Save to a directory store | creates a zarr directory at the target path |
| `get_chunks()` / `set_chunks()` | Inspect or change chunking | zarr-only |
| `get_compressors()` / `set_compressors()` | Inspect or change compressors | zarr-only |

### Compressor helpers
- `resolve_compressor('default')` selects an lz4-based Blosc compressor
- `resolve_compressor('disk')` selects a zstd-based Blosc compressor
- `get_optimal_chunks(shape, dtype, target_chunk_bytes=2e6, max_chunk_length=None)` picks time-major chunks for common replay-buffer shapes

## SequenceSampler

**Signature**

```python
SequenceSampler(
    replay_buffer: ReplayBuffer,
    sequence_length: int,
    pad_before: int = 0,
    pad_after: int = 0,
    keys=None,
    key_first_k={},
    episode_mask: Optional[numpy.ndarray] = None,
)
```

### Parameter meanings
- `sequence_length`: final returned horizon
- `pad_before` / `pad_after`: allow windows to extend around episode boundaries
- `keys`: subset of replay-buffer keys to sample; defaults to all keys
- `key_first_k`: only load the first `k` steps for selected keys to reduce memory traffic
- `episode_mask`: boolean mask over episodes; `True` episodes contribute sample windows

### Semantics
- the internal index rows are `[buffer_start_idx, buffer_end_idx, sample_start_idx, sample_end_idx]`
- when the requested window crosses a boundary, the sampler repeats the first or last valid value to fill the missing region
- the returned arrays always have `sequence_length` steps along axis 0

### Helper utilities
- `create_indices(...)` builds the sampler index table
- `get_val_mask(...)` creates a train/validation split mask
- `downsample_mask(...)` subsamples a training mask to a maximum number of episodes

## Dataset base classes

### `BaseLowdimDataset`
- `get_normalizer(**kwargs) -> LinearNormalizer`
- `get_all_actions() -> torch.Tensor`
- `__getitem__(idx) -> {'obs': Tensor[To, Do], 'action': Tensor[Ta, Da]}`

### `BaseImageDataset`
- `get_normalizer(**kwargs) -> LinearNormalizer`
- `get_all_actions() -> torch.Tensor`
- `__getitem__(idx) -> {'obs': Dict[str, Tensor], 'action': Tensor[Ta, Da]}`

## Normalizer APIs

### `LinearNormalizer`
- `fit(data, last_n_dims=1, dtype=torch.float32, mode='limits', output_max=1., output_min=-1., range_eps=1e-4, fit_offset=True)`
- `normalize(x)` / `unnormalize(x)`
- `get_input_stats()` / `get_output_stats()`
- `__getitem__(key)` returns a `SingleFieldLinearNormalizer`
- `__setitem__(key, value)` stores the field normalizer under that key

### `SingleFieldLinearNormalizer`
- `create_fit(data, **kwargs)`
- `create_manual(scale, offset, input_stats_dict)`
- `create_identity(dtype=torch.float32)`
- `normalize(x)` / `unnormalize(x)`
- `get_input_stats()` / `get_output_stats()`

### `normalize_util` helpers
| Function | Use |
|---|---|
| `array_to_stats(arr)` | compute min, max, mean, and std for a numpy array |
| `get_range_normalizer_from_stat(stat)` | map low-dim values into `[-1, 1]` |
| `get_image_range_normalizer()` | map image pixels from `[0, 1]` into `[-1, 1]` |
| `get_identity_normalizer_from_stat(stat)` | preserve already-normalized values |
| `robomimic_abs_action_normalizer_from_stat(stat, rotation_transformer)` | convert and normalize absolute Robomimic actions |
| `robomimic_abs_action_only_normalizer_from_stat(stat)` | normalize absolute actions with pose-like and remainder channels |
| `robomimic_abs_action_only_dual_arm_normalizer_from_stat(stat)` | dual-arm variant for wider action vectors |

## Shape-meta convention for image datasets

A common image dataset config uses:

```python
shape_meta = {
  "obs": {
    "camera": {"shape": [3, 224, 224], "type": "rgb"},
    "state": {"shape": [8], "type": "low_dim"},
  },
  "action": {"shape": [8]},
}
```

Rules:
- `type: "rgb"` means the stored source is image-like and will be converted to channel-first float32 in `[0, 1]`
- `type: "low_dim"` means the value is treated as a normal tensor field
- `n_obs_steps` trims returned observations after sampling
- `n_latency_steps` trims the leading action steps for latency compensation when present

## Common usage pattern

```python
from diffusion_policy.common.replay_buffer import ReplayBuffer
from diffusion_policy.common.sampler import SequenceSampler
from diffusion_policy.model.common.normalizer import LinearNormalizer

buffer = ReplayBuffer.create_from_path("dataset.zarr")
sampler = SequenceSampler(buffer, sequence_length=16, pad_before=2, pad_after=2)
sample = sampler.sample_sequence(0)
normalizer = LinearNormalizer()
normalizer.fit({"obs": sample["obs"], "action": sample["action"]}, last_n_dims=1)
```

The exact key names must stay consistent across the ReplayBuffer, sampler, dataset return value, and normalizer.
