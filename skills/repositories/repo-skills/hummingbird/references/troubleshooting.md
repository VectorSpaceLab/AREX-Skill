# Cross-Cutting Troubleshooting

## Purpose

Read this for package-wide Hummingbird failures before routing to a narrower sub-skill reference.

## Install or import failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'hummingbird'` | `hummingbird-ml` is not installed in the active Python | Install `hummingbird-ml`; rerun `python scripts/check_hummingbird_env.py --json` from this skill directory. |
| `MissingBackend` for `onnx` | `onnxruntime` or other ONNX extra is missing, so the backend alias is not registered | Install `hummingbird-ml[onnx]`; then route to [ONNX and model I/O](../sub-skills/onnx-and-model-io/SKILL.md). |
| `MissingBackend` for `tvm` | TVM is optional and not importable | Read [advanced backends](../sub-skills/advanced-backends-and-performance/SKILL.md); TVM often needs a separate compatible Python/build environment. |
| `MissingConverter` | Source estimator/operator is unsupported or optional source package is absent | Check [sklearn operator coverage](../sub-skills/sklearn-pipelines-and-operators/SKILL.md) or [optional source models](../sub-skills/optional-source-models/SKILL.md). |
| Optional LightGBM/XGBoost import error on Linux/Mac | Missing OpenMP/cmake/system library or optional package was not installed | Read [optional source troubleshooting](../sub-skills/optional-source-models/references/troubleshooting.md). |

## Backend and hardware failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `torch.cuda.is_available()` is false even though a GPU exists | CPU-only PyTorch wheel, driver/container passthrough issue, or incompatible CUDA runtime | Run [advanced backend checker](../sub-skills/advanced-backends-and-performance/scripts/check_backends.py). Reinstall a CUDA-compatible PyTorch wheel only when GPU execution is required. |
| CPU conversion works but GPU conversion fails | Hummingbird core may be valid, but the active PyTorch/CUDA stack is not verified | Keep CPU validation separate from GPU validation; do not claim GPU coverage until a tiny CUDA tensor and converted model path run. |
| TVM compilation hangs or is very slow | TVM backend compiles fixed-shape graphs and may need fuse-depth controls | Use `constants.TVM_MAX_FUSE_DEPTH`, small representative inputs, and the TVM reference under advanced backends. |

## Conversion and parity failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| scikit-learn `NotFittedError` or assertion around fitted estimator | The estimator was not trained before conversion | Fit the estimator first and run a small source-model prediction before calling `convert`. |
| Predictions have wrong shape or differ from source model | Input dtype/shape/column layout changed, wrong validation method, or unsupported operator branch | Validate on the exact downstream method (`predict`, `predict_proba`, `transform`, `decision_function`, `score_samples`); read the core and sklearn pipeline references. |
| Backend says test inputs are required | Trace/export backend cannot infer input shape/schema | Pass representative `test_input`; for multiple inputs use tuple arrays or columnar structures described in the sklearn data-format reference. |
| XGBoost conversion cannot infer feature count | XGBoost object lacks a usable `num_features` signal | Pass representative 2-D `test_input` when converting; route to optional source models. |

## Artifact load failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Loading a saved model asks for `digest` or `override_flag=True` | Hummingbird's loader protects artifact integrity | Prefer the digest returned by `save()`. Use `override_flag=True` only for a trusted artifact. |
| Version warnings while loading | Saved artifact records different package versions | Treat warnings as compatibility risk; validate predictions against a known fixture before using the artifact. |
| Saved directory already exists | Container `save(location)` expects a non-existing location before creating and zipping it | Choose a fresh location or remove an old temporary output deliberately. |

## When to stop

Stop and request a narrower scope or prepared environment when the user requires GPU, TVM, SparkML, Prophet, LightGBM, or XGBoost runtime verification but the active environment lacks the required backend, compiled packages, JVM, or system libraries. Do not substitute a CPU import check for a required accelerator or optional-source runtime check.
