# Parametric UMAP Troubleshooting

Use this playbook for optional TensorFlow/Keras Parametric UMAP failures. Start
with the bundled stack checker; it avoids training and explains which optional
components are missing.

```bash
python scripts/check_parametric_stack.py --json
```

## Missing TensorFlow or Keras

Symptoms:

- `from umap.parametric_umap import ParametricUMAP` raises an import error.
- `from umap import ParametricUMAP` succeeds, but `ParametricUMAP()` raises
  `ImportError: umap.parametric_umap requires Tensorflow >= 2.0`.
- A warning says TensorFlow, Tensorflow, or Keras is required.

Cause:

- Parametric UMAP is optional. The base `umap-learn` package does not require
  TensorFlow/Keras.
- The root package installs a dummy `ParametricUMAP` class when direct import of
  `umap.parametric_umap` fails.
- Source code imports both `tensorflow` and top-level `keras`/`keras.ops`.

Recovery:

1. Confirm the target Python environment, not just a notebook kernel, passes:

   ```bash
   python scripts/check_parametric_stack.py --json
   ```

2. Install optional dependencies in that same environment:

   ```bash
   pip install "umap-learn[parametric_umap]"
   ```

3. If TensorFlow is already installed but direct import still fails, check Keras
   separately (`python -c "import keras; from keras import ops"`). Use a
   TensorFlow/Keras combination compatible with your Python version.
4. Import the real class directly for neural workflows:

   ```python
   from umap.parametric_umap import ParametricUMAP
   ```

5. Treat CPU TensorFlow as valid for correctness checks. Do not block on CUDA
   unless the user explicitly requires GPU throughput.

## Dummy `ParametricUMAP` From Root Import

Symptom:

```python
from umap import ParametricUMAP
ParametricUMAP()
# ImportError: umap.parametric_umap requires Tensorflow >= 2.0
```

Explanation:

- `umap.__init__` catches the missing optional dependency and exposes a dummy
  class so the package import can still complete.
- The dummy is not trainable; it exists only to raise an actionable error.

Recovery:

- Run the stack checker and install `umap-learn[parametric_umap]` plus a
  compatible Keras import.
- After installation, confirm `ParametricUMAP.__module__` is
  `umap.parametric_umap`, not `umap`.

## Encoder Output Does Not Match `n_components`

Symptom:

- Construction raises a `ValueError` like "Dimensionality of embedder network
  output ... does not match n_components ...".
- `transform` returns the wrong number of columns.

Cause:

- Custom encoder final dense/output layer does not have exactly
  `n_components` units.

Recovery:

```python
n_components = 2
encoder = tf.keras.Sequential([... , tf.keras.layers.Dense(n_components, name="z")])
embedder = ParametricUMAP(encoder=encoder, n_components=n_components, dims=dims)
```

Validation:

```python
assert int(encoder.outputs[0].shape[-1]) == n_components
```

## `dims`, Input Shape, or Reshape Errors

Symptoms:

- Keras complains about incompatible input shape.
- Source reshape fails inside fit.
- A convolutional encoder receives flat vectors or a dense encoder receives
  image tensors unexpectedly.

Causes:

- `dims` does not match each sample's feature shape.
- Flattened data width is not `prod(dims)`.
- Fit and transform use different preprocessing.

Recovery:

- For flat tabular data, use `dims=(n_features,)` or omit `dims` and let source
  infer `[X.shape[-1]]`.
- For image-like convnets, flatten for `fit` only if `prod(dims)` equals the row
  width; the fit path reshapes to `[n_samples] + list(dims)`.
- Apply the same normalization and flatten/reshape convention before
  `transform`.
- In custom smoke tests, assert both embedding and reconstruction shapes.

## Decoder Output or Reconstruction Errors

Symptoms:

- `inverse_transform` has the wrong shape.
- Keras reconstruction loss fails due to shape mismatch.
- Warning: data should be scaled to `[0, 1]` for cross-entropy reconstruction
  loss.

Causes:

- `decoder` output cannot reshape to `dims`.
- `parametric_reconstruction=True` but data scale/loss combination is invalid.
- `reconstruction_validation` shape differs from training data shape.

Recovery:

```python
decoder = tf.keras.Sequential(
    [
        tf.keras.layers.Input(shape=(n_components,)),
        tf.keras.layers.Dense(int(np.prod(dims)), activation=None),
        tf.keras.layers.Reshape(dims),
    ]
)
embedder = ParametricUMAP(
    decoder=decoder,
    dims=dims,
    n_components=n_components,
    parametric_reconstruction=True,
)
```

- Scale image-like data to `[0, 1]` or provide a reconstruction loss matched to
  your data domain.
- Check `X_recon.shape[1:] == dims` after `inverse_transform`.
- If you do not need neural inverse mapping, leave
  `parametric_reconstruction=False` and route base inverse-transform issues to
  the core embedding sub-skill.

