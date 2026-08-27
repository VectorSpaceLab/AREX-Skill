# API Reference: Named Einsum And Packing

This reference is for runtime use of `einops.einsum`, `einops.pack`, and
`einops.unpack` after `einops` is installed. It intentionally avoids depending
on source checkout files.

## Import Surface And Verified Signatures

```python
from einops import einsum, pack, unpack
```

| Function | Signature | Return |
| --- | --- | --- |
| `einsum` | `einsum(*tensors_and_pattern)` | Tensor of the same backend family as the first tensor. |
| `pack` | `pack(tensors, pattern: str)` | `(packed_tensor, packed_shapes)` where `packed_shapes` is `PS`. |
| `unpack` | `unpack(tensor, packed_shapes, pattern: str)` | `list[tensor]`, one output for each entry in `packed_shapes`. |

The installed package facts for this generated skill included `einops` version
`0.9.0dev` at runtime and distribution metadata `0.9.0.dev0`.

## `einsum(*tensors_and_pattern)`

### Parameters

| Parameter | Meaning |
| --- | --- |
| `tensor1, tensor2, ...` | One or more tensor-like objects supported by einops/backends. Keep operands from one compatible backend. |
| `pattern` | Last positional argument. A string with comma-separated input axis specifications, an explicit `->`, and an output axis specification. |

### Call Order

`einops.einsum` is tensors-first, pattern-last:

```python
scores = einsum(q, k, "batch query head channel, batch key head channel -> batch head query key")
```

This differs from NumPy:

```python
# NumPy style, not einops style:
np_scores = np.einsum("bqhc,bkhc->bhqk", q, k)
```

A common conversion is therefore:

1. Move the pattern string from first position to last position.
2. Replace one-letter symbols with readable names.
3. Keep commas and `->` structure aligned with the number of operands.
4. Compare against the original backend formula on a small deterministic array.

### Pattern Semantics

- Each axis name is a Python-identifier-like token such as `batch`, `head`,
  `in_dim`, or `channel`.
- Multi-letter axis names are supported. Internally, each distinct name is
  mapped to a compact single-letter backend einsum symbol in first-seen order.
- At most the backend compact alphabet is available for distinct named axes;
  this implementation raises `RuntimeError: Too many axes in einsum.` if the
  compact mapping is exhausted.
- Axes that appear on an input side but not on the output side are reduced by
  summation.
- Repeating the same axis name inside one input term selects a diagonal or
  trace-style contraction, matching ordinary einsum semantics.
- `...` can represent arbitrary dimensions and can appear in input and output
  positions accepted by backend einsum.
- Output axes must come from input axes; introducing a new output-only axis is
  rejected.

### Supported Examples

```python
# Matrix multiplication / linear projection.
y = einsum(x, w, "batch in_dim, in_dim out_dim -> batch out_dim")

# Attention scores from query/key tensors.
scores = einsum(
    q, k,
    "batch query head channel, batch key head channel -> batch head query key",
)

# Ellipsis-aware projection.
y = einsum(weights, data, "out_dim in_dim, ... in_dim -> ... out_dim")

# Trace / diagonal reduction.
trace = einsum(matrix, "row row ->")

# Preserve the diagonal axis while reducing intervening ellipsis-compatible axes.
diagonal = einsum(x, "token ... token -> token ...")
```

### Current Limitations

`einops.einsum` is intentionally narrower than the full `rearrange` grammar.
Do not put these constructs inside an `einsum` pattern:

| Unsupported construct | Example | Recovery |
| --- | --- | --- |
| Grouped/composed axes | `"batch (head channel) -> batch head channel"` | Use `rearrange` before or after `einsum`; route the reshape recipe to `tensor-operations`. |
| Singleton axes | `"batch () channel -> batch channel"` | Insert or remove length-1 axes outside `einsum`. |
| Anonymous numeric axes | `"batch 2 channel -> batch channel"` | Use a named axis plus explicit shape handling outside `einsum`. |
| Missing explicit output | `"batch channel"` | Add `->` and the intended output axes. |
| Pattern-first call | `einsum("b c -> b", x)` | Use `einsum(x, "batch channel -> batch")`. |

