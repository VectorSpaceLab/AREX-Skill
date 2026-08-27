# Pattern Recipes for Core Tensor Operations

These recipes are designed for copy/paste use by future agents. They cover the
high-frequency transformations exercised by the public README, tutorials, and
core operation tests.

All examples assume:

```python
import numpy as np
from einops import rearrange, reduce, repeat, parse_shape
```

Replace NumPy arrays with tensors from a supported framework as needed; the same
core patterns apply.

## Naming conventions used here

| Name | Meaning |
| --- | --- |
| `b` | batch |
| `c` | channels/features |
| `h`, `w` | image height/width |
| `t`, `f` | time/frame axes |
| `h2`, `w2`, `p`, `patch` | factor/kernel/patch sizes |
| `...` | rank-polymorphic middle axes |

Prefer semantic names (`frames`, `batch`, `channels`) in production code when
that improves readability.

## Flatten and unflatten

### Flatten every sample

```python
features = rearrange(x, "b c h w -> b (c h w)")
assert features.shape == (x.shape[0], x.shape[1] * x.shape[2] * x.shape[3])
```

For NHWC:

```python
features = rearrange(x, "b h w c -> b (h w c)")
```

### Flatten all axes

```python
flat = rearrange(x, "... -> (...)")
assert flat.size == np.asarray(x).size
```

Right-side parenthesized ellipsis collapses all input axes. Do not put
parenthesized ellipsis on the left side.

### Unflatten with explicit dimensions

```python
x = rearrange(features, "b (c h w) -> b c h w", c=3, h=32, w=32)
```

If the flattened length is not exactly `c * h * w`, einops raises a shape
mismatch. That is a feature: it catches stale comments and wrong assumptions.

### Unflatten using `parse_shape`

Use this when one tensor still has the authoritative shape.

```python
source = np.zeros([2, 3, 5, 7])
flat = np.zeros([2 * 10 * 5 * 7])
shape = parse_shape(source, "b _ h w")
y = rearrange(flat, "(b c h w) -> b c h w", **shape)
assert y.shape == (2, 10, 5, 7)
```

### Split an axis into multiple outputs

Python unpacking can split the first output axis:

```python
x = np.zeros([10, 20, 30, 40])
y1, y2 = rearrange(x, "b (part c) h w -> part b c h w", part=2)
assert y1.shape == y2.shape == (10, 10, 30, 40)
```

## Axis order and C-order composition

Composition order matters. In `(a b)`, the rightmost axis `b` changes fastest.
Use a tiny sentinel check when refactoring unclear code:

```python
x = np.arange(2 * 3).reshape(2, 3)
y = rearrange(x, "a b -> (a b)")
assert y.tolist() == [0, 1, 2, 3, 4, 5]
```

Two common horizontal strips differ:

```python
strip_batch_major = rearrange(images, "b h w c -> h (b w) c")
strip_width_major = rearrange(images, "b h w c -> h (w b) c")
```

Pick the one matching downstream indexing.

## Image and video conventions

### Channels-first ↔ channels-last images

```python
nhwc = rearrange(nchw, "b c h w -> b h w c")
nchw = rearrange(nhwc, "b h w c -> b c h w")
```

Single image without batch:

```python
hwc = rearrange(chw, "c h w -> h w c")
chw = rearrange(hwc, "h w c -> c h w")
```

### Add or remove batch/channel singleton axes

```python
batched = rearrange(image_hwc, "h w c -> () h w c")
image_hwc = rearrange(batched, "() h w c -> h w c")

nchw = rearrange(gray_hw, "h w -> () () h w")
gray_hw = rearrange(nchw, "() () h w -> h w")
```

### Video tensor `(frames, batch, channels, height, width)`

Move to batch-major channels-last video:

```python
video_bfhwc = rearrange(video_fbchw, "frames batch channels height width -> batch frames height width channels")
assert video_bfhwc.shape == (video_fbchw.shape[1], video_fbchw.shape[0], video_fbchw.shape[3], video_fbchw.shape[4], video_fbchw.shape[2])
```

