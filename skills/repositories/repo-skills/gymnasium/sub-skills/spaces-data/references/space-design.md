# Space Design Reference

Gymnasium spaces are the public contract for valid actions and observations. They should be explicit enough that agents, wrappers, validators, vector environments, and RL models can infer shape, dtype, range, and structure without inspecting implementation details.

## Base Contract

Every `gymnasium.spaces.Space` exposes:

| Member | Use |
| --- | --- |
| `shape` | Static numpy-array shape when a space has one; composite or dynamic spaces can use `None`. |
| `dtype` | Element dtype for numpy-like spaces; composite spaces often use `None`. |
| `sample(mask=None, probability=None)` | Generate a valid sample; only some spaces support masks or probabilities. Do not pass both. |
| `contains(x)` / `x in space` | Validate shape, dtype/castability, bounds, keys, lengths, or graph structure. |
| `seed(seed=None)` | Seed the space RNG and, for composites, subspace RNGs. Return shape depends on the space. |
| `to_jsonable(sample_n)` | Convert a batch of samples to JSON-compatible Python data. |
| `from_jsonable(sample_n)` | Convert a JSON-compatible batch back to samples with expected dtypes where supported. |
| `is_np_flattenable` | Whether `flatdim` can compute a single static flat vector length. |

Prefer built-in spaces over custom `Space` subclasses. Custom spaces may work with `contains` and `sample`, but Gymnasium's vector utilities and many RL libraries assume the built-in space types.

## Fundamental Spaces

| Space | Constructor | Use when | Critical rules |
| --- | --- | --- | --- |
| `Box` | `Box(low, high, shape=None, dtype=np.float32, seed=None)` | Continuous or array-valued data with per-element lower/upper bounds. | `dtype` is required and must be bool, integer, unsigned integer, or float. Shape is inferred from array bounds, scalar bounds default to `(1,)` unless `shape` is supplied. |
| `Discrete` | `Discrete(n, seed=None, start=0, dtype=np.int64)` | One scalar integer category in `{start, ..., start + n - 1}`. | `n > 0`; `dtype` must be integer. Nonzero `start` changes valid values and one-hot flatten offsets. |
| `MultiBinary` | `MultiBinary(n, seed=None)` | Fixed-shape binary vector/tensor of `0` and `1`. | `n` can be an int or positive shape sequence. Samples use `np.int8`; `contains` accepts correct-shape arrays or list-like sequences containing only 0/1. |
| `MultiDiscrete` | `MultiDiscrete(nvec, dtype=np.int64, seed=None, start=None)` | Fixed product of categorical variables, such as gamepad buttons. | `nvec` is counts, not max values. Valid element `x[i]` satisfies `start[i] <= x[i] < start[i] + nvec[i]`. `start` shape must match `nvec`. |
| `Text` | `Text(max_length, min_length=1, charset=..., seed=None)` | Variable-length strings over a bounded character set. | Length bounds are inclusive. Default `min_length=1` rejects empty strings. `charset` may be a string or `frozenset`. |

### `Box` Shape and Dtype Checklist

- If both `low` and `high` are scalars and `shape` is omitted, the shape is `(1,)`, not scalar `()`.
- If either bound is an array, array shape drives or must match `shape`.
- Scalar bounds broadcast to the provided `shape`.
- `low.shape` and `high.shape` must match when both are arrays.
- Integer and unsigned integer dtypes reject bounds outside the dtype range; unsigned and bool boxes cannot use `-np.inf` or `np.inf` in the unsupported direction.
- `np.nan` is never a valid bound.
- For integer `Box`, sampling floors sampled values and returns the declared integer dtype.
- `Box.sample(mask=...)` and `Box.sample(probability=...)` are unsupported.

Use `Box(..., shape=(), dtype=...)` only when a true zero-dimensional numpy scalar is intended. Use `shape=(1,)` when models or wrappers expect a one-element vector.

## Sampling Masks and Probabilities

Only pass masks or probability arrays when the space implementation supports them.

