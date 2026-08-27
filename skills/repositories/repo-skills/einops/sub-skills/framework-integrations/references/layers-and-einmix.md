# Layers and EinMix

## Purpose

Read this when a user wants `einops` inside neural network modules, serialized
models, framework layers, or the `EinMix` linear/einsum abstraction.

## Layer Families

Common mixin signatures verified from the installed package/source:

```python
Rearrange(pattern: str, **axes_lengths)
Reduce(pattern: str, reduction: str, **axes_lengths)
EinMix(pattern: str, weight_shape: str, bias_shape: str | None = None, **axes_lengths)
```

Framework modules expose these concepts with framework-specific class bases:

| Import | Classes | Notes |
| --- | --- | --- |
| `einops.layers.torch` | `Rearrange`, `Reduce`, `EinMix` | `torch.nn.Module`; torch layers use scriptable torch-specific application for `Rearrange`/`Reduce`. |
| `einops.layers.tensorflow` | `Rearrange`, `Reduce`, `EinMix` | `tf.keras.layers.Layer`; implementation follows TF 2.16-style layer construction. |
| `einops.layers.keras` | `Rearrange`, `Reduce`, `EinMix`, `keras_custom_objects` | Re-exports TensorFlow layer classes plus custom object mapping for model loading. |
| `einops.layers.flax` | `Rearrange`, `Reduce`, `EinMix` | Flax `nn.Module`; constructor uses `sizes={...}` instead of variadic `**axes_lengths`. |
| `einops.layers.paddle` | `Rearrange`, `Reduce`, `EinMix` | Paddle `paddle.nn.Layer`. |
| `einops.layers.oneflow` | `Rearrange`, `Reduce`, `EinMix` | OneFlow `flow.nn.Module`. |

Install the chosen framework separately. Importing a layer module fails if its
framework dependency is absent.

## Choosing Functional API vs Layer API

Use top-level functions in ordinary tensor code:

```python
from einops import rearrange
x = rearrange(x, "b c h w -> b h w c")
```

Use framework layers when the transform belongs inside model construction,
serialization, tracing, or a `Sequential` block:

```python
from torch.nn import Sequential, Linear, ReLU
from einops.layers.torch import Rearrange

model = Sequential(
    Rearrange("batch channel height width -> batch (channel height width)"),
    Linear(16 * 5 * 5, 120),
    ReLU(),
)
```

Use `Reduce` layers for pooling-like operations when the pattern is part of the
model graph:

```python
from einops.layers.torch import Reduce
pool = Reduce("b c (h h2) (w w2) -> b c h w", "max", h2=2, w2=2)
```

## EinMix Operating Model

`EinMix` combines:

- Optional pre-rearrange when the input pattern has composed axes.
- A learned weight tensor described by `weight_shape`.
- Optional bias described by `bias_shape`.
- Optional post-rearrange when the output pattern has composed axes.
- A generated backend `einsum` pattern with single-letter internal identifiers.

Example:

```python
from einops.layers.torch import EinMix

layer = EinMix(
    "time batch channel_in -> time batch channel_out",
    weight_shape="channel_in channel_out",
    bias_shape="channel_out",
    channel_in=128,
    channel_out=256,
)
```

Use `EinMix` when a normal linear layer would require awkward transposes,
manual parameter shapes, or grouped/head-specific connections. Do not use it
just to rename axes; use `Rearrange` or the functional API for that.

## EinMix Constraints From Source

- `pattern` must contain `->` and describes input axes to output axes.
- Every axis in `weight_shape` must have a supplied length in `axes_lengths` or
  framework-specific `sizes`.
- `weight_shape` must be flat: parentheses are not allowed.
- `weight_shape` cannot contain ellipsis.
- Anonymous numeric axes are not allowed in `EinMix` patterns or weight shapes.
- If ellipsis appears in input/output pattern, it must appear on both sides.
- Ellipsis on the left side cannot be parenthesized.
- Output axes must be recognized from input axes or weight axes.
- Weight axes must not be redundant: they should participate in input/output.
- Bias axes must appear in the output and must have supplied sizes.
- Bias dimensions that depend on non-trivial axes must appear after any ellipsis
  in the output, per source validation.

Expected errors are `EinopsError` messages such as:

- `Dimension <axis> of weight should be specified`
- `Parenthesis is not allowed in weight shape`
- `Ellipsis is not supported in weight`
- `Ellipsis in EinMix should be on both sides`
- `Anonymous axes (numbers) are not allowed in EinMix`
- `Bias axes ... not present in output`
- `Axes ... are not used in pattern`

## Torch Script and Compile Notes

- Torch `Rearrange` and `Reduce` layers override the normal mixin application
  and call a torch-specific scriptable recipe application.
- Repository tests cover tracing and scripting of models containing torch
  layers.
- Top-level functions are not designed for `torch.jit.script`, but repository
  evidence says `torch.compile` can work with operations.
- `einops._torch_specific.allow_ops_in_compiled_graph()` registers top-level
  operations with torch dynamo for torch versions where that is needed. The
  module calls it on import when torch backend support is initialized.
- For torch 2.8 and newer, source comments say explicit allow-in-graph is no
  longer needed.

When troubleshooting compilation, first compare the eager model and compiled or
scripted model on a tiny tensor. If eager fails, solve the pattern first in
[`tensor-operations`](../../tensor-operations/SKILL.md).

## Flax Constructor Difference

Flax modules use dataclass-style fields. Examples from source/tests pass sizes
through a dictionary:

```python
from einops.layers.flax import Rearrange, Reduce, EinMix

x = Rearrange("b h w c -> b (w h c)", sizes={"c": 5})(x)
y = Reduce("b hwc -> b", "mean", {"hwc": 30})(x)
z = EinMix("b (h h2) c -> b h out", "h2 c out", "out", sizes={"h2": 2, "c": 4, "out": 8})(x)
```

Other framework layers generally accept `**axes_lengths`.

## Keras Serialization

For Keras model loading, use the provided custom object mapping:

```python
from einops.layers.keras import keras_custom_objects
# tf.keras.models.load_model(path, custom_objects=keras_custom_objects)
```

If serialization fails, verify TensorFlow/Keras version compatibility and that
`get_config()` includes the pattern, reduction/weight/bias fields, and axis
lengths needed to reconstruct the layer.
