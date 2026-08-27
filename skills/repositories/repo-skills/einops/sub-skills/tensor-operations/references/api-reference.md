# Tensor Operations API Reference

This reference covers the core `einops` functions owned by the
`tensor-operations` sub-skill. It is self-contained for runtime use and bundles
the API facts future agents need.

## Verified package facts

Runtime inspection during skill generation verified the development runtime as
`einops.__version__ == "0.9.0dev"`; distribution metadata was reported as
`0.9.0.dev0`. The public core imports are:

```python
from einops import rearrange, reduce, repeat, parse_shape, asnumpy
```

Also available in `einops` but routed elsewhere in this repo skill:
`pack`, `unpack`, and `einsum`.

## Core signatures

| Function | Verified signature | Primary use | Return behavior |
| --- | --- | --- | --- |
| `rearrange` | `rearrange(tensor, pattern: str, **axes_lengths)` | Transpose/permutation, reshape/view, squeeze/unsqueeze, stack, concatenate, split/combine axes. | Tensor of the same backend/type as input when backend supports it; for list input, a single stacked/combined tensor. May return a view when backend and transform allow it. |
| `reduce` | `reduce(tensor, pattern: str, reduction, **axes_lengths)` | Combine rearrangement with reductions over axes omitted from the right side. | Tensor of the same backend/type as input after reducing named axes. Callable reductions return the callable's tensor output. |
| `repeat` | `repeat(tensor, pattern: str, **axes_lengths)` | Broadcast/tile/repeat existing values along new or composed axes. | Tensor of the same backend/type as input, with new axes broadcast or repeated according to pattern. |
| `parse_shape` | `parse_shape(x, pattern: str)` | Read named dimensions from a tensor's shape for later `axes_lengths` checks. | `dict` mapping named axes to lengths; symbolic frameworks may return symbolic shape values. |
| `asnumpy` | `asnumpy(tensor)` | Convert an imperative supported backend tensor to `numpy.ndarray`. | NumPy array converted through the active einops backend. |

Implementation note: `rearrange` and `repeat` are implemented through the same
recipe engine as `reduce`, with special internal reduction types
`"rearrange"` and `"repeat"`.

## Pattern grammar and invariants

Patterns have the form:

```text
left-side axes -> right-side axes
```

- Axis names are Python-like identifiers. They must not start or end with `_`.
  The single underscore `_` is special only in `parse_shape`, where it skips a
  dimension.
- Whitespace separates axes; names can be long (`batch`, `height`) or short
  (`b`, `h`).
- Parentheses compose or decompose axes, e.g. `(c h w)` or `(h h2)`.
- `1` and `()` denote singleton axes.
- Numeric anonymous axes greater than one are allowed where the operation can
  prove their role; they are especially useful for reduced axes or new repeated
  axes, e.g. `reduce(x, "b (h 2) (w 2) c -> b h w c", "mean")` and
  `repeat(x, "h w -> h 5 w")`.
- Ellipsis `...` stands for a run of zero or more axes and can make patterns
  rank-polymorphic.
- Ellipsis may be parenthesized on the right side to collapse all omitted axes,
  e.g. `rearrange(x, "... -> (...)")`; ellipsis inside parentheses on the left
  side is rejected.
- If the right side has ellipsis, the left side must also have ellipsis.

### Operation-specific axis rules

| Operation | Axis rule |
| --- | --- |
| `rearrange` | Every non-anonymous named axis must appear on both sides. Named axes only on one side raise `Identifiers only on one side of expression`. Non-unit anonymous axes are not supported for ordinary `rearrange`, except singleton `1`/`()`. |
| `reduce` | Named axes may disappear from left to right; the disappeared axes are reduced. Named axes may not appear only on the right. |
| `repeat` | Named axes may be introduced on the right, but every new named axis must have a supplied size in `axes_lengths`. Named axes may not disappear from the left. |
| `parse_shape` | No `->`. Pattern describes the input shape only. Use `_` to skip dimensions. Composite axes such as `(h w)` are not accepted by `parse_shape`. |

### C-order axis composition

When composing axes, einops uses C-order enumeration: the rightmost component in
parentheses changes fastest. For example:

```python
x = np.arange(2 * 3).reshape(2, 3)
y = rearrange(x, "a b -> (a b)")
assert y.tolist() == [0, 1, 2, 3, 4, 5]
```

The order inside parentheses is therefore part of the contract. These are not
interchangeable:

```python
rearrange(x, "b h w c -> h (b w) c")
rearrange(x, "b h w c -> h (w b) c")
```

## `rearrange`

Use `rearrange` for shape transformations that preserve all element values and
only move, group, split, stack, concatenate, squeeze, or unsqueeze axes.

Common examples:

```python
# channels-first image batch to channels-last
x = rearrange(x, "b c h w -> b h w c")

# flatten every sample
features = rearrange(x, "b c h w -> b (c h w)")

# unflatten using a checked axis length
x = rearrange(features, "b (c h w) -> b c h w", c=3, h=32, w=32)

# split an embedding/group axis into separate tensors via Python unpacking
part1, part2 = rearrange(x, "b (part c) h w -> part b c h w", part=2)

# stack a list of same-shaped images on the first axis, then transpose
x = rearrange(list_of_images, "b h w c -> b c h w")

# concatenate list elements horizontally
strip = rearrange(list_of_images, "b h w c -> h (b w) c")
```

List input behavior: if `tensor` is a non-empty list, einops asks the backend of
the first element to stack the list on a new zeroth dimension before applying
the pattern. All list elements must be compatible tensors of the same backend,
shape, dtype/device constraints expected by that backend. An empty list raises a
TypeError before pattern processing.

