---
name: parametric-umap
description: "Use ParametricUMAP for TensorFlow/Keras-backed neural embeddings,
  reconstruction, save/load, callbacks, landmarks, and ONNX caveats."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Parametric UMAP

Use this sub-skill when the task is about the neural `ParametricUMAP` path
rather than the base `umap.UMAP` estimator.

## Route Here For

- Diagnosing missing TensorFlow/Keras support for Parametric UMAP.
- Running learned embeddings with `ParametricUMAP`.
- Supplying custom encoder/decoder networks.
- Enabling reconstruction, `inverse_transform`, or `autoencoder_loss`.
- Saving, loading, or continuing parametric models.
- Adding callbacks, landmarks, or retraining on new data slices.
- Checking ONNX export caveats and optional Torch dependencies.

## Route Elsewhere

- Base UMAP fit/transform/inverse/update workflows: read
  [core-embedding](../core-embedding/SKILL.md).
- Plotting the training history or other UMAP diagnostics: read
  [plotting-diagnostics](../plotting-diagnostics/SKILL.md).
- Supervised, densMAP, or aligned/composed workflows are owned by their
  sibling sub-skills, not this one.

## Start Fast

1. Run [`scripts/check_parametric_stack.py`](scripts/check_parametric_stack.py)
   before training. It reports whether `umap`, TensorFlow, Keras, and the
   optional Torch/torchvision ONNX path are available, and it explains the root
   import shim when TensorFlow is absent.
2. If TensorFlow/Keras are missing, do not expect `from umap import
   ParametricUMAP` to train. In that case the root package may expose a dummy
   class whose constructor raises `ImportError`.
3. Keep custom encoder output units aligned with `n_components`, and keep
   decoder output shape aligned with `dims` when reconstruction is enabled.
4. CPU-only TensorFlow is enough for correctness checks; GPU support is
   optional and only affects speed.

## Quick Pattern

```python
from umap.parametric_umap import ParametricUMAP

model = ParametricUMAP(n_components=2, verbose=True)
embedding = model.fit_transform(X)
```

For a custom network or reconstruction, read the bundled references before
writing code:

- [`references/parametric-workflows.md`](references/parametric-workflows.md)
  for recipes.
- [`references/api-reference.md`](references/api-reference.md) for verified
  signatures and parameter notes.
- [`references/troubleshooting.md`](references/troubleshooting.md) for import,
  shape, save/load, landmark, and ONNX recovery steps.

## Decision Points

- **Need the real class or a dummy shim?** Use the stack check first. If
  TensorFlow is missing, the root import may still expose `ParametricUMAP`, but
  constructing it raises `ImportError`.
- **Need a neural embedding only?** Use the default fully connected encoder.
- **Need a custom architecture?** Supply both `encoder` and, when requested,
  `decoder`; make sure the encoder output width equals `n_components`.
- **Need reconstruction?** Enable `parametric_reconstruction=True`, keep the
  data scale and decoder output compatible with the chosen loss, and use
  `reconstruction_validation` when you want held-out reconstruction checks.
- **Need early stopping or other callbacks?** Pass them through
  `keras_fit_kwargs`.
- **Need to continue from a previous fit on new data?** Use
  `add_landmarks(...)` or pass `landmark_positions` into `fit`/`fit_transform`.
- **Need export rather than training?** `save()` and `load_ParametricUMAP()`
  preserve the Keras objects and pickle state; `to_ONNX()` is an encoder-only
  export path and requires Torch extras.

## Keep in Mind

- `transform(X, batch_size=None)` uses the encoder path directly; provide input
  in the shape the encoder expects.
- `inverse_transform(X)` uses the decoder only when
  `parametric_reconstruction=True`; otherwise it falls back to the base UMAP
  inverse path.
- `_history` accumulates Keras loss values across fits. Use the plotting
  sub-skill if you need to render the curve.
- Save/load behavior is version-sensitive; verify the generated filenames when
  round-tripping a model directory.

## References

- Read [`references/parametric-workflows.md`](references/parametric-workflows.md)
  for end-to-end recipes covering embedding, reconstruction, callbacks,
  save/load, landmarks, and ONNX caveats.
- Read [`references/api-reference.md`](references/api-reference.md) for the
  constructor, method signatures, and shape/parameter constraints.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for the
  concrete failure modes and recovery steps.
- Run [`scripts/check_parametric_stack.py`](scripts/check_parametric_stack.py)
  whenever you need a safe import/dependency summary or a tiny smoke check.
