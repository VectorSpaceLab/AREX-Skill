# Keras Workflows

DeepCTR Keras models are regular `tf.keras.Model` objects built from DeepCTR feature columns. This page gives self-contained patterns that future agents can adapt without reading original examples.

## Imports

Use public TensorFlow Keras imports:

```python
import numpy as np
import tensorflow as tf
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.models import save_model, load_model

from deepctr.feature_column import SparseFeat, DenseFeat, get_feature_names
from deepctr.layers import custom_objects
from deepctr.models import DeepFM, AFM, DCN, xDeepFM, AutoInt
```

Avoid `tensorflow.python.keras` in user-facing code.

## Minimal fixed-length binary CTR workflow

```python
import numpy as np
from deepctr.feature_column import SparseFeat, DenseFeat, get_feature_names
from deepctr.models import DeepFM

linear_feature_columns = [
    SparseFeat("user_id", vocabulary_size=1000, embedding_dim=8),
    SparseFeat("ad_id", vocabulary_size=500, embedding_dim=8),
    DenseFeat("price", 1),
]
dnn_feature_columns = linear_feature_columns
feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)

n = 128
model_input = {
    "user_id": np.random.randint(0, 1000, size=(n, 1)),
    "ad_id": np.random.randint(0, 500, size=(n, 1)),
    "price": np.random.random(size=(n, 1)).astype("float32"),
}
y = np.random.randint(0, 2, size=(n, 1)).astype("float32")

# Optional guard: fail early if a dict key is missing or has the wrong row count.
missing = sorted(set(feature_names) - set(model_input))
if missing:
    raise ValueError(f"Missing model_input keys: {missing}")
if {np.asarray(model_input[name]).shape[0] for name in feature_names} != {n}:
    raise ValueError("All model_input arrays must have the same sample count")

model = DeepFM(linear_feature_columns, dnn_feature_columns, task="binary")
model.compile(optimizer="adam", loss="binary_crossentropy", metrics=["binary_crossentropy"])
history = model.fit(model_input, y, batch_size=32, epochs=1, verbose=2, validation_split=0.2)
pred = model.predict(model_input, batch_size=32)
print(pred.shape)  # (128, 1)
```

## Minimal regression workflow with a dense vector

This covers the common request: "minimal regression model with `DenseFeat` vector and save/load".

```python
import numpy as np
from tensorflow.keras.models import save_model, load_model
from deepctr.feature_column import DenseFeat, get_feature_names
from deepctr.layers import custom_objects
from deepctr.models import DeepFM

feature_columns = [
    DenseFeat("profile_vec", 5),
    DenseFeat("price", 1),
]
feature_names = get_feature_names(feature_columns)

n = 32
x = {
    "profile_vec": np.random.random((n, 5)).astype("float32"),
    "price": np.random.random((n, 1)).astype("float32"),
}
y = np.random.random((n, 1)).astype("float32")

model = DeepFM(feature_columns, feature_columns, dnn_hidden_units=(8,), task="regression")
model.compile("adam", "mse", metrics=["mse"])
model.fit(x, y, batch_size=8, epochs=1, verbose=0)
score = model.evaluate(x, y, batch_size=8, verbose=0)
pred = model.predict(x, batch_size=8)

save_model(model, "deepctr_regression.h5")
reloaded = load_model("deepctr_regression.h5", custom_objects=custom_objects)
reloaded_pred = reloaded.predict(x, batch_size=8)
assert reloaded_pred.shape == pred.shape == (n, 1)
```

Notes:

- `DenseFeat("profile_vec", 5)` expects shape `(n, 5)`, not `(n,)`.
- For scalar dense features, shape `(n, 1)` is safest.
- For `task="regression"`, use `mse` or another regression loss. Do not use `binary_crossentropy`.

## Encoding and model input handoff

Feature-column construction belongs to `data-and-feature-columns`, but Keras workflows still need to enforce the handoff contract:

1. `feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)`.
2. `model_input` is a dictionary keyed by every feature name.
3. Sparse integer features should be integer arrays of ids in `[0, vocabulary_size)`, usually shape `(n, 1)` or `(n,)`.
4. Sparse string features must use `SparseFeat(..., use_hash=True, dtype="string")`; do not pass raw strings to integer `SparseFeat`.
5. Dense scalar features should be numeric float arrays with shape `(n, 1)`.
6. Dense vector features should be numeric float arrays with shape `(n, dimension)`.

## Model-choice variants

All examples below assume `linear_feature_columns`, `dnn_feature_columns`, and `model_input` already exist.

```python
from deepctr.models import DeepFM, DCN, xDeepFM, AutoInt, AFM, FiBiNET, EDCN

# General baseline
model = DeepFM(linear_feature_columns, dnn_feature_columns, task="binary")

# Explicit cross layers
model = DCN(linear_feature_columns, dnn_feature_columns, cross_num=3,
            cross_parameterization="vector", dnn_hidden_units=(128, 64), task="binary")

# Explicit CIN plus deep branch
model = xDeepFM(linear_feature_columns, dnn_feature_columns,
                cin_layer_size=(64, 64), dnn_hidden_units=(128, 64), task="binary")

# Self-attention over feature embeddings
model = AutoInt(linear_feature_columns, dnn_feature_columns,
                att_layer_num=2, att_head_num=2, att_embedding_size=8,
                dnn_hidden_units=(128, 64), task="binary")

# Pairwise attention, useful for inspecting interactions later
model = AFM(linear_feature_columns, dnn_feature_columns,
            use_attention=True, attention_factor=8, task="binary")

# Field-importance and bilinear interactions
model = FiBiNET(linear_feature_columns, dnn_feature_columns,
                bilinear_type="interaction", reduction_ratio=3, task="binary")

# Enhanced deep-and-cross; needs sparse embeddings in the interaction path
model = EDCN(linear_feature_columns, dnn_feature_columns,
             cross_num=2, bridge_type="concatenation", task="binary")
```