## `reduce`

Use `reduce` when some axes should disappear or become singleton/pooled axes.
The `reduction` argument can be a supported name or a callable.

Verified built-in reduction names:

```python
("min", "max", "sum", "mean", "prod", "any", "all")
```

Common examples:

```python
# global average pooling from NCHW to NC
pooled = reduce(x, "b c h w -> b c", "mean")

# 2D max pooling, kernel 2x2, channels-first
pooled = reduce(x, "b c (h h2) (w w2) -> b c h w", "max", h2=2, w2=2)

# keepdims-like per-image channel mean for broadcasting
centered = x - reduce(x, "b c h w -> b c 1 1", "mean")
centered_same = x - reduce(x, "b c h w -> b c () ()", "mean")

# reduce every middle axis while preserving endpoints
summary = reduce(x, "batch ... channels -> batch channels", "sum")

# boolean reductions
any_positive = reduce(mask, "b h w -> b", "any")
all_valid = reduce(mask, "b h w -> b", "all")
```

### Callable reductions

A callable reduction must accept the tensor and a tuple of reduced axis indices:

```python
def logsumexp_numpy(x, axes):
    max_keep = np.max(x, axis=axes, keepdims=True)
    return np.log(np.sum(np.exp(x - max_keep), axis=axes)) + np.squeeze(max_keep, axis=axes)

out = reduce(x, "b c h w -> b c", logsumexp_numpy)
```

The callable receives axes after einops has arranged the recipe, so write it as
a backend-native reduction over exactly those axes. The callable must be
hashable because transformation recipes are cached.

### Mean and dtypes

The core engine intentionally rejects `"mean"` for non-floating tensors for
backends where average on integer tensors is not consistently available. The
error fragment is:

```text
reduce_mean is not available for non-floating tensors
```

Cast integer data to a floating dtype before `reduce(..., "mean")`, or use
`"sum"`, `"max"`, `"min"`, `"prod"`, `"any"`, or `"all"` when those match the
intended semantics.

## `repeat`

Use `repeat` to add axes, tile/broadcast values, or upsample by copying values.
Every new named axis on the right side must be specified by `axes_lengths`.
Anonymous numeric axes are also supported.

```python
# grayscale to RGB-like channels
rgb = repeat(gray, "h w -> h w c", c=3)

# add a copy axis at the front
copies = repeat(x, "b c -> n b c", n=4)

# repeat along existing spatial axes
upsampled = repeat(image, "h w -> (h h2) (w w2)", h2=2, w2=2)

# anonymous new axis of length 5
expanded = repeat(x, "b c -> b 5 c")
```

A useful verification trick from the source tests is to reverse a repeat with
`reduce` using both `"min"` and `"max"`; if both recover the original tensor,
then every repeated tile agrees with the source values.

## `parse_shape`

`parse_shape(x, pattern)` reads shape facts without moving data.

```python
x = np.zeros([2, 3, 5, 7])
parse_shape(x, "batch _ h w")
# {'batch': 2, 'h': 5, 'w': 7}

flat = np.zeros([2 * 10 * 5 * 7])
shape = parse_shape(x, "b _ h w")  # provides b/h/w; c is inferred from the flat length
y = rearrange(flat, "(b c h w) -> b c h w", **shape)
assert y.shape == (2, 10, 5, 7)
```

Notes:

- Use `_` to skip axes. Repeated ordinary names are rejected.
- `parse_shape` can parse ellipsis in simple shape patterns, e.g.
  `parse_shape(x, "a ... b")` returns only `a` and `b`.
- Anonymous axes can assert literal dimensions: `parse_shape(x, "a 1 2")`.
- Composite axes are not supported in `parse_shape`; use explicit checks plus
  `rearrange`/`reduce` with `axes_lengths` for composed shapes.
- For symbolic frameworks, values may be symbolic objects rather than Python
  integers. Pass the returned mapping into einops operations instead of forcing
  integer conversion unless the backend supports it.

## `asnumpy`

`asnumpy(tensor)` converts a known imperative backend tensor to a NumPy array by
using einops' active backend. It is useful in examples, smoke checks, or
backend-neutral assertions after core operations:

```python
from einops import asnumpy, reduce

pooled = reduce(x, "b c h w -> b c", "mean")
pooled_np = asnumpy(pooled)
```

Backend notes distilled from the implementation:

- NumPy input returns a NumPy array directly.
- PyTorch conversion detaches the tensor, moves it to CPU, and calls `.numpy()`.
- JAX, CuPy, TensorFlow, OneFlow, Paddle, tinygrad, and MLX have backend-specific
  conversions when the corresponding backend module has already been imported
  and the tensor type is recognized.
- Unknown objects raise a `Tensor type unknown to einops ...` error from backend
  dispatch. Convert unsupported objects to a supported tensor/array first.

## Error context added by einops

For `rearrange`, `reduce`, and `repeat`, failures are wrapped with context that
includes the operation, pattern, input shape or list-input note, and provided
axis lengths. The useful fragment is often near the end of the error message:

```text
Error while processing rearrange-reduction pattern "...".
Input tensor shape: (...). Additional info: {...}.
Shape mismatch, can't divide axis of length ...
```

Use that context to decide whether to fix rank, axis spelling, factor sizes, or
operation choice. See [`troubleshooting.md`](troubleshooting.md) for recovery
playbooks.

## Source evidence distilled

This reference distills public facts from `README.md`, `einops/einops.py`,
`einops/parsing.py`, `einops/tests/test_ops.py`, `einops/tests/test_examples.py`,
`einops/tests/test_other.py`, and tutorial notebook headings/examples. It does
not require future agents to open those source files.
