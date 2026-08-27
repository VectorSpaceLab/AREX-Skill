# Parametric UMAP API Reference

This reference covers the optional TensorFlow/Keras-backed `ParametricUMAP`
API in `umap-learn` 0.5.12. The minimum verified inspection environment did
not install TensorFlow, Keras, Torch, or torchvision, so treat neural execution
as optional until the target environment passes the bundled stack check.

## Imports and Optional Dependencies

Install the optional extra when Parametric UMAP is required:

```bash
pip install "umap-learn[parametric_umap]"
```

Package metadata declares `tensorflow >= 2.1` for the `parametric_umap` extra.
The source also imports top-level `keras` and `keras.ops`, so a compatible
Keras installation must be importable. In environments without TensorFlow:

- `from umap import ParametricUMAP` may succeed because `umap.__init__` installs
  a dummy class.
- Constructing that dummy class raises `ImportError: umap.parametric_umap
  requires Tensorflow >= 2.0`.
- `from umap.parametric_umap import ParametricUMAP` raises during import when
  TensorFlow or Keras is missing.

The `to_ONNX()` path imports `torch`, `torch.nn`, `torch.onnx`, and
`torchvision`. Those packages are not part of the `parametric_umap` extra and
are optional for ONNX export only.

## Constructor

Verified source signature:

```python
ParametricUMAP(
    batch_size=None,
    dims=None,
    encoder=None,
    decoder=None,
    parametric_reconstruction=False,
    parametric_reconstruction_loss_fcn=None,
    parametric_reconstruction_loss_weight=1.0,
    autoencoder_loss=False,
    reconstruction_validation=None,
    global_correlation_loss_weight=0,
    landmark_loss_fn=None,
    landmark_loss_weight=1.0,
    keras_fit_kwargs={},
    **kwargs,
)
```

`ParametricUMAP` subclasses `umap.UMAP`, so `**kwargs` are forwarded to the base
UMAP constructor. Use base UMAP parameters such as `n_neighbors`,
`n_components`, `metric`, `n_epochs`, `min_dist`, `random_state`, `verbose`, and
`target_*` here. Do not pass arbitrary neural-only keys through `**kwargs`
unless the installed version documents them; in 0.5.12 the source sets
`n_training_epochs` and `loss_report_frequency` as attributes after the base
constructor, not as explicit constructor parameters.

Important constructor and attribute notes:

| Parameter or attribute | Meaning and constraints |
| --- | --- |
| `batch_size` | Edge-batch size for neural training and default inference batch size. `None` lets the source choose a default from the edge dataset. |
| `dims` | Shape expected by the neural network, for example `(784,)` for flattened vectors or `(28, 28, 1)` for image convnets. If `dims` has more than one dimension, fit reshapes flat input to `[n_samples] + list(dims)`. |
| `encoder` | Keras model that maps input data to `n_components`. If provided, its output width must equal `n_components`; otherwise construction raises `ValueError`. |
| `decoder` | Keras model that maps embedding coordinates back to the data shape. Required for custom parametric reconstruction; a default dense decoder is created when `parametric_reconstruction=True` and `decoder is None`. |
| `parametric_reconstruction` | If `True`, the model trains a decoder and `inverse_transform` calls `decoder.predict`. If `False`, `inverse_transform` falls back to the base UMAP inverse path. |
| `parametric_reconstruction_loss_fcn` | Optional Keras loss for reconstruction. Source default is `keras.losses.BinaryCrossentropy(from_logits=True)` inside `UMAPModel`. |
| `parametric_reconstruction_loss_weight` | Weight for reconstruction loss relative to UMAP loss. |
| `autoencoder_loss` | If `False`, reconstruction loss is stopped before reaching the encoder. If `True`, reconstruction loss also trains the encoder. |
| `reconstruction_validation` | Held-out data used as Keras validation data for reconstruction; it is reshaped according to `dims` when needed. |
| `global_correlation_loss_weight` | Adds global pairwise-correlation loss when greater than zero. This is an advanced neural objective; expect additional training cost. |
| `landmark_loss_fn` | Callable loss used for landmark retraining. Default source function computes safe Euclidean distance and avoids NaN gradients at exact matches. |
| `landmark_loss_weight` | Weight for landmark loss relative to UMAP loss. Can be changed between fits or through `add_landmarks`. |
| `keras_fit_kwargs` | Dictionary forwarded to `parametric_model.fit`, commonly for `callbacks`. Avoid reusing a mutable dictionary across unrelated models. |
| `n_training_epochs` | Source default attribute is `1`. It controls how many passes over the UMAP graph to train, independent of base `n_epochs`. In 0.5.12 safest pattern is `model.n_training_epochs = k` after construction if constructor passing is rejected. |
| `loss_report_frequency` | Source default attribute is `10`; Keras `epochs` becomes `loss_report_frequency * n_training_epochs`. |
| `optimizer` | Source default attribute is `keras.optimizers.Adam(1e-3, clipvalue=4.0)`. Advanced users may replace it before fitting. |
| `_history` | Dictionary of Keras history lists created after the first fit and extended on subsequent fits. Common keys include `loss` plus objective-specific losses. |

