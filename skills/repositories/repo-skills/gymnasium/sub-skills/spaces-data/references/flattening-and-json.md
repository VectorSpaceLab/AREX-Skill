# Flattening and JSON Reference

Use Gymnasium's space utilities when a policy, replay buffer, model, logger, or API needs a data representation different from the structured space sample. Always keep the original `space` object next to the transformed data; `unflatten(space, x)` is only meaningful for the same space used to flatten.

## Utility Functions

Import from `gymnasium.spaces.utils`:

```python
from gymnasium.spaces import utils as space_utils

flat_length = space_utils.flatdim(space)
flat_space = space_utils.flatten_space(space)
flat_sample = space_utils.flatten(space, sample)
restored = space_utils.unflatten(space, flat_sample)
```

| Function | Purpose | Important caveat |
| --- | --- | --- |
| `flatdim(space)` | Return the static flat vector length for a numpy-flattenable space. | Raises `ValueError` for `Graph`, `Sequence`, and composites containing them. |
| `flatten_space(space)` | Return a flattened space, usually a flat `Box`. | For `Graph`, returns a `Graph` with flattened node/edge spaces. For `Sequence`, returns a `Sequence` of flattened feature space. |
| `flatten(space, x)` | Convert a sample into its flattened representation. | For non-numpy-flattenable spaces, output can remain structured (`tuple`, `dict`, `GraphInstance`). |
| `unflatten(space, x)` | Reverse `flatten` for the same space. | Not every point sampled from `flatten_space(space)` is reversible, especially one-hot categorical encodings. |

## Flat Representation by Space

| Space | `flatdim` | `flatten` output | `flatten_space` output |
| --- | --- | --- | --- |
| `Box(shape=s)` | product of `s` | 1-D array cast to `space.dtype`. | `Box` with flattened low/high and same dtype. |
| `MultiBinary(shape=s)` | product of `s` | 1-D `int8` array. | `Box(0, 1, shape=(flatdim,), dtype=int8)`. |
| `Discrete(n, start=...)` | `n` | one-hot vector with index `x - start`. | `Box(0, 1, shape=(n,), dtype=space.dtype)`. |
| `MultiDiscrete(nvec, start=...)` | `sum(nvec)` | concatenated one-hot vectors, each offset by `start`. | `Box(0, 1, shape=(sum(nvec),), dtype=space.dtype)`. |
| `Text(max_length=...)` | `max_length` | integer character indices padded with `len(character_set)`. | `Box(0, len(character_set), shape=(max_length,), dtype=int32)`. |
| `Tuple` | sum of subspace flatdims when all are numpy-flattenable. | concatenated flat array, otherwise tuple of flattened parts. | flat `Box` when possible; otherwise `Tuple` of flattened subspaces. |
| `Dict` | sum of values' flatdims when all are numpy-flattenable. | concatenated flat array in `space.spaces` order, otherwise dict of flattened values. | flat `Box` when possible; otherwise `Dict` of flattened subspaces. |
| `Graph` | unavailable for full graph. | `GraphInstance` with flattened node/edge features and original links. | `Graph(flattened_node_space, flattened_edge_space_or_None)`. |
| `Sequence` | unavailable because length is dynamic. | tuple of flattened feature samples, or stacked array-like output when `stack=True`. | `Sequence(flatten_space(feature_space), stack=space.stack)`. |
| `OneOf` | `1 + max(flatdim(subspace))`. | `[index, flat_sample...]` padded to max subspace length. | `Box` covering the index and widest subspace value range. |

## Decision Rules for Model Inputs

1. If a space is `Box`, flattening is a reshape/cast; keep bounds and dtype for normalization.
2. If a space is `Discrete` or `MultiDiscrete`, flattening creates one-hot encodings. Do not feed raw integer categories to code that expects Gymnasium's flattened representation.
3. If a `Dict` or `Tuple` is fully numpy-flattenable, `flatten` returns one concatenated array. Record `flatdim(space)` and use `unflatten` to recover structure.
4. If a space contains `Sequence` or `Graph`, `flatdim` cannot produce a fixed model vector. Use a model that supports variable length/graphs, or write a wrapper/adapter that pads, truncates, pools, or featurizes data and updates the public space.
5. If a space is `OneOf`, the first flattened value is the selected subspace index. Downstream code must understand the padded payload convention.
6. Never sample directly from `flatten_space(Discrete(...))` or `flatten_space(MultiDiscrete(...))` and assume it can be unflattened. A random `Box` sample may not be a valid one-hot vector.