Flatten frames into the batch for a 2D image model:

```python
images = rearrange(video_fbchw, "frames batch channels height width -> (batch frames) channels height width")
restored = rearrange(images, "(batch frames) channels height width -> frames batch channels height width", frames=video_fbchw.shape[0])
```

When restoring, provide either `frames` or `batch`; otherwise einops cannot infer
both factors from `(batch frames)`.

### Shape-polymorphic image/video channels

```python
channels_first = rearrange(x, "batch ... channels -> batch channels ...")
channels_last = rearrange(channels_first, "batch channels ... -> batch ... channels")
```

This works for images, videos, or higher-dimensional spatial tensors because
ellipsis captures the middle axes.

## Pooling and reductions

### Global pooling

```python
avg = reduce(x, "b c h w -> b c", "mean")
mx = reduce(x, "b c h w -> b c", "max")
```

Keep dimensions for broadcasting:

```python
per_image_mean = reduce(x, "b c h w -> b c 1 1", "mean")
centered = x - per_image_mean
```

`1` and `()` are equivalent for singleton output axes:

```python
per_image_mean = reduce(x, "b c h w -> b c () ()", "mean")
```

### 1D, 2D, and 3D pooling with the same notation

```python
pool1d = reduce(x1, "b c (t dt) -> b c t", "max", dt=2)
pool2d = reduce(x2, "b c (h dh) (w dw) -> b c h w", "max", dh=2, dw=2)
pool3d = reduce(x3, "b c (z dz) (y dy) (x dx) -> b c z y x", "max", dz=2, dy=2, dx=2)
```

The input length along each decomposed axis must be divisible by the supplied
factor.

### Average over all middle axes with ellipsis

```python
summary = reduce(x, "batch ... channels -> batch channels", "mean")
```

### Boolean masks

```python
any_valid = reduce(mask, "b h w -> b", "any")
all_valid = reduce(mask, "b h w -> b", "all")
```

### Callable reduction

```python
def numpy_l2_norm(x, axes):
    return np.sqrt(np.sum(x * x, axis=axes))

norm = reduce(x, "b c h w -> b c", numpy_l2_norm)
```

The callable receives a tuple of integer axes to reduce. It should return the
backend tensor with those axes removed.

## Repeat, broadcast, and reduce/repeat interplay

### Add channels to grayscale

```python
rgb = repeat(gray, "h w -> h w c", c=3)
assert rgb.shape[-1] == 3
```

### Add copies on any side

```python
copies_first = repeat(x, "b c -> copies b c", copies=4)
copies_last = repeat(x, "b c -> b c copies", copies=4)
```

### Repeat along existing axes

```python
upsampled = repeat(image, "h w -> (h h2) (w w2)", h2=2, w2=2)
```

Order changes visual behavior:

```python
repeat_pixels = repeat(image, "h w -> h (w r)", r=3)  # each value repeated in-place
repeat_blocks = repeat(image, "h w -> h (r w)", r=3)  # whole axis tiled by block order
```

### Pixelate: reduce then repeat

```python
lowres = reduce(image, "(h h2) (w w2) -> h w", "mean", h2=2, w2=2)
pixelated = repeat(lowres, "h w -> (h h2) (w w2)", h2=2, w2=2)
assert pixelated.shape == image.shape
```

### Verify a repeat operation

```python
x = np.arange(2 * 3 * 5).reshape(2, 3, 5)
y = repeat(x, "a b c -> copies a b c", copies=3)
assert np.array_equal(reduce(y, "copies a b c -> a b c", "min"), x)
assert np.array_equal(reduce(y, "copies a b c -> a b c", "max"), x)
```

## Stack and concatenate list inputs

A Python list of same-shaped tensors is treated as a new leading axis before
pattern interpretation.

### Stack list as batch