Other practical constraints:

- No `axes_lengths` keyword arguments are accepted by `einsum`.
- It does not perform reshape, split, merge, singleton insertion, or arbitrary
  axis creation; compose it with `rearrange`, `repeat`, or `pack`/`unpack` when
  those are needed.
- Duplicate axes are meaningful on input terms but duplicate output axes are not
  valid.
- Operand count, shape compatibility, dtype promotion, precision, and gradient
  behavior are ultimately delegated to the active backend's `einsum`.

### Error Behavior

| Symptom / fragment | Raised by | Typical cause | Fix |
| --- | --- | --- | --- |
| `Einsum pattern must contain '->'` | einops validation | Pattern omits explicit arrow. | Add `-> output_axes`; do not rely on NumPy implicit output. |
| `The last argument ... must be a string` | einops validation | Pattern placed first, or a tensor passed last. | Call `einsum(t1, t2, "pattern")`. |
| `` `einops.einsum` takes at minimum two arguments`` | einops validation | No tensor or no pattern supplied. | Pass at least one tensor and one pattern. |
| `Shape rearrangement is not yet supported in einsum` | einops validation | A grouped axis such as `(a b)` appears. | Reshape outside `einsum`. |
| `Singleton () axes are not yet supported in einsum` | einops validation | `()` appears in pattern. | Add/drop singleton axes outside `einsum`. |
| `Anonymous axes are not yet supported in einsum` | einops validation | Numeric anonymous axis such as `2` appears. | Use named axes and external reshape. |
| `Invalid axis identifier` | einops parser | Axis name is not valid for einops parsing. | Rename the axis; avoid leading/trailing underscores. |
| `Unknown axis ... on right side` | einops validation | Output references an axis absent from inputs. | Add the axis to an input or remove it from output. |
| `Indexing expression contains duplicate dimension` | einops parser | Duplicate axis on output side. | Output each axis at most once. |
| Backend shape/broadcast error | Backend einsum | Incompatible operand dimensions or wrong operand count. | Check operand count, axis sizes, and ellipsis placement. |

## `pack(tensors, pattern: str)`

### Parameters

| Parameter | Meaning |
| --- | --- |
| `tensors` | Non-empty sequence of tensors. Inputs may have different ranks as long as axes before and after `*` match the pattern. |
| `pattern` | Space-separated axes with exactly one literal `*`, for example `"batch * channel"`. No arrow is used. |

### Return Contract

```python
packed, ps = pack([class_token_bc, image_tokens_bhwc, text_tokens_btc], "batch * channel")
```

- `packed` has one axis for every token in the pattern. The `*` position is the
  concatenation axis.
- `ps` / `packed_shapes` is a list with one entry per input tensor.
- Each `ps[i]` records the original shape segment that was consumed by `*` for
  input `i`.
- Empty packed shape `()` means that input contributed one element along the
  packed axis with no explicit axis in its original shape.
- A zero length such as `(0,)` is valid and contributes zero elements.

For pattern `"i j * k"` and input shapes `(2, 3, 5)`, `(2, 3, 7, 5)`, and
`(2, 3, 7, 9, 5)`, the shared axes are `i=2`, `j=3`, `k=5`; the packed shapes
are `()`, `(7,)`, and `(7, 9)`; the packed tensor shape is `(2, 3, 71, 5)`.

### Star-Axis Grammar

For `pattern.split()`:

- There must be exactly one token equal to `*`.
- No token may be duplicated; this includes `*`.
- Every non-star token must be a valid einops axis name.
- Axes before `*` are matched against leading dimensions of every input.
- Axes after `*` are matched against trailing dimensions of every input.
- Every input rank must be at least `len(axes_before_star) + len(axes_after_star)`.
- The dimensions between the leading and trailing shared axes are flattened by
  product and concatenated at the star position.

`pack` is a generic concatenation/stacking primitive, not arbitrary
rearrangement. It does not reorder axes; it only preserves leading/trailing
axes, flattens the middle selected by `*`, and concatenates.

