# Tensor Operations Troubleshooting

Use this reference when `rearrange`, `reduce`, `repeat`, `parse_shape`, or
`asnumpy` fails or a pattern produces an unexpected shape. Error messages are
shown as fragments because einops wraps them with operation, pattern, input
shape, and `axes_lengths` context.

## Fast diagnosis flow

1. Read the wrapper context: operation, pattern, input shape, and additional
   axis lengths.
2. Check rank first: does the left side have the right number of axes, after
   accounting for ellipsis?
3. Check spelling: every axis name must be consistently spelled and valid.
4. Check operation choice:
   - Use `rearrange` only when named axes appear on both sides.
   - Use `reduce` when axes disappear.
   - Use `repeat` when axes are introduced or copied.
5. Check every parenthesized input group: all known factors must divide the
   input axis length, and at most one factor may be inferred.
6. For list input, remember the list becomes a new zeroth axis before pattern
   interpretation.

## Symptom table

| Symptom / fragment | Likely cause | Recovery |
| --- | --- | --- |
| `Wrong shape: expected N dims. Received M-dim tensor.` | Left side rank does not match the input rank and no ellipsis accounts for the difference. | Fix the input layout assumption, add/remove axes on the left side, or use ellipsis for variable middle axes. |
| `Wrong shape: expected >=N dims. Received M-dim tensor.` | Pattern uses ellipsis but the tensor does not have enough dimensions for the explicitly named axes. | Reduce the explicit axes or pass a tensor with the documented rank. |
| `Shape mismatch, X != Y` | A provided or inferred composed axis product does not equal the actual input axis length. | Correct `axes_lengths`, use the right input layout, or change the factorization. |
| `Shape mismatch, can't divide axis of length X in chunks of Y` | Decomposition such as `(h h2)` used `h2=Y`, but the input axis length is not divisible by `Y`. | Validate divisibility before calling einops; choose a factor that divides the axis, crop/pad upstream, or use a different pooling/patch size. |
| `Could not infer sizes for {...}` | More than one unknown factor appears inside one parenthesized input group, e.g. `(h w)` without either `h` or `w`. | Supply enough `axes_lengths` so at most one factor is unknown, or parse shape from a source tensor. |
| `Identifiers only on one side of expression` | `rearrange` was used while a named axis appears only on one side. | If an axis disappears, use `reduce`; if an axis is new, use `repeat`; otherwise fix the spelling. |
| `Unexpected identifiers on the right side of reduce` | `reduce` introduced a new named axis on the right. | Use `repeat` after reduction if you need to add a new axis, or replace with `1`/`()` for a singleton keepdims axis. |
| `Unexpected identifiers on the left side of repeat` | `repeat` omitted a named input axis on the right. | Use `reduce` to remove axes, or preserve the axis on the right side. |
| `Specify sizes for new axes in repeat` | A new named axis appears on the right side of `repeat` without a length. | Pass the new axis size as a keyword, e.g. `repeat(x, "h w -> h w c", c=3)`, or use an anonymous numeric axis such as `5`. |
| `reduce_mean is not available for non-floating tensors` | `reduce(..., "mean")` was called on an integer or boolean tensor. | Cast to a floating dtype before the mean, or use a reduction appropriate for the dtype. |
| `Tensor type unknown to einops` | Backend dispatch could not recognize the object type, often because it is not a supported tensor/array or its framework module was not imported. | Convert to NumPy or a supported framework tensor first; ensure the framework package is imported before calling einops on its tensors. |
| `Indexing expression contains duplicate dimension` | The same axis name appears twice in one side of a core pattern where duplicates are not allowed. | Rename axes or route true repeated-index algebra to named `einsum` in the sibling sub-skill. |
| `Invalid axis identifier` | Axis name is not a valid identifier, starts/ends with `_`, contains illegal characters, or is otherwise disallowed. | Use names like `batch`, `channels`, `h2`; use `_` only in `parse_shape` to skip an axis. |
| `Ellipsis found in right side, but not left side` | Right side uses `...` but left side does not. | Add ellipsis to the left side or explicitly name all axes. |
| `Ellipsis inside parenthesis in the left side is not allowed` | Pattern attempted to decompose/collapse `(...)` on the left. | Put ellipsis as its own left-side axis; collapse ellipsis only on the right, e.g. `"... -> (...)"`. |
| `Rearrange/Reduce/Repeat can't be applied to an empty list` | List input has no tensors to stack. | Check list construction upstream; return early or provide at least one tensor. |

