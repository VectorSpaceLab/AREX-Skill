# Troubleshooting: Named Einsum And Packing

Start by identifying the pattern family:

- `einsum` patterns have commas and an explicit `->`.
- `pack`/`unpack` patterns have no arrow and exactly one literal `*` token.

## Einsum Failures

| Error fragment | Most likely cause | Fix |
| --- | --- | --- |
| `Einsum pattern must contain '->'` | The pattern is NumPy shorthand or an input-only expression. | Add `->` and the intended output axes, even for scalar output: `"i ->"`. |
| `last argument ... must be a string` | The pattern was passed first, NumPy-style, or a tensor was accidentally last. | Use tensors-first order: `einsum(x, y, "batch dim, dim out -> batch out")`. |
| `` `einops.einsum` takes at minimum two arguments`` | Missing tensor or missing pattern. | Pass at least one tensor and one pattern string. |
| `Shape rearrangement is not yet supported in einsum` | Pattern contains grouped/composed axes such as `(head channel)` or `(height width)`. | Split/merge axes before or after `einsum` with a reshape/rearrange step; keep `einsum` axes simple. |
| `Singleton () axes are not yet supported` | Pattern uses `()` to add/drop a length-1 axis. | Add/drop singleton axes outside `einsum`. |
| `Anonymous axes are not yet supported` | Pattern uses numeric axes such as `2`. | Replace with a named axis and handle shape constraints outside `einsum`. |
| `Invalid axis identifier` | Axis token is not a valid einops identifier. | Use names like `batch`, `head`, `channel`; avoid leading/trailing underscores or digit-leading names. |
| `Unknown axis ... on right side` | Output names an axis that appears in no input term. | Remove the output-only axis or create it with a separate operation. |
| `Indexing expression contains duplicate dimension` | Duplicate axis appears where duplicates are invalid, usually the output side. | Output each axis at most once. Repeated input axes are only for diagonal/trace semantics. |
| Backend shape error | Operand count or axis lengths do not match the pattern. | Compare with a small `np.einsum` formula, print operand shapes, and check every shared axis size. |

### Tensors-First Repair

Wrong:

```python
einsum("batch channel -> batch", x)
```

Right:

```python
einsum(x, "batch channel -> batch")
```

### Missing Arrow Repair

Wrong:

```python
einsum(x, "batch channel")
```

Right:

```python
einsum(x, "batch channel -> batch")
```

### Grouped Axis Repair

Wrong:

```python
einsum(x, w, "batch (head channel), head channel out -> batch out")
```

Right pattern for the contraction after a separate reshape step:

```python
einsum(x_bhc, w, "batch head channel, head channel out -> batch out")
```

The separate reshape from `x` to `x_bhc` belongs to `tensor-operations`.

## Packing Pattern Failures

| Error fragment | Most likely cause | Fix |
| --- | --- | --- |
| `No *-axis` | Pattern has no `*`. | Use one literal star token, for example `"batch * channel"`. |
| `Duplicates in axes names` | Pattern repeats an axis name or contains multiple `*` tokens. | Make every token unique and keep exactly one `*`. |
| `Invalid axis name` | Non-star token is not a valid einops axis name. | Rename `_bad`, `bad_`, `1bad`, or punctuation-containing tokens. |
| `assumes at least ... axes` | One tensor has too few dimensions for axes before/after `*`. | Move `*`, adjust the pattern, or add the missing axes before packing. |
| Backend concat error | Shared leading/trailing axes disagree across inputs. | Print all input shapes and check axes before and after `*`. |

### Star-Axis Grammar Check

Valid:

```python
pack([class_token_bc, image_tokens_bhwc], "batch * channel")
```

Invalid:

```python
pack([x], "batch channel")      # no star
pack([x], "batch * * channel")  # duplicate star
pack([x], "batch batch *")      # duplicate axis name
```

## `packed_shapes` / `PS` Failures

| Error fragment | Most likely cause | Fix |
| --- | --- | --- |
| `received input of wrong dim` | `unpack` pattern rank does not match packed tensor rank. | Use a pattern with the same token count as the packed tensor shape. |
| `more than one -1` | More than one inferred dimension appears across `packed_shapes`. | Compute all but one shape explicitly. |
| `could not split axis` | Requested `packed_shapes` cannot reshape slices into outputs. | Use the original `ps` from `pack`, or recompute products and compare with packed-axis length. |
| Silent wrong modality order | `ps` entries were reordered, dropped, or reused after packed-axis order changed. | Keep `ps` paired with its packed tensor and unpack in the original logical order. |
| Zero-length output surprise | A `packed_shapes` entry contains `0` or `-1` inferred to zero. | Preserve it if the modality is genuinely empty; otherwise validate upstream lengths. |

### Validate Manual `packed_shapes`

For known shapes, the packed axis should equal the sum of products:

```python
import math

def product(shape):
    return math.prod(shape) if len(shape) else 1

packed_shapes = [[], [mask_h, mask_w], [num_classes]]
assert packed.shape[star_axis] == sum(product(shape) for shape in packed_shapes)
```

For one `-1`, validate after unpack:

```python
parts = unpack(packed, [[known_left], [-1], [known_right]], "batch * channel")
assert parts[1].shape[1] >= 0
```

If any known part can over-consume the packed axis, avoid relying only on
backend slicing behavior. Compute the intended split positions or run a
round-trip smoke case with explicit values.

## Round-Trip Debugging Procedure

1. Reduce the problem to two or three small arrays with deterministic values.
2. For `einsum`, compare named einops output with `np.einsum` using compact axis
   names and `np.testing.assert_allclose`.
3. For `pack`, immediately run `unpack(packed, ps, same_pattern)` and compare
   every shape and value with the originals.
4. For `unpack` with manual shapes, pack the outputs again and compare with the
   original packed tensor.
5. If zero-length tensors are involved, assert both the value round trip and the
   zero-length shape; do not drop empty modalities from `ps`.
6. Re-run the bundled smoke scripts and adapt the nearest passing case to the
   failing shapes.