```python
images = [np.zeros([30, 40, 3]) for _ in range(32)]
batch = rearrange(images, "b h w c -> b h w c")
assert batch.shape == (32, 30, 40, 3)
```

### Stack list along the last axis

```python
stack_last = rearrange(images, "b h w c -> h w c b")
assert stack_last.shape == (30, 40, 3, 32)
```

### Concatenate vertically or horizontally

```python
vertical = rearrange(images, "b h w c -> (b h) w c")
horizontal = rearrange(images, "b h w c -> h (b w) c")
assert vertical.shape == (32 * 30, 40, 3)
assert horizontal.shape == (30, 32 * 40, 3)
```

Pitfall: all list elements must have compatible backend type and shape. If they
have variable spatial sizes, use the sibling packing route rather than list
`rearrange`.

## Space-depth and patch transforms

### Space-to-depth, NCHW

```python
y = rearrange(x, "b c (h h2) (w w2) -> b (h2 w2 c) h w", h2=2, w2=2)
assert y.shape == (x.shape[0], x.shape[1] * 4, x.shape[2] // 2, x.shape[3] // 2)
```

### Depth-to-space, NCHW

```python
y = rearrange(x, "b (c h2 w2) h w -> b c (h h2) (w w2)", h2=2, w2=2)
```

To invert exactly, keep the same factor order on both sides.

### Space-to-depth, NHWC

```python
y = rearrange(x, "b (h h2) (w w2) c -> b h w (c h2 w2)", h2=2, w2=2)
```

### Depth-to-space, NHWC

```python
y = rearrange(x, "b h w (c h2 w2) -> b (h h2) (w w2) c", h2=2, w2=2)
```

### Patchify images

```python
patches = rearrange(images, "b c (h ph) (w pw) -> b (h w) (c ph pw)", ph=16, pw=16)
```

Unpatchify:

```python
images = rearrange(patches, "b (h w) (c ph pw) -> b c (h ph) (w pw)", h=14, w=14, ph=16, pw=16)
```

At least enough factors must be provided to infer composed axes. If both `h` and
`w` are unknown in `(h w)`, supply one or both explicitly.

### Strided subgrid trick

Split each spatial subgrid into its own batch item, run an operation, then pack
back:

```python
y = rearrange(x, "b c (h hs) (w ws) -> (hs ws b) c h w", hs=2, ws=2)
y = convolve_2d(y)
y = rearrange(y, "(hs ws b) c h w -> b c (h hs) (w ws)", hs=2, ws=2, b=x.shape[0])
```

This pattern is useful when a model only supports a simpler spatial stride but
you want explicit shape semantics.

## Ellipsis recipes

### Identity and rank-polymorphic moves

```python
same = rearrange(x, "... -> ...")
last_to_first = rearrange(x, "... c -> c ...")
first_to_last = rearrange(x, "b ... -> ... b")
```

### Collapse arbitrary tail axes

```python
flat_tail = rearrange(x, "b ... -> b (...)")
```

### Reduce arbitrary middle axes

```python
summary = reduce(x, "b ... c -> b c", "sum")
```

### Repeat while preserving arbitrary middle axes

```python
y = repeat(x, "b ... c -> b ... c copies", copies=2)
```

Use ellipsis when rank may vary; use explicit axis names when rank is part of
the interface you want einops to check.

## Pattern debugging checklist

1. Write down the input shape and label every axis.
2. Mark which axes are preserved, reduced, repeated, or decomposed.
3. For each parenthesized input group, ensure at most one factor is unknown.
4. Supply `axes_lengths` for new `repeat` axes and ambiguous decomposition.
5. Remember C-order: in `(a b c)`, `c` changes fastest.
6. Use a tiny `np.arange(...).reshape(...)` fixture and assert shape plus one
   sentinel value before applying the pattern to model data.

The bundled `scripts/shape_recipe_smoke.py` implements a deterministic set of
these checks.