## Shape mismatch recovery playbooks

### Factor does not divide an axis

Typical failed pattern:

```python
pooled = reduce(video, "f b c (h h2) (w w2) -> f b c h w", "mean", h2=2, w2=2)
```

If height is odd, the error includes:

```text
Shape mismatch, can't divide axis of length ... in chunks of 2
```

Recovery:

```python
f, b, c, height, width = video.shape
h2 = w2 = 2
if height % h2 != 0 or width % w2 != 0:
    raise ValueError(f"height/width must be divisible by {h2}/{w2}; got {(height, width)}")
pooled = reduce(video, "f b c (h h2) (w w2) -> f b c h w", "mean", h2=h2, w2=w2)
```

If the user wants padding instead of rejection, pad/crop with the tensor
framework before einops, then apply the same pattern.

### More than one unknown factor

Failed pattern:

```python
# Cannot infer h and w from one flat axis unless one is supplied.
y = rearrange(x, "b (h w) c -> b h w c")
```

Recovery options:

```python
y = rearrange(x, "b (h w) c -> b h w c", h=32)
y = rearrange(x, "b (h w) c -> b h w c", h=32, w=32)
```

Or reuse shape facts:

```python
shape = parse_shape(reference_image, "b h w c")
y = rearrange(tokens, "b (h w) c -> b h w c", h=shape["h"], w=shape["w"])
```

### Wrong layout assumption

If a pattern expects NCHW but the tensor is NHWC, both rank checks and products
can still pass while output semantics are wrong. Use shape labels and sentinel
values:

```python
x = np.arange(2 * 3 * 4 * 5).reshape(2, 3, 4, 5)  # b c h w
nhwc = rearrange(x, "b c h w -> b h w c")
assert x[1, 2, 3, 4] == nhwc[1, 3, 4, 2]
```

## Invalid axes and spelling

### Axis only on one side in `rearrange`

Failed:

```python
rearrange(x, "b c h w -> b h w")
```

Recovery if dropping channels by max:

```python
reduce(x, "b c h w -> b h w", "max")
```

Recovery if the intended channel axis is singleton:

```python
rearrange(x, "b 1 h w -> b h w")
```

Recovery if it was a typo:

```python
rearrange(x, "batch channels height width -> batch height width channels")
```

### New axis in `repeat` without size

Failed:

```python
repeat(x, "h w -> h w c")
```

Recovery:

```python
repeat(x, "h w -> h w c", c=3)
# or
repeat(x, "h w -> h w 3")
```

### Duplicate axis names

Failed core pattern:

```python
rearrange(x, "b b c -> b c")
```

Recovery: use distinct semantic names:

```python
rearrange(x, "batch time channels -> batch (time channels)")
```

If the duplicate name means a diagonal, trace, contraction, or matrix product,
route to the named `einsum` sibling rather than forcing it into `rearrange`.

### Invalid identifier characters

Failed names include `h-2`, `.time`, `_hidden`, `hidden_`, or other strings that
are not valid axis identifiers. Use names like `h2`, `time`, `hidden`, or
`hidden_axis`. The single `_` is allowed only in `parse_shape` to skip a
dimension:

```python
parse_shape(x, "b _ h w")
```

## Non-floating mean

`mean` is deliberately guarded for non-floating tensors. Common recovery:

```python
x_float = x.astype("float32")              # NumPy
pooled = reduce(x_float, "b c h w -> b c", "mean")
```

For framework tensors, use that framework's cast operation. If the user needs an
integer result after averaging, cast back explicitly after the mean and document
the rounding policy.

## Unknown tensor type and `asnumpy`

Backend detection is lazy and type-based. Unknown types fail with:

```text
Tensor type unknown to einops <class '...'>
```

