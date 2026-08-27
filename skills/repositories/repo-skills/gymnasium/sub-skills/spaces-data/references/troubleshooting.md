# Spaces Troubleshooting

Most Gymnasium space bugs are contract mismatches: a value looks plausible but differs in dtype, shape, bounds, keys, categorical offset, or dynamic structure. Diagnose by checking the space object first, then the value.

## Fast Diagnostic Snippet

```python
import numpy as np

print(space)
print("shape:", getattr(space, "shape", None), "dtype:", getattr(space, "dtype", None))
print("value type:", type(value))
if isinstance(value, np.ndarray):
    print("value shape:", value.shape, "dtype:", value.dtype)
print("contains:", space.contains(value))
```

For `Box`, also inspect `space.low`, `space.high`, `np.nanmin(value)`, `np.nanmax(value)`, and `np.isnan(value).any()` when numeric values are expected.

## `Box.contains` Fails for Plausible Observations

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| A Python list triggers a warning and fails or passes unexpectedly. | `Box.contains` casts non-arrays to `np.asarray(x, dtype=space.dtype)` before validation. | Convert explicitly with `np.asarray(value, dtype=space.dtype)` and verify shape/bounds. |
| Correct-looking array fails. | `value.shape != space.shape`; common scalar `( )` vs one-element `(1,)` confusion. | Match the declared shape exactly. Use `Box(..., shape=())` for scalars or `(1,)` for vectors. |
| Values are in range but fail. | `np.can_cast(value.dtype, space.dtype)` is false, often int64 to smaller int dtype or float64 to float32 under strict casting rules. | Emit arrays with the declared dtype, e.g. `value.astype(space.dtype, copy=False)`, only after confirming no precision/range loss. |
| Values are out of range by tiny float noise. | Numeric transform or simulator produced `low - eps` or `high + eps`. | Clip only if clipping is semantically valid; otherwise widen bounds or fix the producer. |
| `NaN` observation fails. | Comparisons with bounds are false for `NaN`; `Box` bounds also cannot contain `np.nan`. | Fix upstream invalid math or encode missing values explicitly within bounds. |
| Constructor raises on bounds. | `low > high`, array shapes differ, `np.nan` bound, unsupported dtype, or integer/unsigned bound outside dtype range. | Validate `low`, `high`, `shape`, and `dtype` before constructing. For unsigned/bool boxes, avoid unsupported infinities. |

Remember that scalar `low` and `high` without `shape` create `shape=(1,)`. This is a frequent reason for scalar observations such as `np.float32(0.5)` failing a one-element vector space.

## Discrete and MultiDiscrete Offsets

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Action `0` is rejected by `Discrete(3, start=1)`. | Valid values are `{1, 2, 3}`. | Use `space.start` when mapping model indices to actions. |
| One-hot flatten/unflatten returns a shifted integer. | `flatten(Discrete(n, start=k), x)` writes one at `x - k`. | Keep raw model class index separate from environment action value. |
| `MultiDiscrete([5, 2, 2])` accepts value `4` in first slot but rejects `5`. | `nvec` entries are counts, not maxima. | Valid range per slot is `[start[i], start[i] + nvec[i] - 1]`. |
| Multidimensional `MultiDiscrete` masks are rejected. | Mask tuple does not mirror `nvec` structure, or leaf dtype/length is wrong. | Build nested tuples matching axes; each leaf length equals the relevant count and dtype is `np.int8` or `np.float64`. |
| Wrappers assume `0` is a noop but action space has nonzero `start`. | Some wrappers and external libraries expect zero-based categories. | Prefer zero-based spaces unless a nonzero start is essential; document and adapt mapping carefully. |

## Dict and Tuple Structure Mismatches

