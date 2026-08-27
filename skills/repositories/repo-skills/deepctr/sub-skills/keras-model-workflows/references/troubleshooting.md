# Troubleshooting Keras DeepCTR Workflows

Use this page when a Keras-style DeepCTR task fails during import, model construction, compile/fit/evaluate/predict, save/load, inspection, or smoke testing.

## TensorFlow is not installed

Symptom examples:

- `ModuleNotFoundError: No module named 'tensorflow'`
- `ImportError` while importing `deepctr.models`

Likely cause: DeepCTR does not install TensorFlow for you.

Recovery:

1. Install a TensorFlow build compatible with the user's Python, CPU/GPU, operating system, CUDA, cuDNN, NumPy, and platform.
2. Then install or import `deepctr`.
3. Validate with:

```python
import tensorflow as tf
import deepctr
print(tf.__version__)
print(deepctr.__version__)
```

Do not claim a DeepCTR model bug until TensorFlow imports cleanly.

## NumPy, h5py, TensorFlow, or Keras incompatibility

Symptom examples:

- TensorFlow rejects installed NumPy, often with a message about an unsupported NumPy major version.
- `h5py` or HDF5 errors when saving/loading `.h5` models.
- Optimizer, metric, or serialization failures after mixing Keras imports.

Recovery:

- Follow the TensorFlow release's dependency requirements, especially NumPy version requirements.
- For Python `>=3.9`, DeepCTR allows modern `h5py>=3.7.0`, but TensorFlow may still constrain NumPy.
- Use public imports such as:

```python
from tensorflow.keras.models import save_model, load_model
from tensorflow.keras.optimizers import Adam
```

- Avoid `tensorflow.python.keras` in user code; it is private API and can break serialization or optimizer/metric loading across TensorFlow versions.

## Missing input dictionary keys

Symptom examples:

- Keras raises a `ValueError` about missing data for named inputs.
- Training starts with unexpected zero/empty data for a feature.

Likely cause: `model_input` does not contain every name returned by `get_feature_names(linear_feature_columns + dnn_feature_columns)`.

Recovery:

```python
from deepctr.feature_column import get_feature_names

feature_names = get_feature_names(linear_feature_columns + dnn_feature_columns)
missing = sorted(set(feature_names) - set(model_input))
extra = sorted(set(model_input) - set(feature_names))
if missing:
    raise ValueError(f"Missing DeepCTR input keys: {missing}")
if extra:
    print(f"Unused model_input keys: {extra}")
```

Extra keys are often harmless but may reveal that the user passed target columns or sequence support columns to the wrong workflow.

## Inconsistent sample counts

Symptom examples:

- `Data cardinality is ambiguous`
- Keras complains about input arrays with different first dimensions.

Recovery:

```python
sizes = {name: len(value) for name, value in model_input.items()}
if len(set(sizes.values())) != 1:
    raise ValueError(f"Inconsistent model_input row counts: {sizes}")
if len(y) != next(iter(sizes.values())):
    raise ValueError("Target row count does not match model_input")
```

## Raw string features without hashing or encoding

Symptom examples:

- Embedding lookup type errors.
- A DeepCTR `SparseFeat(dtype='string')` error saying string ids require hashing.
- Categorical columns appear as object/string arrays but `SparseFeat` uses default `dtype="int32"`.

Recovery:

Choose one:

1. Encode categories to integer ids before fitting and use `SparseFeat(..., dtype="int32", use_hash=False)`.
2. Use on-the-fly hashing and pass strings:

```python
SparseFeat("ad_category", vocabulary_size=10000, embedding_dim=8,
           use_hash=True, dtype="string")
```

Do not pass raw strings to an integer `SparseFeat`.

## Dense-only model fails

Symptom examples:

- A model raises `DenseFeat is not supported in dnn_feature_columns`.
- Interaction layers complain about no sparse embeddings or invalid dimensions.

Likely cause: Some models are sparse-interaction-first and cannot operate on dense-only inputs.

Recovery:

- For dense-only classification or regression, prefer `DeepFM` with `DenseFeat` columns. A native dense-only model IO test covers this path.
- Avoid `AFM`, `CCPM`, and `EDCN` as dense-only first choices because their main interaction paths disable dense support.
- For dense vector inputs, use `DenseFeat("name", dimension)` and provide arrays shaped `(n, dimension)`.

## Sparse plus dense shape problems

Symptom examples:

- Input shape mismatch for named dense input.
- Unexpected output shape from Keras.
- Dense vector is flattened or treated as many samples.

Recovery:

- Scalar dense features: `DenseFeat("x", 1)` and data shape `(n, 1)`.
- Dense vector features: `DenseFeat("vec", d)` and data shape `(n, d)`.
- Sparse scalar features: shape `(n, 1)` or `(n,)` with integer ids.
- The first dimension must match for every feature and target.

## Constructor-specific errors

