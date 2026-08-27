# Workflows: Named Einsum And Packing

These recipes show how to use `einops.einsum`, `einops.pack`, and
`einops.unpack` in model-style flows. They are written as small patterns future
agents can adapt after `einops` is installed.

## 1. Convert Attention Scores From NumPy Einsum

Original compact formula:

```python
# q: (batch, query, head, channel)
# k: (batch, key,   head, channel)
np_scores = np.einsum("bqhc,bkhc->bhqk", q, k)
```

Named einops formula:

```python
from einops import einsum

scores = einsum(
    q,
    k,
    "batch query head channel, batch key head channel -> batch head query key",
)
```

Conversion checklist:

1. Keep the tensors in operand order.
2. Move the einsum pattern to the last positional argument.
3. Expand one-letter axes into semantic names.
4. Keep the same comma count and `->` output structure.
5. On a deterministic small array, compare with the original backend formula.

Unsupported grouped-axis repair:

```python
# Not supported inside einops.einsum:
# einsum(q, "batch (head channel) -> batch head channel")
```

If the compact formula assumes a grouped dimension, split or combine that axis
with a separate reshape/rearrange step first, then call `einsum` on simple named
axes. Route the standalone reshape recipe to `tensor-operations`.

## 2. Dot Product And Linear Projection

Use named axes to make matrix orientation explicit:

```python
# x: (batch, in_dim)
# w: (in_dim, out_dim)
y = einsum(x, w, "batch in_dim, in_dim out_dim -> batch out_dim")
```

For unknown leading batch shape, use ellipsis:

```python
# data: (..., in_dim)
# weights: (out_dim, in_dim)
y = einsum(weights, data, "out_dim in_dim, ... in_dim -> ... out_dim")
```

If a user needs bias addition, broadcasting, activation, or layer wrappers, keep
those outside this sub-skill unless the failure is specifically in the einsum
formula.

## 3. Trace, Diagonal, And Repeated Axes

A repeated axis inside one input term selects matching diagonal positions:

```python
trace = einsum(matrix, "row row ->")
```

Keep the repeated axis in the output to preserve diagonal values:

```python
# x: (token, batch, channel, token)
diagonal = einsum(x, "token batch channel token -> token batch channel")
```

Ellipsis works with repeated axes:

```python
# x: (token, ..., token)
middle = einsum(x, "token ... token -> ...")
```

Use this only for genuine diagonal/contraction semantics. If repeated names are
an accidental duplicate in a packing pattern or on the `einsum` output side,
fix the pattern instead.

## 4. ViT Class Token Packing

Use `pack` when a class token has fewer axes than patch tokens but both should
be processed as one token sequence.

```python
from einops import pack, unpack

# class_token_bc: (batch, channel)
# patch_tokens_bhwc: (batch, height, width, channel)
packed, ps = pack([class_token_bc, patch_tokens_bhwc], "batch * channel")

# transformer accepts (batch, tokens, channel) and may change channel size.
processed = transformer(packed)

class_out, patch_out = unpack(processed, ps, "batch * channel_out")
```

Expected bookkeeping:

- `ps[0] == ()` for the class token: one token with no explicit packed axis.
- `ps[1] == (height, width)` for the patch grid.
- `patch_out` recovers `(batch, height, width, channel_out)`.
- `class_out` recovers `(batch, channel_out)` without manual squeeze.

## 5. Multimodal Packing, Including Zero-Length Modalities

The same pattern supports heterogeneous token sources:

```python
all_inputs = [class_token_bc, image_tokens_bhwc, text_tokens_btc]
packed, ps = pack(all_inputs, "batch * channel")
processed = transformer(packed)
class_out, image_out, text_out = unpack(processed, ps, "batch * channel_out")
```

Zero-length modalities require no special branch:

```python
# text_tokens_btc has shape (batch, 0, channel)
packed, ps = pack([class_token_bc, image_tokens_bhwc, text_tokens_btc], "batch * channel")
# ps contains (), (height, width), and (0,)
class_out, image_out, text_out = unpack(processed, ps, "batch * channel_out")
assert text_out.shape[1] == 0
```

Do not drop zero-length entries from `ps`; doing so changes the output count and
breaks the caller's modality alignment.

## 6. Multi-Output Prediction Splitting

When one model head packs several logical outputs along one feature axis, use
manual `packed_shapes` to split it declaratively.

```python
# model_output: (batch, height, width, packed_features)
confidence, bbox_x, bbox_y, bbox_w, bbox_h, mask_logits, class_logits = unpack(
    model_output,
    [[], [], [], [], [], [mask_h, mask_w], [num_classes]],
    "batch height width *",
)
```

Shape results:

- `[]` / `()` outputs have shape `(batch, height, width)`.
- `[mask_h, mask_w]` outputs have shape `(batch, height, width, mask_h, mask_w)`.
- `[num_classes]` outputs have shape `(batch, height, width, num_classes)`.

Use this when the packed feature layout is part of the model contract. If the
layout is learned or dynamic, record the manual `packed_shapes` next to the
model configuration and validate it against a small known output.

## 7. Auto-Batching Single Examples And Batches

`pack([x], "* height width channel")` can normalize both a single image and a
batch of images to a batch-first representation.

```python
from einops import pack, unpack


def image_classifier(images_bhwc):
    # Example only: a real model would accept (batch, height, width, channel).
    return images_bhwc.mean(axis=(1, 2))


def universal_predict(x):
    # x may be (height, width, channel) or (batch, height, width, channel)
    images_bhwc, ps = pack([x], "* height width channel")
    predictions_bcls = image_classifier(images_bhwc)
    [predictions] = unpack(predictions_bcls, ps, "* cls")
    return predictions
```

If `x` is a single image, `ps == [()]` and the result is `(cls,)`. If `x` is a
batch, `ps == [(batch,)]` and the result is `(batch, cls)`.

## 8. Round-Trip Validation For Dynamic Packing

Use a local assertion when the pattern or input list is computed dynamically:

```python
from einops import pack, unpack
import numpy as np


def assert_pack_roundtrip(inputs, pattern):
    packed, ps = pack(inputs, pattern)
    recovered = unpack(packed, ps, pattern)
    assert len(recovered) == len(inputs)
    for original, restored in zip(inputs, recovered):
        assert original.shape == restored.shape
        np.testing.assert_allclose(restored, original)
    return packed, ps
```

For manual `packed_shapes`, validate the packed-axis length explicitly:

```python
import math


def product(shape):
    return math.prod(shape) if len(shape) else 1

known = [[], [mask_h, mask_w], [num_classes]]
expected_width = sum(product(shape) for shape in known)
assert model_output.shape[-1] == expected_width
```

When using one `-1`, verify the inferred output shape immediately after
`unpack`, especially if any known part can be zero.

## 9. Choosing Between `einsum` And `pack`

Use `einsum` when the operation multiplies and sums/reorders axes according to
Einstein notation. Use `pack`/`unpack` when the operation preserves values and
only records how heterogeneous shapes were flattened and concatenated.

A common combined flow is:

```python
packed, ps = pack([class_token, image_tokens, text_tokens], "batch * channel")
attended = transformer(packed)
# Optional named contraction on the packed sequence:
scores = einsum(attended, attended, "batch token channel, batch key channel -> batch token key")
outputs = unpack(attended, ps, "batch * channel_out")
```

Keep the `ps` tied to the tensor whose packed axis has the same segmentation;
if filtering, sorting, or pooling changes the packed axis length/order, old
`ps` is no longer valid.
