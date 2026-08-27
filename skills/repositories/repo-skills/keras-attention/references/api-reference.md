# Attention API reference

## Public import surface

```python
from attention import Attention
```

The package exports `Attention` from the `attention` module and has no public
CLI entry points. The public constructor verified for package version 5.0.0 is:

```python
Attention(units: int = 128, score: str = "luong", **kwargs)
```

`Attention` subclasses `tensorflow.keras.layers.Layer` in normal mode and can be
used inside Functional or Sequential Keras models as long as the previous layer
returns a full sequence.

## Parameters

| Parameter | Meaning | Practical guidance |
| --- | --- | --- |
| `units` | Output dimensionality of the attention vector `a_t`. | Choose the feature width expected by downstream dense/classification/regression layers. Default is `128`. |
| `score` | Attention score function. | Use exactly `"luong"` or `"bahdanau"`. Invalid values raise `ValueError: Possible values for score are: [luong] and [bahdanau].` |
| `**kwargs` | Standard Keras layer keyword arguments. | Names, dtype, and trainability are passed through when debug mode is off. |

Class constants exposed by the implementation:

```python
Attention.SCORE_LUONG == "luong"
Attention.SCORE_BAHDANAU == "bahdanau"
```

## Input and output contract

`Attention` expects a 3D tensor:

```text
(batch_size, timesteps, input_dim)
```

The usual producer is a recurrent layer with `return_sequences=True`:

```python
x = LSTM(64, return_sequences=True)(model_input)
x = Attention(units=32, score="luong")(x)
```

The layer returns a 2D tensor:

```text
(batch_size, units)
```

A tiny model usually follows the attention layer with `Dense(...)`, dropout, or
other task-specific heads. If the preceding RNN does not return sequences,
`Attention` receives a 2D tensor and cannot compute per-timestep weights.

## Score-function behavior

Both score functions use the final timestep hidden state `h_t` against the full
hidden-state sequence `h_s` and then combine the context vector with `h_t`.

### Luong

`score="luong"` uses multiplicative-style scoring:

1. Project the hidden-state sequence with a bias-free dense layer named
   `luong_w`.
2. Dot the final hidden state against the projected sequence with a layer named
   `attention_score`.
3. Softmax the scores with a layer named `attention_weight`.
4. Dot the attention weights with the original hidden-state sequence to produce
   `context_vector`.
5. Concatenate context and final state, then project through a bias-free tanh
   dense layer named `attention_vector`.

### Bahdanau

`score="bahdanau"` uses additive-style scoring:

1. Project the final state and each sequence state through separate bias-free
   dense layers.
2. Repeat the final-state projection across timesteps.
3. Add the projections, apply tanh, and project to a scalar score per timestep.
4. Squeeze the trailing singleton score dimension.
5. Softmax with `attention_weight`, compute `context_vector`, concatenate with
   `h_t`, and project through `attention_vector`.

Use Luong as the compact default. Use Bahdanau when a user explicitly wants the
additive formulation from the original sequence-to-sequence attention family or
is matching the repository's delimiter-sum visualization demo.

## Serialization and `get_config()`

The layer implements `get_config()` and preserves `units` and `score`, for
example:

```python
layer = Attention(units=4, score="bahdanau")
config = layer.get_config()
assert config["units"] == 4
assert config["score"] == "bahdanau"
```

When reloading a saved model, register the custom layer:

```python
from tensorflow.keras.models import load_model
from attention import Attention

model = load_model("model.h5", custom_objects={"Attention": Attention})
```

The upstream example uses HDF5 (`.h5`) save/load. Newer Keras versions may warn
that HDF5 is legacy; the warning is not itself a failure. The native `.keras`
format can be used for new projects, but keep the `custom_objects` habit unless
the layer has been explicitly registered in the user's codebase.

## Debug mode and attention weights

Debug mode is controlled at import time:

```bash
KERAS_ATTENTION_DEBUG=1 python your_script.py
```

or in Python before importing `attention`:

```python
import os
os.environ["KERAS_ATTENTION_DEBUG"] = "1"
from attention import Attention
```

In debug mode, `Attention` is no longer a normal Keras `Layer`; it subclasses
`object` so that internal tensors/layers can be inspected. Consequences:

- Set the environment variable before the first `attention` import. Restart the
  Python process or notebook kernel after changing it.
- Do not expect Sequential-model insertion to behave like normal mode. Use the
  Functional API or direct calls for debug experiments.
- The softmax layer that contains attention weights is named
  `attention_weight`, which is the name the repository's visualization demos
  inspect with `keract`.
- Debug mode is for visualization/introspection, not for ordinary training or
  production inference.

A direct debug-mode smoke call should return `(batch, units)`:

```python
import tensorflow as tf
from attention import Attention

layer = Attention(units=5, score="luong")
out = layer(tf.ones((2, 3, 4)))
assert tuple(out.shape) == (2, 5)
```

## Safe validation

Use the bundled script when validating an install or a TensorFlow/Keras version:

```bash
python scripts/smoke_attention.py --score both --save-format h5 --force-cpu
```

That script is a tiny, self-contained replacement for the safe parts of the
basic package example: it builds both score variants, checks output shapes,
checks config serialization, and round-trips a saved model with
`custom_objects`.