## Nested Dict/Tuple Round Trip Pattern

```python
import numpy as np
from gymnasium import spaces
from gymnasium.spaces import utils as space_utils

space = spaces.Dict({
    "agent": spaces.Tuple((
        spaces.Box(-1, 1, shape=(2,), dtype=np.float32),
        spaces.Discrete(3, start=1),
    )),
    "flags": spaces.MultiBinary(4),
})

sample = space.sample()
flat = space_utils.flatten(space, sample)
assert flat.shape == (space_utils.flatdim(space),)
assert flat in space_utils.flatten_space(space)

restored = space_utils.unflatten(space, flat)
assert space.contains(restored)
assert restored["agent"][0].dtype == np.float32
```

The exact equality check for restored values can be dtype-sensitive. Prefer `space.contains(restored)` plus application-specific numeric comparisons when arrays are involved.

## JSONable Batch Conversion

`to_jsonable` and `from_jsonable` operate on batches, not single samples:

```python
samples = [space.sample() for _ in range(3)]
payload = space.to_jsonable(samples)
round_tripped = space.from_jsonable(payload)
assert all(space.contains(item) for item in round_tripped)
```

| Space | JSONable shape | Round-trip notes |
| --- | --- | --- |
| `Box` | list of sample lists. | Restores arrays with `space.dtype`. |
| `Discrete` | list of ints. | Restores numpy scalar dtype. |
| `MultiBinary` / `MultiDiscrete` | list of nested lists. | Restores numpy arrays with declared dtype. |
| `Text` | list of strings. | Identity conversion. |
| `Dict` | dict of key to each subspace's JSONable batch. | Input batch must contain all keys expected by the space. |
| `Tuple` | list indexed by tuple position, where each value is that subspace's JSONable batch. | Restores list of tuples by zipping subspace batches. |
| `Sequence` | list of feature-space JSONable batches, or stacked feature JSONable output. | Dynamic lengths mean nested batch shape can vary. |
| `Graph` | list of dicts containing `nodes`, optionally `edges` and `edge_links`. | Restores `GraphInstance`; `edge_links` dtype is `int32`. |
| `OneOf` | list of `[space_index, subspace_jsonable_sample]`. | Restores `(np.int64(index), sub_sample)` tuples. |

Use JSONable conversion for logging, IPC, checkpoints, or network payloads. Use flattening for numerical model inputs. They are different transformations and should not be substituted for each other without an adapter.

## Common Shape Accounting Errors

- `Discrete(n, start=k)` contributes `n` flat dimensions, not `start + n`.
- `MultiDiscrete([2, 3])` contributes `5` flat dimensions, not `2` or `6`.
- `Box(low=0, high=1)` has shape `(1,)`; `Box(low=0, high=1, shape=())` has scalar shape `()`.
- A plain `Dict({"b": ..., "a": ...})` with comparable keys is ordered by sorted keys internally, so concatenated flatten order can differ from source literal order. Use a sequence of pairs or explicit ordering if flatten order matters.
- `Text(max_length=6)` always flattens to length `6`, even if a sample string is shorter.
- `Sequence` with `stack=False` contains tuples; with `stack=True`, samples may be stacked arrays. Choose based on downstream batch handling.

## When to Use Wrappers

If an environment emits a valid structured observation but a model expects a flat vector, the public env can be wrapped rather than changing the raw env. Use `../wrappers-recording/SKILL.md` for `FlattenObservation` and custom observation wrappers. If wrapper output changes the public observation, the wrapper must expose the transformed `observation_space`.

For vectorized environments, use `../vectorization/SKILL.md`; vector utilities have additional batched-space conventions beyond these single-sample functions.