Recovery:

```python
# Make an unsupported object explicit before using einops.
x_np = np.asarray(x)
y = rearrange(x_np, "b c h w -> b h w c")
```

For framework tensors, ensure the framework is installed and imported in the
process before creating tensors. Avoid passing dataclasses, PIL images, lists of
non-tensors, generator objects, or wrapper classes directly. Extract the actual
tensor/array first.

`asnumpy` uses the same backend dispatch, so the same recovery applies. For
PyTorch tensors, conversion detaches and moves to CPU through the backend; for
unknown objects it cannot guess a conversion policy.

## List-input pitfalls

List input is powerful but easy to misread. einops first stacks the list on a
new zeroth axis, then applies the pattern.

### Pitfall: forgot the list axis

Failed or wrong:

```python
rearrange(images, "h w c -> h w c")  # images is a list
```

Correct:

```python
batch = rearrange(images, "b h w c -> b h w c")
```

### Pitfall: variable shapes

`rearrange(list_of_tensors, ...)` expects a backend stack operation to succeed.
If images have different heights or widths, stack cannot form a rectangular
tensor. Resize/pad them first, or route variable-length packing workflows to the
sibling packing sub-skill.

### Pitfall: mixed backend/device/dtype

A list should contain compatible tensors of the same backend. Mixed NumPy and
PyTorch tensors, or tensors on incompatible devices, should be normalized before
calling einops.

### Pitfall: empty list

Handle empty input explicitly:

```python
if not tensors:
    raise ValueError("expected at least one tensor to stack")
stacked = rearrange(tensors, "b ... -> b ...")
```

## Ellipsis pitfalls

### Right-side ellipsis without left-side ellipsis

Failed:

```python
rearrange(x, "b c h w -> b ... c")
```

Correct either names all axes:

```python
rearrange(x, "b c h w -> b h w c")
```

or uses ellipsis on both sides:

```python
rearrange(x, "b c ... -> b ... c")
```

### Parenthesized ellipsis on the left

Failed:

```python
rearrange(x, "(...) -> ...")
```

Correct collapse direction:

```python
flat = rearrange(x, "... -> (...)")
```

To unflatten, provide explicit axes:

```python
x = rearrange(flat, "(b c h w) -> b c h w", b=2, c=3, h=4, w=5)
```

## Difficult usability case: video pooling with non-divisible height

User situation: tensor shape is `(frames, batch, channels, height, width)` and
the user wants 2x2 pooling, but receives a message about `h2` not dividing
height.

Recommended answer shape:

```python
frames, batch, channels, height, width = video.shape
h2 = w2 = 2
if height % h2 or width % w2:
    raise ValueError(f"2x2 pooling requires divisible spatial dims; got height={height}, width={width}")
pooled = reduce(video, "frames batch channels (h h2) (w w2) -> frames batch channels h w", "max", h2=h2, w2=w2)
```

If the user expects batch-major output, combine with a rearrange:

```python
pooled_bfchw = rearrange(pooled, "frames batch channels h w -> batch frames channels h w")
```

## Difficult usability case: replacing view/permute/max-pool snippets

User situation: code contains framework-native `view`, `permute`, and pooling
snippets and needs readable einops plus shape assertions.

Recommended answer shape:

```python
# Equivalent to x.permute(0, 2, 3, 1)
x_nhwc = rearrange(x, "b c h w -> b h w c")
assert x_nhwc.shape == (x.shape[0], x.shape[2], x.shape[3], x.shape[1])

# Equivalent to flatten per sample.
flat = rearrange(x, "b c h w -> b (c h w)")
assert flat.shape[0] == x.shape[0]

# Equivalent to explicit 2x2 max-pooling if dims are divisible.
if x.shape[2] % 2 or x.shape[3] % 2:
    raise ValueError("height and width must be divisible by 2 for this pooling pattern")
pooled = reduce(x, "b c (h h2) (w w2) -> b c h w", "max", h2=2, w2=2)
```

Add sentinel assertions when order matters:

```python
assert x[0, 0, 0, 0] == x_nhwc[0, 0, 0, 0]
```
