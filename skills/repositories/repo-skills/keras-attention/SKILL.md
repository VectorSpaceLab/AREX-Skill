---
name: keras-attention
description: "Guides use of the Keras Attention Layer attention package for
  TensorFlow/Keras sequence models, save/load checks, debug-mode attention
  weights, and example workflow troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Keras Attention Layer

Use this repo skill when a task involves the `attention` Python package, the
Keras Attention Layer project, `from attention import Attention`, Luong or
Bahdanau score functions in TensorFlow/Keras sequence models, attention-weight
visualization with `KERAS_ATTENTION_DEBUG`, or troubleshooting the package's
example workflows.

The package surface is small and the skill is intentionally root-only: all
runtime guidance is in this skill directory, with detailed API, examples,
compatibility, and troubleshooting notes in bundled references.

## Quick routing

| User need | Read or run |
| --- | --- |
| Install and smoke-test the package | Start here, then run `scripts/smoke_attention.py`. |
| Add an attention layer after an RNN/LSTM/GRU | Read `references/api-reference.md`. |
| Choose `score="luong"` vs `score="bahdanau"` or set `units` | Read `references/api-reference.md`. |
| Save and reload a model that contains `Attention` | Read `references/api-reference.md` and run `scripts/smoke_attention.py --save-format h5`. |
| Enable/debug attention weights or adapt the visualization demos | Read `references/examples.md` and `references/troubleshooting.md`; run `scripts/check_example_dependencies.py`. |
| Decide whether a TensorFlow/Keras/Python version is compatible | Read `references/compatibility.md`. |
| Diagnose install/import, Keras, Graphviz, dataset, or GPU-warning issues | Read `references/troubleshooting.md`. |
| Check whether this skill is stale for a checkout | Read `references/repo-provenance.md`. |

## Minimal package contract

Install from PyPI when using the public package:

```bash
python -m pip install attention
```

Then verify the import:

```python
from attention import Attention
```

The core layer pattern is:

```python
from tensorflow.keras import Input
from tensorflow.keras.layers import Dense, LSTM
from tensorflow.keras.models import Model
from attention import Attention

model_input = Input(shape=(time_steps, input_dim))
x = LSTM(64, return_sequences=True)(model_input)
x = Attention(units=32, score="luong")(x)  # or score="bahdanau"
x = Dense(output_dim)(x)
model = Model(model_input, x)
```

Important facts to preserve when helping users:

- Distribution name: `attention`; import module: `attention`; public class:
  `Attention`.
- `Attention(units=128, score="luong", **kwargs)` expects a 3D sequence tensor
  `(batch_size, timesteps, input_dim)` and returns `(batch_size, units)`.
- Valid score functions are exactly `"luong"` and `"bahdanau"`; other values
  raise `ValueError`.
- Put `return_sequences=True` on the preceding recurrent layer so `Attention`
  receives all timesteps, not only the final state.
- When loading a saved model, pass `custom_objects={"Attention": Attention}`.
- Set `KERAS_ATTENTION_DEBUG=1` before importing `attention` only when you need
  intermediate attention tensors; debug mode changes `Attention` so it is no
  longer a normal Keras `Layer`.

## Bundled scripts

Run these scripts from the generated skill directory or address them by path
from another working directory. They do not read the original repository
checkout.

```bash
python scripts/smoke_attention.py --score both --save-format h5 --force-cpu
```

`smoke_attention.py` builds tiny Luong and Bahdanau models, checks prediction
shapes, verifies `get_config()`, and optionally save/loads the model with the
proper `custom_objects` mapping. Use it after installing the package or when a
TensorFlow/Keras upgrade may have changed behavior.

```bash
python scripts/check_example_dependencies.py
```

`check_example_dependencies.py` verifies optional packages and the Graphviz
`dot` executable needed by the visualization-oriented examples; it does not run
long training or download datasets.

## Boundaries and safety

- This is a package-use skill, not a maintainer workflow. For editing lint,
  release, or CI configuration, use a repository-maintenance workflow instead.
- The package has no public CLI and no dataset/config schema beyond ordinary
  TensorFlow/Keras tensors.
- The basic bundled smoke is safe and CPU-capable. The IMDB and visualization
  demos are long-running, may download data or write plots, and should not be
  treated as default smoke tests.
- Do not point users back to source-checkout examples or scripts. Use the
  bundled references and scripts here as the self-contained operating context.