- `Dict.contains(x)` requires `x` to be a `dict` with exactly the same keys as the space. Missing, extra, or differently typed keys fail.
- Plain comparable-key dicts may be sorted internally; flatten order follows `space.spaces.items()`, not necessarily the source literal you remember. Inspect `list(space.spaces.keys())`.
- `Tuple.contains(x)` accepts lists and arrays by converting to tuple, but length and each subspace still must match.
- `Dict.seed(dict)` requires the exact key set, including nested dict seed keys.
- `Tuple.seed([...])` length must equal the number of subspaces.
- `unflatten(Dict_or_Tuple, x)` splits by each subspace `flatdim`. If you changed a subspace but reused an old flat vector, recovery will be wrong or fail.

## Flattening and Unflattening Errors

| Error or surprise | Cause | Fix |
| --- | --- | --- |
| `flatdim(space)` raises for a composite. | The composite includes a `Sequence` or `Graph`, which has dynamic size. | Use structured flatten output, a padding/graph adapter, or a wrapper that produces a fixed `Box`. |
| `unflatten(Discrete, array)` raises about invalid one-hot vector. | The vector has no nonzero entry. | Pass a real Gymnasium flattened sample, not an arbitrary `Box` sample. |
| `unflatten(MultiDiscrete, array)` raises about concatenated one-hot vectors. | At least one categorical segment lacks a selected entry. | Validate each segment has a nonzero one-hot value. |
| `flatten_space(space).sample()` cannot be unflattened. | Flattened categorical spaces are `Box` spaces and can sample invalid one-hot values. | Sample original `space`, then `flatten(space, sample)`. |
| Flattened dtype is unexpected. | Composite flat `Box` uses `np.result_type` across subspace dtypes. | Cast deliberately at model boundary and keep original space for recovery. |
| `OneOf` flattened payload has repeated/padded values. | It pads shorter subspace flattened samples to the maximum subspace width. | Use the first element as the index and `unflatten(space, flat)` instead of hand-parsing. |

## Sequence, Graph, and OneOf Limits

- `Sequence` has dynamic length. With `stack=False`, samples are tuples; with `stack=True`, samples use vector utility batching for the feature space. Many feed-forward RL models need padding/truncation outside the raw space contract.
- `Graph` contains `GraphInstance(nodes, edges, edge_links)`. Nodes must match `node_space`; edges and `edge_links` are both present or both `None`. `edge_links` must be integer shape `(num_edges, 2)` and indices must be within node count.
- `Graph.sample(num_nodes=1)` may produce no edges. `Graph.sample(num_edges=...)` warns if `edge_space is None`.
- `OneOf` samples are `(index, sub_sample)`. `contains` requires `index` to be an `int` or `np.int64` in range and the sub-sample to belong to that selected subspace.
- Dynamic or variant spaces usually need custom model adapters, not blind flattening.

## JSONable Conversion Problems

- Pass a batch/list of samples to `to_jsonable`, even for one item: `space.to_jsonable([sample])`.
- Feed the returned batch payload to `from_jsonable`, not a single sample payload unless the specific space documents identity behavior.
- `Dict.to_jsonable` returns a dict of per-key batches. Keep keys intact.
- `Tuple.to_jsonable` returns a list ordered by tuple position, not a list of tuple-looking records.
- `Graph.from_jsonable` expects `edges` and `edge_links` together when edges exist.

## Wrapper or Env Emits Data Not Matching Space

If an observation/action transform changes shape, dtype, keys, values, or semantic bounds, the corresponding space must change at the same layer.

- For custom environments, update `self.observation_space` / `self.action_space` and validate the env with the checker; route to `../environment-api/SKILL.md`.
- For wrappers, update the wrapper's public `observation_space` or `action_space`; route to `../wrappers-recording/SKILL.md`.
- For vectorized environments, distinguish single spaces from batched spaces; route to `../vectorization/SKILL.md`.

Do not silence `contains` failures by broadening spaces to `Box(-inf, inf, ...)` unless the data truly has no meaningful bounds. Overly broad spaces hide bugs and make model preprocessing harder.