| Symptom | Likely cause | Recovery |
|---|---|---|
| `Either hidden_layer or cross layer must > 0` | `DCN` or `DCNMix` was instantiated with both no DNN units and `cross_num=0`. | Set `cross_num>=1` or provide `dnn_hidden_units`. |
| `Either hidden_layer or att_layer_num must > 0` | `AutoInt` has no attention layers and no DNN tower. | Set `att_layer_num>=1` or provide `dnn_hidden_units`. |
| `Cross layer num must > 0` | `EDCN(cross_num=0)`. | Use `cross_num>=1` or choose `DCN` for an ablated cross-free baseline. |
| `kernel_type must be mat,vec or num` | Invalid `PNN(kernel_type=...)`. | Use `"mat"`, `"vec"`, or `"num"`. |
| `conv_kernel_width, conv_filters, new_maps and pooling_width must have same length` | Invalid `FGCNN` convolution settings. | Make all four tuples the same length. |
| `dnn_hidden_units is null!` | `IFM` or `DIFM` was given an empty DNN tower. | Provide at least one DNN hidden layer. |
| `there are no sparse features` | Input-aware or interaction-heavy model received only dense columns. | Add sparse feature columns or choose a dense-tolerant model such as `DeepFM`. |

## Wrong task/loss pairing

Symptom examples:

- Regression predictions are constrained to `[0, 1]` unexpectedly.
- Binary classifier trains with MSE by accident and metrics are not useful.

Recovery:

- For CTR classification: `task="binary"`, `loss="binary_crossentropy"`, metrics such as `"binary_crossentropy"` or AUC metrics from `tf.keras.metrics`.
- For scalar regression: `task="regression"`, `loss="mse"`, metric `"mse"` or MAE.
- Check target shape `(n, 1)` and target dtype numeric.

## Full-model load fails with custom objects

Symptom examples:

- `Unknown layer: DNN`, `Unknown layer: PredictionLayer`, `Unknown layer: AFMLayer`, or similar.
- `load_model` fails after `save_model` on a DeepCTR model.

Recovery:

```python
from tensorflow.keras.models import load_model
from deepctr.layers import custom_objects

model = load_model("deepctr_model.h5", custom_objects=custom_objects)
```

If this still fails:

1. Confirm you did not mix `tensorflow.python.keras` and `tensorflow.keras` imports.
2. Confirm TensorFlow/Keras/h5py compatibility.
3. Prefer reconstructing the same model and using `load_weights`.
4. If the model used custom activation objects outside DeepCTR, include those in a merged custom object dict.

## Embedding extraction returns no layer

Symptom examples:

- `ValueError: No such layer: sparse_emb_user_id`
- Embedding weight helper returns an empty dict.

Likely causes:

- The model prefixes embedding layers, e.g. linear or feature-generation paths.
- The feature uses `embedding_name` different from `name`.
- The model is dense-only.

Recovery:

```python
[(layer.name, getattr(layer, "output_shape", None)) for layer in model.layers if "emb" in layer.name]
```

Search by `embedding_name`, not only by feature name. Validate returned matrix shape against `vocabulary_size` and `embedding_dim`.

## AFM attention extraction fails

Symptom examples:

- No `AFMLayer` found.
- `normalized_att_score` is missing or stale.
- Attention shape does not match pairwise combinations.

Recovery:

- Ensure the model is `AFM(..., use_attention=True)`.
- Fit or call the model once before extracting attention.
- Find the layer by class (`isinstance(layer, AFMLayer)`) instead of relying on `model.layers[-3]`.
- `AFM` attention weights correspond to `itertools.combinations(get_feature_names(dnn_feature_columns), 2)`.

## Optional GPU warnings

Symptom examples:

- TensorFlow logs warnings about missing CUDA libraries.
- `tf.config.list_physical_devices("GPU")` returns `[]`.
- Multi-GPU examples are too slow or fail in a CPU-only environment.

Recovery:

- CPU is acceptable for Keras model construction, fitting small batches, save/load, and the bundled smoke test.
- Do not treat missing GPU as a failure unless the user explicitly requested GPU training.
- For GPU tasks, install the TensorFlow package compatible with CUDA/cuDNN and verify with:

```python
import tensorflow as tf
print(tf.config.list_physical_devices("GPU"))
```

- Multi-GPU Criteo-style training is optional and training-heavy; use it only when the user asks for distributed or multi-GPU guidance.

## Smoke script failure triage

Run:

```bash
python skills/disco/deepctr/sub-skills/keras-model-workflows/scripts/keras_tiny_ctr_smoke.py
```

Expected behavior:

- Prints TensorFlow and DeepCTR versions.
- Builds a synthetic DeepFM binary CTR model.
- Trains one tiny epoch.
- Prints evaluation metrics and prediction shape/range.
- Saves and loads a temporary `.h5` model with `custom_objects`.
- Exits with status 0.

If it fails:

1. First fix TensorFlow/DeepCTR import errors.
2. If training fails, inspect dict keys and array shapes printed by any added debugging.
3. If save/load fails, check `h5py` and pass `custom_objects` exactly.
4. If predictions are not shape `(n, 1)`, re-check model task and feature-column dimensions.