Compile each model after construction:

```python
model.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])
```

## Optimizers and callbacks

DeepCTR Keras models accept standard `tf.keras` optimizers and callbacks.

```python
from tensorflow.keras.callbacks import EarlyStopping
from tensorflow.keras.optimizers import Adagrad, Adam

model.compile(Adagrad(learning_rate=0.05), "binary_crossentropy", metrics=["binary_crossentropy"])
callbacks = [EarlyStopping(monitor="val_binary_crossentropy", patience=2, restore_best_weights=True)]
model.fit(model_input, y, batch_size=256, epochs=10, verbose=2,
          validation_split=0.2, callbacks=callbacks)
```

For regression:

```python
model.compile(Adam(learning_rate=1e-3), "mse", metrics=["mse"])
```

## Evaluate and predict

```python
results = model.evaluate(test_model_input, y_test, batch_size=256, verbose=0)
print(dict(zip(model.metrics_names, results if isinstance(results, list) else [results])))

pred = model.predict(test_model_input, batch_size=256)
assert pred.ndim == 2 and pred.shape[1] == 1
```

For binary CTR, predictions are sigmoid probabilities in `[0, 1]`. For regression, predictions are unconstrained scalar values.

## Save and load

Weights-only persistence is the most robust when you can reconstruct the same feature columns and model constructor:

```python
model.save_weights("deepctr_weights.h5")
restored = DeepFM(linear_feature_columns, dnn_feature_columns, task="binary")
restored.compile("adam", "binary_crossentropy", metrics=["binary_crossentropy"])
restored.load_weights("deepctr_weights.h5")
```

Full-model HDF5 save/load needs DeepCTR custom objects:

```python
from tensorflow.keras.models import save_model, load_model
from deepctr.layers import custom_objects

save_model(model, "deepctr_model.h5")
loaded_model = load_model("deepctr_model.h5", custom_objects=custom_objects)
```

If `load_model` fails, first verify TensorFlow/Keras/h5py compatibility, then verify that `custom_objects` is passed as a keyword argument.

## Extract embedding matrices

DeepCTR sparse embedding layer names usually use `sparse_emb_<embedding_name>`.

```python
def get_embedding_weights(feature_columns, model):
    weights = {}
    for fc in feature_columns:
        if hasattr(fc, "embedding_name"):
            name = fc.embedding_name or fc.name
            layer_name = "sparse_emb_" + name
            try:
                weights[name] = model.get_layer(layer_name).get_weights()[0]
            except ValueError:
                # Some models create prefixed or specialized embedding layers.
                matching = [layer for layer in model.layers if layer.name.endswith("_" + name)]
                if matching:
                    weights[name] = matching[0].get_weights()[0]
    return weights
```

Validation checks:

- The matrix row count should equal `vocabulary_size` for that `SparseFeat`.
- The matrix column count should equal `embedding_dim`.
- If no layer matches, inspect `[(layer.name, layer.output_shape) for layer in model.layers]` and check model-specific prefixes.

## Inspect AFM attention weights

AFM stores normalized pairwise attention on the `AFMLayer` after the model has been called. A robust helper should find the layer by class rather than relying on a fixed layer index.

```python
import itertools
from tensorflow.keras.models import Model
from tensorflow.keras.layers import Lambda
from deepctr.layers import AFMLayer
from deepctr.feature_column import get_feature_names

model = AFM(linear_feature_columns, dnn_feature_columns, task="binary")
model.compile("adam", "binary_crossentropy")
model.fit(model_input, y, batch_size=32, epochs=1, verbose=0)

afm_layers = [layer for layer in model.layers if isinstance(layer, AFMLayer)]
if not afm_layers:
    raise ValueError("No AFMLayer found; ensure the model is AFM(use_attention=True)")
afmlayer = afm_layers[0]

attention_model = Model(model.input, outputs=Lambda(lambda _: afmlayer.normalized_att_score)(model.output))
attentional_weights = attention_model.predict(model_input, batch_size=4096)
feature_interactions = list(itertools.combinations(get_feature_names(dnn_feature_columns), 2))

assert attentional_weights.shape[1] == len(feature_interactions)
```

Each `attentional_weights[:, i, 0]` corresponds to `feature_interactions[i]` for all samples.

## Optional CPU/GPU guidance

- DeepCTR does not install TensorFlow; install a TensorFlow package that matches Python, NumPy, CPU/GPU, CUDA, and cuDNN.
- The Keras workflow code does not require GPU. CPU is sufficient for smoke tests and small synthetic examples.
- Multi-GPU training is optional and training-heavy; treat it as reference-only unless the user explicitly asks for distributed or GPU training.
- Use `tf.config.list_physical_devices("GPU")` to report available GPUs, but do not treat "no GPU" as an error for CPU-capable workflows.

## Smoke test

Run the bundled smoke script to verify imports, DeepFM construction, one epoch of training, evaluation, prediction shape/range, and HDF5 save/load with `custom_objects`:

```bash
python skills/disco/deepctr/sub-skills/keras-model-workflows/scripts/keras_tiny_ctr_smoke.py
```

The script uses synthetic data and creates temporary files only.