## Callback or Training-Control Confusion

Symptoms:

- `ParametricUMAP(n_training_epochs=...)` is rejected by the installed version.
- Early stopping callback does not fire.
- `_history` is missing before fit or does not have the expected key.

Causes:

- In 0.5.12, `n_training_epochs` and `loss_report_frequency` are attributes set
  after construction, not explicit constructor parameters in the verified
  signature.
- Callback monitor name does not match available history keys.

Recovery:

```python
embedder = ParametricUMAP(keras_fit_kwargs={"callbacks": callbacks})
embedder.n_training_epochs = 5
embedder.loss_report_frequency = 10
embedder.fit(X)
print(embedder._history.keys())
```

- Monitor `loss` first; add objective-specific monitors only after inspecting
  `_history.keys()`.
- Remember Keras epochs are `loss_report_frequency * n_training_epochs`.

## Save/Load Directory Problems

Symptoms:

- `FileNotFoundError` when saving `model.pkl` or Keras files.
- Loaded model lacks encoder/decoder or cannot transform.
- Full `parametric_model` does not load even though it was saved.

Causes:

- The save directory was not created by caller code.
- File names or Keras serialization behavior differ across installed versions.
- Custom layers/losses need custom-object handling outside the simple helper.
- Source saves `parametric_model.keras` but load probes a path named
  `parametric_model` in 0.5.12; verify behavior in the installed version.

Recovery:

1. Create the directory first.
2. Use `embedder.save(path, exclude_raw_data=True)` for smaller saved state when
   raw training data are not needed.
3. Load with `load_ParametricUMAP(path)`.
4. Validate on a small batch:

   ```python
   loaded = load_ParametricUMAP(path)
   assert loaded.transform(X_small).shape[1] == loaded.n_components
   if loaded.parametric_reconstruction:
       assert loaded.inverse_transform(loaded.transform(X_small)).shape[0] == len(X_small)
   ```

5. For custom layers or cross-version model migration, prefer explicit
   TensorFlow/Keras save/load tests in the target environment.

## Landmark Retraining, NaN Loss, or Drifting Space

Symptoms:

- Loss spikes or becomes NaN after retraining with new data.
- New fit rotates or drifts the embedding too much.
- `ValueError` says lengths of `X` and `landmark_positions` differ.
- `add_landmarks` rejects a sampling mode.

Causes:

- Landmarks are missing, too heavily weighted, or wrong length.
- Non-landmark rows use zeros instead of `np.nan`, causing false constraints.
- The optimizer state carries momentum across a sharp landmark-loss change.
- Source supports `sample_mode="uniform"` and a branch spelled
  `"predetermined"`; other strings raise.

Recovery:

- Use `add_landmarks(X_old, sample_pct=0.01, landmark_loss_weight=0.01,
  reset_optimizer=True)` before fitting new data.
- For explicit positions, build an array of shape `(len(X), n_components)` and
  fill non-landmarks with `np.nan`.
- Lower `landmark_loss_weight` if UMAP loss is compromised, or increase it if
  old positions drift too much.
- Inspect recent losses:

  ```python
  import numpy as np
  assert not np.any(np.isnan(embedder._history["loss"][-5:]))
  ```

- Call `remove_landmarks()` before unrelated future fits.

## ONNX Export Fails

Symptoms:

- Import warnings mention Torch and ONNX.
- `NameError` or export failure in `to_ONNX`.
- Exported model is invalid for a custom encoder.

Causes:

- `torch`, `torch.onnx`, or `torchvision` is not installed.
- `to_ONNX` uses a fixed PyTorch dense network and weight copier intended for
  the default Parametric UMAP encoder, not arbitrary Keras architectures.
- The helper exports the encoder only.

Recovery:

1. Run:

   ```bash
   python scripts/check_parametric_stack.py --check-onnx --json
   ```

2. Install Torch/torchvision only if ONNX export is required.
3. Use `to_ONNX` only for default dense encoders with `dims[0]` equal to the
   flat input width.
4. For custom convnets, use TensorFlow/Keras-native export or a custom ONNX
   conversion path and verify numerical agreement on a tiny batch.

## Slow CPU Training

Symptoms:

- Fit takes much longer than base UMAP.
- Keras epochs print slowly on CPU.

Cause:

- Parametric UMAP trains a neural network over sampled graph edges. CPU is valid
  for correctness but not a speed guarantee.

Recovery:

- Start with small samples, lower `n_training_epochs`, and tune `batch_size`.
- Use callbacks to stop early.
- Use GPU only when the environment and user requirement justify it; do not
  assume CUDA is required for correctness.

## Optional Native Tests

The package's Parametric UMAP native tests are useful evidence, but they require
TensorFlow/Keras and can be slower than base CPU tests. Preserve them as
optional final verification candidates only when the optional neural stack is
installed.