| Space | Mask shape and dtype | Probability shape and dtype | Notes |
| --- | --- | --- | --- |
| `Discrete(n, start=...)` | `np.ndarray` shape `(n,)`, dtype `np.int8`, values 0/1. | shape `(n,)`, dtype `np.float64`, values in `[0, 1]`, sum exactly 1. | If an all-zero mask is used, `sample` returns `start`. |
| `MultiBinary(shape)` | same shape as space, dtype `np.int8`, values 0/1/2. | same shape as space, dtype `np.float64`, values in `[0, 1]`. | Mask value `2` means random bit; `0`/`1` force the bit. |
| `MultiDiscrete(nvec)` | nested tuple matching `nvec` structure, each leaf length equals that categorical count, dtype `np.int8`. | same nested structure, leaf dtype `np.float64`, each leaf sums to 1. | For multidimensional `nvec`, masks are tuples of tuples mirroring axes. |
| `Text` | tuple `(length, char_mask)` where length is `None` or int, char mask length is charset size, dtype `np.int8`. | tuple `(length, char_probability)`, dtype `np.float64`, probabilities sum to 1. | All-zero char mask raises if `min_length > 0`. |
| `Dict` | dict with exactly the same keys as `space.spaces`. | dict with exactly the same keys as `space.spaces`. | Values are delegated to each subspace; use `None` for subspaces that do not support masks. |
| `Tuple` / `OneOf` | tuple length equals number of subspaces. | tuple length equals number of subspaces. | Values are delegated to selected subspaces. |
| `Sequence` | `(length_mask, feature_mask)`. | `(length_mask, feature_probability)`. | `length_mask` is `None`, a nonnegative int, or a 1-D integer array of allowed lengths. |
| `Graph` | `(node_mask, edge_mask)` for discrete node/edge spaces. | `(node_probability, edge_probability)` for discrete node/edge spaces. | `Box` node/edge feature spaces do not accept masks/probabilities. |

Do not pass both `mask` and `probability`; Gymnasium raises an error for all built-in spaces that support either argument.

## Composite Spaces

| Space | Constructor | Best fit | Flattening notes |
| --- | --- | --- | --- |
| `Dict` | `Dict(spaces=None, seed=None, **spaces_kwargs)` | Named observations/actions such as `{"image": ..., "state": ...}`. | Numpy-flattenable only if every subspace is. Plain dict inputs are sorted by key when keys are comparable; `OrderedDict`, sequence of pairs, and kwargs preserve insertion order. |
| `Tuple` | `Tuple(spaces, seed=None)` | Positional product of heterogeneous spaces. | Numpy-flattenable only if every subspace is. `contains` promotes list/array input to tuple. |
| `Sequence` | `Sequence(space, seed=None, stack=False)` | Variable-length tuple/list-like observations. | `is_np_flattenable` is false because length is dynamic. With `stack=True`, samples are batched arrays through vector utilities. |
| `Graph` | `Graph(node_space, edge_space, seed=None)` | Variable-size graph observations. | Node space must be `Box` or `Discrete`; edge space must be `None`, `Box`, or `Discrete`. Static `flatdim(Graph)` is unavailable, but `flatten_space(Graph)` returns a graph with flattened node/edge feature spaces. |
| `OneOf` | `OneOf(spaces, seed=None)` | One active choice among several subspaces. | Sample shape is `(index, sample)`. Numpy-flattenable only if all subspaces are; flattened representation stores index plus padded flattened sample. |

For model inputs, prefer fixed-shape `Box`, `Discrete`, `MultiBinary`, `MultiDiscrete`, or numpy-flattenable `Dict`/`Tuple`. Use `Sequence`, `Graph`, or `OneOf` only when the downstream model/wrapper explicitly supports dynamic or variant data, or add a wrapper/model adapter that converts them to a supported representation.

## Seeding Rules

- `space.seed(int)` makes future `space.sample()` calls reproducible for that space object.
- `Dict.seed(dict)` requires exactly the same keys as the `Dict` space and can contain nested seed dictionaries.
- `Tuple.seed(list_or_tuple)` length must equal the number of subspaces.
- `Sequence.seed((sequence_seed, feature_seed))` seeds both the sequence length generator and the feature space.
- `Graph.seed((graph_seed, node_seed))` is valid when `edge_space is None`; use three values when an edge space exists.
- `OneOf.seed((root_seed, sub_seed_0, sub_seed_1, ...))` requires one root seed plus one seed per subspace.

Environment-level reproducibility normally belongs in `env.reset(seed=...)`; use `../environment-api/SKILL.md` for full environment seeding. Space-level seeding is useful for standalone data-contract tests and deterministic helper scripts.

## Updating Env and Wrapper Contracts

Whenever observations or actions are transformed, update the corresponding space at the same boundary:

- A custom env sets `self.observation_space` and `self.action_space` to match values returned by `reset`, `step`, and expected by `step(action)`.
- An `ObservationWrapper` that changes observation shape, dtype, keys, or bounds must update `self.observation_space`.
- An `ActionWrapper` that accepts a different public action representation must update `self.action_space` and map to the wrapped env's action space.
- A `RewardWrapper` normally does not alter spaces.

Use `../wrappers-recording/SKILL.md` for wrapper implementation details and `../environment-api/SKILL.md` for `check_env` validation.
