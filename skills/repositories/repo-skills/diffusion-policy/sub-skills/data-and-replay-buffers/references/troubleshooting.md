# Troubleshooting

Use these checks when a dataset, replay buffer, sampler, or normalizer behaves unexpectedly.

## 1) Zarr or zip ReplayBuffer episode length mismatch

### Symptoms
- `ReplayBuffer.__init__` or `create_from_path()` fails on a store that otherwise opens
- `episode_ends[-1]` does not match the leading dimension of one or more `data/*` arrays
- episode lengths are negative, zero when they should not be, or not strictly increasing
- `SequenceSampler` returns windows with the wrong effective episode span

### Likely causes
- conversion was interrupted before metadata and arrays were finalized
- the archive was copied or recompressed incorrectly
- one episode was appended with arrays of different lengths
- the store points at the wrong replay-buffer root

### Safe checks
1. Run `python scripts/inspect_replay_buffer.py --path <store> --json`.
2. Compare `episode_ends[-1]` against every reported `data/*` shape.
3. Confirm `episode_ends` is strictly increasing and one-dimensional.

### Safe fix
- regenerate the replay buffer from the original source data
- do not edit `episode_ends` in place unless you are deliberately repairing a known-good store
- if the store is a zip archive, treat it as read-only and write a fresh output archive instead

## 2) Low-dim versus image sample schema confusion

### Symptoms
- a dataset returns a flat tensor when the downstream code expects `obs` to be a dict
- a dataset returns a dict of observation keys when the downstream code expects a flat `obs` tensor
- image values show up with the wrong channel order or without normalization
- `KeyError` appears when looking up image keys or low-dim keys

### Likely causes
- the wrong dataset base class was chosen
- `shape_meta['obs'][key]['type']` does not match the stored data type
- image tensors were not converted from channel-last storage to channel-first tensors
- `n_obs_steps` or `key_first_k` is trimming more data than the consumer expects

### Safe checks
- flat low-dim sample: `{'obs': Tensor[To, Do], 'action': Tensor[Ta, Da]}`
- image sample: `{'obs': {"camera": Tensor[To, ...], ...}, 'action': Tensor[Ta, Da]}`
- inspect a single batch from the dataset and compare it to the expected shape contract before routing elsewhere

### Safe fix
- use the low-dim dataset family for flat observation tensors
- use the image dataset family when `obs` is a dict of key-specific tensors
- make sure image keys are normalized with the image helper and not with the low-dim helper

## 3) Normalizer or action key errors

### Symptoms
- `KeyError: 'action'`
- `KeyError` on one of the observation keys
- `RuntimeError('unsupported')` from a dataset normalizer
- normalized values look wildly out of range

### Likely causes
- the sample keys returned by `__getitem__` do not match the keys used in `get_normalizer()`
- the dataset stores already-normalized values but the normalizer tries to re-fit limits
- a Robomimic loader encountered an unexpected low-dim key suffix
- the action dimension does not match the expected abs-action conversion path

### Safe checks
- print the sample keys and the normalizer keys together
- confirm whether the action should be treated as relative, absolute, or absolute-plus-rotation-converted
- for Robomimic image data, only the supported low-dim key suffixes are handled by the built-in helper path

### Safe fix
- align the sample keys with the normalizer keys exactly
- use `get_identity_normalizer_from_stat()` when a field is already bounded or pre-scaled
- use `get_range_normalizer_from_stat()` for bounded state channels and `get_image_range_normalizer()` for image channels

## 4) Missing zarr, numcodecs, imagecodecs, h5py, or robomimic dependencies

### Symptoms
- import errors when opening replay buffers or conversion routes
- zarr stores cannot be inspected
- HDF5 conversion routes fail before any data is written
- image compression or decoding fails during conversion

### Likely causes
- the runtime environment only has the minimal Python stack
- a dataset conversion route needs a dependency that the inspection-only path does not need

### Safe checks
- if the task is only inspection, try importing the read-only inspector path first
- if the task is HDF5-based, confirm `h5py` is present
- if the task is image compression or decompression heavy, confirm image codec support is installed
- if the task uses Robomimic conversion, confirm the Robomimic stack is available

### Safe fix
- install only the dependency group required by the workflow you are using
- do not expand to the full benchmark stack unless you are actually reproducing benchmark training

## 5) Dataset path or download not present

### Symptoms
- `FileNotFoundError`
- `assert path.is_dir()` or `assert path.is_file()` failures
- conversion routes cannot find the expected data layout
- an inspector runs, but the store is empty or clearly not the intended dataset

### Likely causes
- the path points to the parent directory rather than the actual replay buffer or raw dataset root
- the dataset download or extraction step has not happened yet
- the conversion output path is wrong or points to the input directory

### Safe checks
- confirm whether the task expects a replay buffer store, a raw recorded-data directory, or a source HDF5 file
- confirm the parent directory exists for any output path
- compare the expected keys from the data-layout notes against what the inspector reports

### Safe fix
- point the tool at the exact replay-buffer store or raw dataset root
- create the missing parent directory before writing a converted output
- if the dataset has not been downloaded yet, stop and request the dataset rather than guessing the path

## 6) Empty dataset after splitting

### Symptoms
- the sampler length becomes zero
- validation or training iterations silently produce no batches

### Likely causes
- a custom mask excluded every episode
- `val_ratio` or `max_train_episodes` was set in a way that leaves no eligible episodes

### Safe checks
- inspect the train and validation episode counts separately
- confirm the mask length matches the episode count

### Safe fix
- use `get_val_mask()` or another balanced split helper
- avoid custom masks that remove every episode from the selected split
