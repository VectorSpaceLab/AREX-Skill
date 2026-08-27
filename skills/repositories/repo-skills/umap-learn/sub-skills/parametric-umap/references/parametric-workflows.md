# Parametric UMAP Workflows

Parametric UMAP replaces direct embedding optimization with a learned Keras
encoder. Use these recipes only after the target environment passes the
parametric stack check. The minimum CPU inspection environment for this skill
did not install TensorFlow/Keras, so the examples below are operating guidance,
not proof that neural training was run during skill construction.

## 1. Basic Parametric Embedding

```python
import numpy as np
from sklearn.datasets import make_moons
from umap.parametric_umap import ParametricUMAP

X, _ = make_moons(n_samples=200, noise=0.05, random_state=42)
X = X.astype("float32")

embedder = ParametricUMAP(
    n_components=2,
    n_neighbors=15,
    min_dist=0.1,
    random_state=42,
    verbose=True,
)
embedding = embedder.fit_transform(X)
assert embedding.shape == (X.shape[0], 2)
assert np.isfinite(embedding).all()
```

Notes:

- `ParametricUMAP` is still a UMAP estimator. Base UMAP options such as
  `n_neighbors`, `min_dist`, `metric`, `n_epochs`, `random_state`, and
  supervised `y` labels are forwarded through `**kwargs`.
- Neural training can be slow on CPU even for correctness-valid use. Start with
  small data and short training settings, then scale deliberately.
- For repeated experiments, set `random_state`; source code passes integer
  random states to `keras.utils.set_random_seed`.
- Training history appears after fit as `embedder._history`. Plotting the curve
  is ordinary matplotlib/plotting work; route plotting-specific questions to
  the plotting sub-skill.

## 2. Custom Encoder With Shape Alignment

Use a custom encoder when tabular dense layers are not enough, for example with
image or sequence-like inputs. The key invariant is that the encoder's final
output width equals `n_components`.

```python
import tensorflow as tf
from umap.parametric_umap import ParametricUMAP

# Flat input rows will be reshaped to (28, 28, 1) inside the fit path.
dims = (28, 28, 1)
n_components = 2

encoder = tf.keras.Sequential(
    [
        tf.keras.layers.Input(shape=dims),
        tf.keras.layers.Conv2D(32, 3, strides=(2, 2), activation="relu", padding="same"),
        tf.keras.layers.Conv2D(64, 3, strides=(2, 2), activation="relu", padding="same"),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(256, activation="relu"),
        tf.keras.layers.Dense(n_components, name="z"),
    ]
)

embedder = ParametricUMAP(
    encoder=encoder,
    dims=dims,
    n_components=n_components,
    random_state=42,
)
embedding = embedder.fit_transform(X_flat_float32)
```

Checklist:

- `X_flat_float32.shape[1] == prod(dims)` when you pass flattened data and
  `dims` has multiple dimensions.
- `encoder.outputs[0].shape[-1] == n_components`; source construction raises a
  `ValueError` if it does not.
- Keep preprocessing identical between `fit` and `transform`.
- Do not use notebook-specific CUDA environment variables or dataset downloads
  as defaults in production helpers.

## 3. Reconstruction and Parametric `inverse_transform`

Enable reconstruction when you need the embedding-to-data-space neural decoder.
With `parametric_reconstruction=True`, `inverse_transform` uses the decoder.

```python
import numpy as np
import tensorflow as tf
from umap.parametric_umap import ParametricUMAP

dims = (2,)
n_components = 2

encoder = tf.keras.Sequential(
    [
        tf.keras.layers.Input(shape=dims),
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(100, activation="relu"),
        tf.keras.layers.Dense(100, activation="relu"),
        tf.keras.layers.Dense(n_components, name="z"),
    ]
)

decoder = tf.keras.Sequential(
    [
        tf.keras.layers.Input(shape=(n_components,)),
        tf.keras.layers.Dense(100, activation="relu"),
        tf.keras.layers.Dense(100, activation="relu"),
        tf.keras.layers.Dense(int(np.prod(dims)), name="recon", activation=None),
        tf.keras.layers.Reshape(dims),
    ]
)

embedder = ParametricUMAP(
    encoder=encoder,
    decoder=decoder,
    dims=dims,
    n_components=n_components,
    parametric_reconstruction=True,
    reconstruction_validation=X_valid.astype("float32"),
    verbose=True,
)
Z = embedder.fit_transform(X_train.astype("float32"))
X_recon = embedder.inverse_transform(Z[:5])
assert X_recon.shape[1:] == dims
```

Reconstruction notes:

- The source warns when reconstruction data are outside `[0, 1]` while using
  the default binary cross-entropy reconstruction loss. Scale image-like data
  accordingly or choose a loss that matches the data domain.
- `autoencoder_loss=False` means decoder reconstruction loss is stopped before
  updating the encoder. Set `autoencoder_loss=True` to train encoder and decoder
  jointly on reconstruction plus UMAP loss.
- `reconstruction_validation` should use the same data shape and scaling as
  training data.

## 4. Keras Callbacks and Training Epochs

Keras callbacks are passed through `keras_fit_kwargs` to `parametric_model.fit`.
Use them for early stopping, TensorBoard-style callbacks, or custom monitoring.

