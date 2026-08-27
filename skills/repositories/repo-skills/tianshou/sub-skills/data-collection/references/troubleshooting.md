# Data Collection Troubleshooting

## Install or Import Fails

Symptoms:

- `ModuleNotFoundError: No module named 'tianshou'`
- `ImportError` for `torch`, `gymnasium`, `h5py`, `numba`, or `sensai`
- Version mismatch between package metadata and expected behavior

Fixes:

- Verify `python -c "import tianshou; print(tianshou.__version__)"` prints `2.0.1` for this generated skill.
- Run the bundled smoke with `--skip-collector` first to isolate core `tianshou.data` imports from Gymnasium collection behavior.
- Optional backends such as Atari, Box2D, MuJoCo, VizDoom, EnvPool, robotics, Ray, and broad dev extras are not required for this sub-skill.
- If HDF5 save/load fails, confirm `h5py` is installed; normal in-memory data collection does not require writing HDF5 files.

## Batch Slice or Merge Error

Symptoms:

- `Batch.cat_ only supports concatenation of batches with the same structure`
- `Stack of Batch with non-shared keys ... is only supported with axis=0`
- `Entry for ... has no len()`
- `Batch does not support heterogeneous list/tuple of tensors as unique value yet`
- Unexpected `dtype=object` arrays after stacking

Fixes:

- Compare nested key structures before `Batch.cat` and make missing keys explicit with defaults.
- Ensure every batched field has a leading dimension; wrap single transitions with `Batch.stack([transition])` when needed.
- Use `axis=0` for `Batch.stack` when some keys are present in only some batches.
- Convert homogeneous Python lists to NumPy arrays or Torch tensors before constructing the `Batch`.
- For ragged values, use intentional object arrays and do not call `to_torch()` on those fields.
- Avoid scalar-only fields in batches used for `len`, splitting, replay insertion, or policy forward paths.

## Nested Object Arrays Behave Strangely

Symptoms:

- Slicing a nested observation produces arrays of dictionaries or arrays of arrays.
- `to_torch()` fails on object arrays.
- Policy code expects `batch.obs.key`, but receives an object array.

Fixes:

- Prefer nested dictionaries at construction time: `Batch(obs={"camera": array, "state": array})`.
- If each element is a dictionary, build with `Batch(list_of_dicts)` to stack into nested `Batch` fields.
- Keep ragged Python objects in an `info` field rather than in `obs` fields used by networks.
- Convert dict observations to arrays/tensors at the model preprocessing boundary, not inside the replay buffer.

## ReplayBuffer Add Fails

Symptoms:

- `Input batch must have the following keys: {'obs', 'act', 'rew', 'terminated', 'truncated', 'done'}`
- `If buffer_ids is not None, the batch must have the shape (1, len(data))`
- `key 'obs' is reserved and cannot be assigned`
- Empty samples or wrong episode statistics

Fixes:

- Provide `obs`, `act`, `rew`, `terminated`, `truncated`, `obs_next`, and `info` in the transition batch; the buffer computes `done` internally.
- For a non-vector `ReplayBuffer`, omit `buffer_ids` or pass only `[0]` with a one-row stacked batch.
- For multiple envs, use `VectorReplayBuffer` and pass one transition per ready environment.
- Do not assign reserved keys as direct attributes on a `ReplayBuffer`; add data through `buffer.add`.
- Use `sample(batch_size=0)` to inspect all available transitions and confirm insertion order.

## Buffer Sampling or Shape Is Wrong

Symptoms:

- `buffer[:]` differs from a raw slice expectation.
- `sample(batch_size=0)` returns no data.
- Frame stacking returns unexpected dimensions.
- `get_buffer_indices` raises that start and stop are in different sub-buffers.

Fixes:

- Remember `buffer[:]` returns available transitions; circular storage may not match raw internal order.
- Check `len(buffer)` before sampling; a size-zero buffer or negative sample size returns empty data.
- With `stack_num > 1`, consider `sample_avail=True` to avoid incomplete stacked samples.
- Use `get_buffer_indices` only within one sub-buffer; vector buffer episode slices cannot cross env sub-buffer edges.
- If an episode is as long as or longer than a sub-buffer, increase buffer size or reduce vectorization.

## NaNs or Nulls in Buffer

Symptoms:

- `MalformedBufferError: NaN detected in the buffer`
- `buffer.hasnull()` is true after collection.
- New hook-created fields are partially missing.

Fixes:

- Inspect missing counts with `buffer.isnull().apply_values_transform(np.sum)`.
- When an episode hook returns fields, collect with `n_episode`, not `n_step`.
- Ensure hook-returned arrays have exactly `len(episode_batch)` entries.
- In step hooks, write one value per ready environment.
- Use `raise_on_nan_in_buffer=True` in small smokes, then disable only if validation cost is a measured bottleneck.
- Use `buffer.dropnull()` only after fixing the hook or assignment logic that created nulls.

## Collector Does Not Start

Symptoms:

- `Initial obs and info should not be None`
- `Exactly one of n_step or n_episode should be set`
- `Only one of n_step and n_episode should be set to a value larger than zero`
- Warning that `n_step` is not a multiple of `env_num`

Fixes:

- Call `collector.reset()` before collection or pass `reset_before_collect=True`.
- Pass exactly one positive target: `n_step=...` or `n_episode=...`.
- Make `n_step` a multiple of `len(collector.env)` for predictable step counts.
- Use `n_episode` for evaluation and episode-level stats.
- Keep Gymnasium `reset` and `step` return signatures current: `(obs, info)` and `(obs, reward, terminated, truncated, info)`.

## Collector and Buffer Mismatch

Symptoms:

- `Cannot use ReplayBuffer to collect from multiple envs`
- `Buffer has only ... buffers, but at least env_num are needed`
- Async env error asking to use `AsyncCollector`

Fixes:

- Single env: `ReplayBuffer(size)` is fine.
- Vector env: use `VectorReplayBuffer(total_size, buffer_num=env_num)` or a compatible vectorized prioritized/HER buffer.
- Cached buffer: `cached_buffer_num` must be at least `env_num`.
- Async vector env: use `AsyncCollector`; non-async vector env: use `Collector`.
- For worker/process choices and vector env construction details, route to `../envs-and-vectorization/SKILL.md`.

## Policy Output Misuse During Collection

Symptoms:

- Runtime error that policy result should be a `Batch`.
- Missing `act` in policy output.
- Hidden state shape or reset problems.
- Continuous actions out of bounds.

Fixes:

- Policy `forward` must return a `Batch` containing at least `act`; optional fields include `state`, `policy`, and `dist`.
- The collector stores `policy` entries under the replay buffer's `policy` field.
- `map_action` converts raw actions to env actions; do not pre-scale twice.
- For recurrent state, return a state whose leading dimension matches ready env count; collector resets done-env hidden state by type.
- Use `random=True` to separate environment/buffer issues from policy forward issues.

## Episode Hook Failure

Symptoms:

- Error that hook additions are not supported for `n_step` collection.
- Hook field length mismatch.
- Statistics omit expected episode returns.

Fixes:

- Collect full episodes with `collector.collect(n_episode=M, ...)` when a hook returns fields.
- Return a dictionary where each value has first dimension `len(episode_batch)`.
- Do not return scalar hook values for per-transition fields; broadcast them explicitly.
- If no full episode completes during `n_step`, `stats.returns` and `stats.lens` can be empty by design.

## MalformedBufferError During Return Computation

Symptoms:

- Return targets are incorrect near episode boundaries.
- `get_buffer_indices` raises on sub-buffer crossing.
- Buffer reports a starting index outside available samples.

Fixes:

- Avoid manual edits to private buffer pointers or `_meta`.
- Keep episodes shorter than their sub-buffer capacity.
- Use `buffer.add` for every transition so `last_index`, episode return, and episode start metadata remain consistent.
- Sample through `buffer.sample` and pass the returned `indices` to n-step/GAE preprocessing.
- For vector env data, confirm each environment writes only to its corresponding sub-buffer.

## Data or Config Validation Checklist

Before blaming the algorithm:

1. Run the bundled smoke script.
2. Print `len(batch)`, `batch.get_keys()`, and nested observation keys.
3. Check `len(buffer)`, `buffer.maxsize`, `buffer.hasnull()`, and `buffer.sample(0)[0]`.
4. Confirm collector `env_num`, buffer type, and buffer sub-buffer count agree.
5. Confirm only one collection target is set and first collection resets the env.
6. Confirm optional dependencies are truly needed for the selected env/backend.
