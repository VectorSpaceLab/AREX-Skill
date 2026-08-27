# AutoGluon Package Overview

## When To Read

Read this when deciding which AutoGluon subpackage, predictor class, optional dependency family, or bundled helper applies to a task.

## Public Package Map

| Package | Primary role | Key APIs | Typical dependencies |
| --- | --- | --- | --- |
| `autogluon.common` | Shared utilities, data loading/saving, feature metadata, search spaces | `TabularDataset`, `FeatureMetadata`, `space` | NumPy, Pandas, PyArrow, scikit-learn, boto3 |
| `autogluon.core` | Metrics, HPO/search spaces, ensemble/model abstractions, callbacks, resource helpers | `Scorer`, `get_metric`, `space`, callbacks | SciPy, scikit-learn, NetworkX, Matplotlib |
| `autogluon.features` | Tabular feature generators and feature metadata support | `AutoMLPipelineFeatureGenerator`, generator classes | Pandas, scikit-learn |
| `autogluon.tabular` | Supervised tabular AutoML | `TabularPredictor`, `TabularDataset` | Core stack plus optional LightGBM, CatBoost, XGBoost, Torch, Ray, tabular foundation-model extras |
| `autogluon.timeseries` | Probabilistic time-series forecasting | `TimeSeriesPredictor`, `TimeSeriesDataFrame` | Core/tabular stack plus Torch, GluonTS, StatsForecast, MLForecast, Chronos/transformers |
| `autogluon.multimodal` | Text/image/document/object/NER/matching/segmentation AutoML | `MultiModalPredictor` | Torch, torchvision, transformers, Lightning, TIMM, OCR/PDF/detection/export optional packages |
| `autogluon` | Meta-package for the full stack | imports subpackages | Full stack; heavier than a single subpackage install |

## Verified Public Predictors

The generated skill was based on live inspection of these public classes:

- `TabularPredictor(label, problem_type=None, eval_metric=None, path=None, ...)`
- `TimeSeriesPredictor(target=None, known_covariates_names=None, prediction_length=1, freq=None, ...)`
- `TimeSeriesDataFrame(data, static_features=None, id_column=None, timestamp_column=None, num_cpus=-1)`
- `MultiModalPredictor(label=None, problem_type=None, query=None, response=None, match_label=None, ...)`

Read the owning sub-skill for method signatures and workflow examples.

## Optional Dependency Families

| Need | Likely package family | Notes |
| --- | --- | --- |
| Fast tabular gradient boosting | LightGBM, CatBoost, XGBoost | Often installed by full AutoGluon; narrow installs may need extras or separate packages. |
| Tabular neural networks/foundation models | Torch, fastai, tabpfn, tabicl, tabdpt, mitra-related packages | Can require model downloads, GPU, or large wheels. |
| HPO with Ray | `autogluon.core` Ray extras / `ray[tune]` | Check Ray version support for the user's Python/OS. |
| Forecasting deep/global models | Torch, Lightning, GluonTS, transformers, Chronos | Prefer local/statistical models for offline smoke checks. |
| Multimodal text/image/document models | Torch, torchvision, transformers, TIMM, PDF/OCR packages | Matching torch/torchvision wheels matters. |
| Object detection/segmentation | MMDetection/MMCV-compatible stack, COCO/VOC data, GPU often useful | Validate annotations before training; do not assume these extras are present. |
| Export/deployment | ONNX, ONNXRuntime, TensorRT | Optional and platform-specific; verify imports first. |

## Routing Heuristics

- Rows + target column -> `sub-skills/tabular-ml/`.
- `item_id` + `timestamp` + forecast horizon -> `sub-skills/time-series-forecasting/`.
- Text/image/document/NER/matching/object detection/segmentation -> `sub-skills/multimodal-automl/`.
- Import/version/backend problems before modeling -> root `references/troubleshooting.md` and `scripts/check_autogluon_env.py`.

## CPU And GPU Guidance

A GPU may accelerate many workflows, but package inspection and most schema diagnostics are CPU-safe. Do not force CUDA installations just because a GPU exists. Require GPU verification only when the user's requested workflow needs GPU execution, GPU-specific model families, TensorRT, MMDetection CUDA ops, or large foundation-model inference/training.