## Methods

Verified source method signatures:

```python
fit(X, y=None, precomputed_distances=None, landmark_positions=None)
fit_transform(X, y=None, precomputed_distances=None, landmark_positions=None)
transform(X, batch_size=None)
inverse_transform(X)
save(save_location, verbose=True, exclude_raw_data=False)
add_landmarks(
    X,
    sample_pct=0.01,
    sample_mode="uniform",
    landmark_loss_weight=0.01,
    idx=None,
    reset_optimizer=True,
)
remove_landmarks()
to_ONNX(save_location)
load_ParametricUMAP(save_location, verbose=True)
```

### `fit` and `fit_transform`

`fit`/`fit_transform` accept the same high-level idea as base UMAP, but have
neural-specific extensions:

- `X`: training data. It is used to build the UMAP graph and train the encoder.
- `y`: optional supervised labels forwarded through the base UMAP path.
- `precomputed_distances`: required when `metric="precomputed"`; unlike base
  UMAP, `X` is still required because the neural network needs data inputs.
- `landmark_positions`: array with shape `(n_samples, n_components)`. Use
  `np.nan` rows for samples without fixed landmark targets.

If `prev_epoch_X` has been set by `add_landmarks` and no explicit
`landmark_positions` are provided, the source concatenates new `X` with the
stored landmark samples and builds a landmark-position matrix from the model's
current transform of those stored samples.

### `transform`

`transform(X, batch_size=None)` calls `encoder.predict(np.asanyarray(X), ...)`
and returns shape `(n_samples, n_components)`. It does not rebuild a nearest
neighbour graph. Use the same feature scaling and shape convention as training.

### `inverse_transform`

If `parametric_reconstruction=True`, `inverse_transform(Z)` calls the decoder
and should return the decoder's data-space output. If reconstruction is disabled,
it falls back to base UMAP inverse transform, which has different assumptions
and may not be the desired neural inverse.

### `save` and `load_ParametricUMAP`

`save(save_location, ...)` writes Keras model files for available networks plus
`model.pkl` in the target directory. The source expects the directory to exist
or be creatable by the caller's filesystem context; create it before saving.

Expected save files in 0.5.12:

- `encoder.keras` when `encoder` exists.
- `decoder.keras` when `decoder` exists.
- `parametric_model.keras` when the compiled full model exists.
- `model.pkl` for the pickleable UMAP state.

`load_ParametricUMAP(save_location, verbose=True)` reads `model.pkl`, then tries
to load `encoder.keras`, `decoder.keras`, and a full-model path. Verify loaded
models in your installed version, because the source save name
`parametric_model.keras` and load probe `parametric_model` are version-sensitive.
At minimum, check that `loaded.transform(X).shape == (len(X), n_components)`.

### `add_landmarks` and `remove_landmarks`

`add_landmarks(X, ...)` samples old data to hold the embedding space stable in a
future fit. It stores `prev_epoch_X` and updates `landmark_loss_weight` on the
compiled parametric model. Supported sampling modes in source behavior:

- `sample_mode="uniform"`: sample `int(X.shape[0] * sample_pct)` rows randomly.
- `sample_mode="predetermined"`: use explicit `idx`. The docstring says
  "predefined", but the source branch checks the literal string
  `"predetermined"`.

Call `remove_landmarks()` to clear `prev_epoch_X`.

### `to_ONNX`

`to_ONNX(save_location)` builds a fixed four-layer PyTorch `PumapNet`, copies
weights from the Keras encoder, and calls `torch.onnx.export`. Caveats:

- It requires `torch` and `torchvision` imports at module import time.
- It assumes the default dense encoder shape: input width `dims[0]`, three
  hidden dense layers of width 100, and an output layer of width `n_components`.
- Custom convolutional encoders or non-default architectures are not covered by
  this helper.
- It exports the encoder mapping only, not a full UMAP object with graph state,
  decoder, or Keras training loop.

## Default Network Shape

When no custom encoder is supplied, `prepare_networks` creates a Keras
`Sequential` encoder:

```python
Input(shape=dims)
Flatten()
Dense(100, activation="relu")
Dense(100, activation="relu")
Dense(100, activation="relu")
Dense(n_components, name="z")
```

When reconstruction is enabled and no decoder is supplied, the default decoder
is:

```python
Input(shape=(n_components,))
Dense(100, activation="relu")
Dense(100, activation="relu")
Dense(100, activation="relu")
Dense(prod(dims), name="recon", activation=None)
Reshape(dims)
```

Use these shapes as the baseline when designing custom networks or debugging
ONNX export.
