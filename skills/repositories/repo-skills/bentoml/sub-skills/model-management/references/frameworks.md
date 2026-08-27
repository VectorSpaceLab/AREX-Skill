# Framework Helpers And Optional Dependencies

BentoML includes model helper modules for common ML frameworks. These helpers generally provide a consistent pattern:

- `save_model(name, model, ...)` writes a framework-native object into BentoML's model store.
- `load_model(tag_or_model, ...)` loads the framework-native object from a stored BentoML model.
- `get(tag)` returns the stored `bentoml.Model` after checking that the model was saved by the same helper module.
- Some helpers also expose `import_model(...)` for external framework artifact directories and `get_service(...)` for quick service generation.

In current BentoML versions, framework helper modules are maintained for compatibility and may emit deprecation warnings through the framework importer. Do not overstate them as the only recommended path. For new services, it is often clearer to use `BentoModel` or `HuggingFaceModel` at Service class scope and load the artifact with the framework's own loader in `__init__`.

## Common Helper Modules

| Helper | Typical artifact | Required dependency family | Notes |
| --- | --- | --- | --- |
| `bentoml.sklearn` | scikit-learn estimator | `scikit-learn` | Uses pickle/joblib-style persistence. Best for classical ML estimators. |
| `bentoml.pytorch` | `torch.nn.Module` | `torch` | `load_model(..., device_id=...)` can target CPU/GPU; runtime torch/CUDA must match the saved model and deployment image. |
| `bentoml.torchscript` | TorchScript module | `torch` | Use when the model is already scripted/traced. |
| `bentoml.pytorch_lightning` | Lightning model/module | `torch`, `pytorch_lightning` | Requires Lightning package compatibility. |
| `bentoml.tensorflow` | TensorFlow SavedModel/Keras-compatible object | `tensorflow` | TensorFlow version and hardware backend mismatches are common runtime failures. |
| `bentoml.keras` | Keras model | `tensorflow` backend | Keras helper depends on TensorFlow in this codebase. |
| `bentoml.transformers` | Transformers pipeline/model/tokenizer | `transformers` | Can import/save HF artifacts; gated/private models need runtime credentials outside the skill. |
| `bentoml.diffusers` | Diffusers pipeline | `diffusers`, `transformers`, usually `accelerate` | Heavy dependency and GPU-sensitive; prefer explicit image/runtime dependency declarations. |
| `bentoml.onnx` | ONNX model/session | `onnx`, `onnxruntime` | Provider selection must match installed `onnxruntime` build. |
| `bentoml.xgboost` | XGBoost booster/model | `xgboost` | Provides `get_service` compatibility helper. |
| `bentoml.lightgbm` | LightGBM booster | `lightgbm` | Provides `get_service` compatibility helper. |
| `bentoml.catboost` | CatBoost model | `catboost` | Provides `get_service` compatibility helper. |
| `bentoml.mlflow` | MLflow PyFunc model | `mlflow` | Provides `import_model`, `load_model`, and `get_service`. |
| `bentoml.picklable_model` | arbitrary Python object | standard serialization stack | Use cautiously; Python/package compatibility matters. |
| `bentoml.fastai`, `bentoml.flax`, `bentoml.easyocr`, `bentoml.detectron` | framework-specific objects | corresponding framework packages | Optional and dependency-heavy; verify before recommending. |

## Choosing A Pattern

### Scikit-learn

Use the helper when the service should load the estimator directly and the runtime includes `scikit-learn`:

```python
import bentoml

# training/import step
saved = bentoml.sklearn.save_model("iris_sklearn", estimator)

# service step
model = bentoml.sklearn.load_model("iris_sklearn:latest")
```

Use `BentoModel` plus `joblib.load(model_ref.path_of("model.pkl"))` when the artifact was saved as raw files with `bentoml.models.create()` or when you need custom directory layout control.

### PyTorch

Use `bentoml.pytorch.save_model()` and `bentoml.pytorch.load_model()` for `torch.nn.Module` objects if the serving image has the correct `torch` package and device support. Specify CPU/GPU loading intentionally; do not assume `cuda:0` exists in the runtime.

For portability or strict packaging, save a TorchScript or ONNX artifact and use the matching helper/runtime provider. Hardware mismatch troubleshooting belongs with dependency and deployment configuration, not model tag lookup.

### Hugging Face / Transformers

For remote Hub models used directly in a Service, declare `HuggingFaceModel("org/model")` at class scope and load from the resolved path in `__init__`. For stored Transformer artifacts, use `bentoml.transformers` only if `transformers` is installed and the stored model's `module` is `bentoml.transformers`.

Private/gated models require external credentials in the build/runtime environment. Never put tokens in generated skills, source snippets, or model metadata.

### ONNX

Use `bentoml.onnx.load_model(tag, providers=[...])` only when `onnxruntime` has the requested execution providers. A provider parse error usually means the provider list or installed runtime package is wrong, not that BentoML cannot find the model.

## Optional Dependency Checks

Run the bundled check before advising a framework helper:

```bash
python skills/bentoml/sub-skills/model-management/scripts/check_framework_extra.py sklearn
python skills/bentoml/sub-skills/model-management/scripts/check_framework_extra.py pytorch
python skills/bentoml/sub-skills/model-management/scripts/check_framework_extra.py onnx --json
```

Interpretation:

- `ok: true` means the expected Python modules import in the active environment.
- `ok: false` means use a different pattern, install the missing dependency in the project/runtime image, or make the dependency explicit in the Bento build configuration.
- The script does not install extras and does not download models.

## Module Mismatch Rule

Framework `get()` and `load_model()` implementations check the stored model's `info.module`. Loading a model saved with `bentoml.sklearn` through `bentoml.pytorch.load_model()` should fail. When diagnosing a load error:

1. Inspect `bentoml models get TAG --output json`.
2. Compare `module` with the helper being used.
3. If `module` is empty/custom, load files manually from `BentoModel(...).path` or `bentoml.models.get(TAG).path`.
4. If the helper is deprecated or unavailable, preserve behavior with raw file loading rather than silently switching serialization formats.