### Error Behavior

| Symptom / fragment | Typical cause | Fix |
| --- | --- | --- |
| `No *-axis` | Pattern has no literal `*`. | Add one `*` token. |
| `Duplicates in axes names` | Pattern repeats an axis name or has multiple `*` tokens. | Use unique axis names and exactly one `*`. |
| `Invalid axis name` | Non-star token is not a valid axis name. | Rename the axis; avoid names like `_w`, `w_`, or `1w`. |
| `assumes at least ... axes` | An input tensor rank is too small for axes before/after `*`. | Adjust the pattern or input rank. |
| Backend concat/shape error | Shared axes before/after `*` have incompatible sizes or backend tensors cannot concatenate. | Check all leading/trailing dimensions and backend compatibility. |

## `unpack(tensor, packed_shapes, pattern: str)`

### Parameters

| Parameter | Meaning |
| --- | --- |
| `tensor` | Packed tensor whose rank is exactly the number of tokens in `pattern`. |
| `packed_shapes` | Sequence of shapes that replace `*`, one output per shape. Usually this is the `ps` returned by `pack`. |
| `pattern` | Same one-star no-arrow grammar as `pack`; it identifies which axis to split. |

### Return Contract

```python
class_out, image_out, text_out = unpack(processed, ps, "batch * channel_out")
```

- The packed axis is split into one slice per `packed_shapes` entry.
- Each output shape is:
  `shape_before_star + packed_shapes[i] + shape_after_star`.
- `()` / `[]` in `packed_shapes` contributes one packed element and no explicit
  axis in the output.
- `[0]` or `(0,)` contributes zero elements and creates a zero-length output.
- `-1` may appear in one packed shape entry to infer a dimension from remaining
  packed-axis length.

Patterns for `pack` and `unpack` may differ when a model changes non-packed
axes. For example, `pack(..., "batch * channel")` can later be unpacked with
`unpack(processed, ps, "batch * channel_out")` if the packed axis still has the
same segmentation and the new trailing axis is `channel_out`.

### `-1` Inference Rules

- At most one `-1` is allowed across all `packed_shapes` entries.
- If there is no `-1`, known products must exactly consume the packed axis.
- If there is one `-1`, known products before and after that entry are used to
  determine the remaining slice length; backend reshape then infers the `-1`
  dimension inside that slice.
- Inferred dimensions can be zero when remaining slice length is zero.
- For externally supplied `packed_shapes`, validate products and round trips;
  backend slicing can allow some degenerate overlapping/empty cases that are
  not semantically intended.

### Error Behavior

| Symptom / fragment | Typical cause | Fix |
| --- | --- | --- |
| `No *-axis` | Pattern has no literal `*`. | Use a one-star packing pattern. |
| `Duplicates in axes names` | Pattern repeats a token or includes multiple `*` tokens. | Make the pattern tokens unique. |
| `received input of wrong dim` | Packed tensor rank does not equal pattern token count. | Match the pattern to the packed tensor rank. |
| `more than one -1` | More than one packed shape contains `-1`. | Use exactly one inferred shape or compute all shapes explicitly. |
| `could not split axis` | `packed_shapes` products cannot reshape slices into requested outputs. | Use the original `PS`, fix manual shapes, or validate products against the packed axis. |
| Backend reshape/slice error | Incompatible split products, dimensions, or backend behavior. | Check `sum(product(ps_i))` and each output shape. |

## Provenance Summary

The behavior above was distilled from the public README API section, the public
runtime implementations of einsum and packing, repository tests covering
functional einsum and packing cases, and tutorial examples for pack/unpack,
auto-batching, class-token flows, multimodal packing, and multi-output
prediction splitting. Relative evidence names: `README.md`, `einops/einops.py`,
`einops/packing.py`, `einops/tests/test_einsum.py`,
`einops/tests/test_packing.py`, `docs/4-pack-and-unpack.ipynb`, and
`docs/2-einops-for-deep-learning.ipynb`.