```python
import tensorflow as tf
from umap.parametric_umap import ParametricUMAP

callbacks = [
    tf.keras.callbacks.EarlyStopping(
        monitor="loss",
        min_delta=1e-2,
        patience=5,
        verbose=1,
    )
]

embedder = ParametricUMAP(
    random_state=42,
    verbose=True,
    keras_fit_kwargs={"callbacks": callbacks},
)

# In 0.5.12 the source initializes this attribute after construction.
embedder.n_training_epochs = 5
embedding = embedder.fit_transform(X)
print(embedder._history.keys())
```

Training controls:

- Base `n_epochs` controls how many times graph edges are trained within a
  Parametric UMAP epoch.
- `n_training_epochs` controls how many passes over the graph the neural model
  trains.
- `loss_report_frequency` subdivides reporting; Keras epochs become
  `loss_report_frequency * n_training_epochs`.
- A callback that monitors `loss` is the safest cross-version default because
  the base loss is always present after fitting.

## 5. Save, Load, and Continue Using a Model

Do not rely on plain pickle for a trained Parametric UMAP object. Use the
source-provided save/load helpers so Keras objects are saved alongside the UMAP
state.

```python
from pathlib import Path
from umap.parametric_umap import ParametricUMAP, load_ParametricUMAP

save_dir = Path("pumap-model")
save_dir.mkdir(parents=True, exist_ok=True)

embedder = ParametricUMAP(random_state=42).fit(X_train)
embedder.save(str(save_dir), exclude_raw_data=True)

loaded = load_ParametricUMAP(str(save_dir))
Z_new = loaded.transform(X_new)
assert Z_new.shape[1] == loaded.n_components
```

After loading:

- Validate `transform` on a small trusted batch before replacing a production
  model.
- If reconstruction is required, check that `loaded.decoder` exists and that
  `loaded.inverse_transform(Z_small)` has the expected output shape.
- Save/load filenames are version-sensitive around the full Keras model; verify
  directory contents and behavior in the installed package.

## 6. Landmark Retraining for New Data

Landmarks keep old points near their previous positions when fine-tuning on new
data. This is useful when new categories or new time windows should enter an
existing embedding without rotating or drifting the whole space.

### Automatic landmark sampling

```python
from umap.parametric_umap import ParametricUMAP

p = ParametricUMAP(random_state=42, n_epochs=50)
p.fit(X_old)

# Samples 5% of old rows, stores them in p.prev_epoch_X, and lowers landmark
# loss weight for a gentle constraint.
p.add_landmarks(X_old, sample_pct=0.05, landmark_loss_weight=0.01)
p.fit(X_new)
Z_new = p.transform(X_new)

# Clear landmark state if later fits should not append old landmark samples.
p.remove_landmarks()
```

### Explicit landmark positions

```python
import numpy as np

landmark_positions = np.full((X_mixed.shape[0], p.n_components), np.nan, dtype="float32")
landmark_positions[known_rows] = known_embedding_positions
p.fit(X_mixed, landmark_positions=landmark_positions)
```

Landmark checks:

- `len(landmark_positions) == len(X)`; source raises `ValueError` otherwise.
- Non-landmarks should have `np.nan` coordinates, not zeros.
- If loss spikes or becomes NaN after adding landmarks, reduce
  `landmark_loss_weight`, reset/rebuild the optimizer through `add_landmarks`,
  and inspect recent `p._history["loss"]` values.
- Source accepts `sample_mode="uniform"` and a literal
  `sample_mode="predetermined"` with `idx`; the docstring wording differs.

## 7. Precomputed Distances With Neural Inputs

Parametric UMAP can use `metric="precomputed"`, but the neural network still
needs real `X` values for training. Pass the distance matrix separately:

```python
from sklearn.metrics import pairwise_distances
from umap.parametric_umap import ParametricUMAP

D = pairwise_distances(X_train)
p = ParametricUMAP(metric="precomputed", random_state=42)
Z = p.fit_transform(X_train, precomputed_distances=D)
```

If `metric="precomputed"` and `precomputed_distances` is missing, the source
raises `ValueError`. Base UMAP precomputed-distance transform caveats still
apply; for general non-parametric handling route to the core embedding
sub-skill.

## 8. ONNX Export Caveat

`to_ONNX(save_location)` is a narrow encoder-export helper. Use it only when all
of these are true:

- `torch`, `torch.onnx`, and `torchvision` are importable.
- The trained encoder matches the default dense shape closely enough for the
  fixed PyTorch `PumapNet` weight copier.
- You need only the encoder mapping, not the full UMAP graph state, decoder, or
  retraining loop.

```python
p.to_ONNX("pumap_encoder.onnx")
```

For custom convolutional or non-default encoders, prefer framework-native export
from Keras/TensorFlow or write a bespoke conversion test instead of assuming
`to_ONNX` covers the architecture.

## 9. Tiny Smoke Testing Policy

The bundled script does not train by default. When TensorFlow/Keras are present,
run an explicit tiny smoke only when acceptable:

```bash
python scripts/check_parametric_stack.py --tiny-smoke --json
```

The smoke is designed for import and shape sanity, not benchmark quality. It
uses a tiny local dataset, avoids downloads, and should be skipped when optional
neural dependencies are absent.
