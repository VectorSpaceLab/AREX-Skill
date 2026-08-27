# ArcGIS Learn Workflow Patterns

This reference distills the `arcgis.learn` workflow shapes observed across the deep-learning guide and data-science sample notebooks. It is intentionally self-contained: do not require the original notebooks to run or read before using these patterns.

## 1. Dependency and runtime gate

- `arcgis.learn` is an optional surface. The base `arcgis` package can import successfully while `arcgis.learn` fails because `torch`, `torchvision`, or a model-specific dependency is missing.
- Before attempting training, import-heavy inspection, or notebook recovery, run `python scripts/check_learn_optional_deps.py` from this sub-skill directory.
- If the report shows `arcgis.learn` failing with `No module named 'torchvision'`, treat the deep-learning stack as incomplete. Repair the `torch`/`torchvision` pair first, then rerun the check.
- The repository evidence includes many GPU-oriented notebooks and sample items tagged for advanced GPU runtimes. This skill did not verify GPU training, model downloads, ArcGIS Notebook GPU runtimes, or Image Server deployment. Mark those as unverified unless the user supplies a matching runtime, data, and credentials.

## 2. Choose the preparation object by input shape

| User input or label shape | Start with | Common model families |
| --- | --- | --- |
| Exported imagery chips, masks, bounding boxes, image pairs, video frames, or raster change pairs | `prepare_data` | `UnetClassifier`, `MaskRCNN`, `SingleShotDetector`, `FasterRCNN`, `YOLOv3`, `RetinaNet`, `ChangeDetector`, `Pix2Pix`, `CycleGAN`, `SuperResolution`, `ObjectTracker`, road/edge detectors, SAM/SamLoRA, MMDetection/MMSegmentation adapters |
| Feature-layer rows, spatially enabled DataFrame rows, tabular covariates, or univariate/multivariate sequences | `prepare_tabulardata` | `MLModel`, `AutoML`, `FullyConnectedNetwork`, `TimeSeriesModel` |
| Labeled documents, text classes, entity spans, or sequence-to-sequence text data | `prepare_textdata` | `TextClassifier`, `EntityRecognizer`, `SequenceToSequence`, third-party language model wrappers |
| LiDAR or 3D point-cloud chips/labels | `prepare_data(..., dataset_type=...)` with a point-cloud dataset type | `PointCNN`, `PointTransformer`, `RandLA-Net`, `SQN`, `SECOND`, MMDetection3D-style paths |
| A custom detector, segmentation framework, NLP function, or external model package | `ModelExtension` or a framework adapter | Custom `FasterRCNN`, custom NLP `.dlpk`, `MMDetection`, `MMSegmentation`, `SamLoRA` |

When in doubt, do not begin with a model class. First identify the input object and the training labels, then pick the preparation helper and model family.

## 3. Common imagery workflow

Most image and raster deep-learning notebooks follow this high-level shape:

1. Export or collect training data in the notebook-specific layout. Examples include object-detection boxes, instance masks, pixel masks, image pairs, before/after change images, point-cloud chips, or video frame metadata.
2. Build a data object with `prepare_data(...)`. Typical knobs are `path`, `chip_size`, `batch_size`, `split_pct`, `dataset_type`, imagery/band settings, and optional transforms.
3. Instantiate the model with the data object and optional `backbone`, `model_arch`, or model-specific parameters.
4. Inspect learning-rate or data sanity with `lr_find()`, `data.show_batch()`, or `model.show_results()` when available.
5. Train with `fit(...)` only after dependency, data, and backend readiness are confirmed.
6. Evaluate using model-appropriate methods: examples include `show_results()`, `average_precision_score()`, `precision_recall_score()`, `accuracy()`, or manual inspection of predictions.
7. Run inference with `predict(...)`, `predict_video(...)`, or task-specific inference helpers only on a trained/saved model and valid input.
8. Persist with `save(...)`. Some image notebooks use `save(..., publish=True)` when publishing a model artifact to ArcGIS infrastructure is intended.

A safe future agent should keep every step explicit. If the user only needs model choice or import triage, stop before training.

## 4. Text, NLP, and language-model workflows

- Use `prepare_textdata` for labeled text classification, entity extraction, and sequence-to-sequence preparation.
- Use `TextClassifier` when each document/text row has a class label.
- Use `EntityRecognizer` when labels are spans or named entities inside the text.
- Use `SequenceToSequence` or third-party language-model wrapper guidance when the task is address standardization, correction, or custom text transformation.
- Notebook patterns include `supported_backbones`, `fit(...)`, `accuracy()`, `precision_score()`, `recall_score()`, `predict(...)`, and `save(...)`.
- Model-extension and custom NLP examples package a custom model or `.dlpk` so `arcgis.learn` can load it later. Treat those as dependency-sensitive and version-sensitive.

## 5. Tabular and time-series workflows

- Use `prepare_tabulardata` for feature layers, spatially enabled DataFrames, ordinary tabular predictors, and time-series rows.
- `MLModel` is the wrapper path for classical or scikit-learn-style tabular models exposed through `arcgis.learn`.
- `AutoML` appears in tabular automation notebooks and should be used when the requested deliverable is automated model search rather than hand-picking a regressor/classifier.
- `FullyConnectedNetwork` is used for deep-learning tabular regression/classification patterns.
- `TimeSeriesModel` handles sequence forecasting. Notebook evidence uses architectures such as `InceptionTime`, `ResCNN`, `ResNet`, and `FCN`, and may return forecasts as a DataFrame when `prediction_type='dataframe'` is used.
- Validate target fields, date fields, explanatory variables, missing values, categorical fields, and scaler/normalization choices before fitting.

## 6. Point-cloud and 3D workflows

- Point-cloud notebooks cover classification, segmentation, and object detection. Do not interchange these dataset types.
- Observed point-cloud families include `PointCNN`, `PointTransformer`, `RandLA-Net`, `SQN`, and `SECOND`.
- Use the task-specific `dataset_type` and data layout expected by `prepare_data(...)`; wrong task/type pairings usually fail before training or produce unusable metrics.
- Point-cloud workflows are advanced and typically need GPU memory, 3D point-cloud preprocessing, and large data assets. Treat CPU-only guidance as planning, not verification.

## 7. Model extensibility and adapter workflows

- `ModelExtension` wraps a custom Python model so it can participate in the `arcgis.learn` preparation, training, saving, and inference contract. Notebook evidence includes a custom `FasterRCNN` class and custom NLP functions.
- `MMDetection` and `MMSegmentation` adapters drive external framework models from `arcgis.learn`, sometimes using named supported models and sometimes using config/weight files.
- `SAM` and `SamLoRA` workflows are fine-tuning or adaptation paths, not generic raster analytics. They require their own model weights, data layout, and dependency stack.
- Treat all custom/adapter paths as requiring stronger environment verification than built-in families. If the external import fails, stop and report the missing framework rather than substituting a different model silently.

## 8. Save, export, deploy, and registry patterns

- `save(...)` is the basic persistence pattern for trained models.
- `save(..., publish=True)` is used in some image workflows when the trained model should be published for ArcGIS-side inference. This requires credentials and a compatible portal/server context.
- `list_models()` is a registry inspection helper for deployed models. It is not proof that a local training artifact was published.
- `uninstall_model()` is a destructive cleanup helper for deployed models. Do not call it unless the user explicitly asks to remove a deployed model and has confirmed the target.
- Some notebooks describe importing saved artifacts into ArcGIS Pro or ArcGIS Enterprise. Treat that as a deployment boundary: record model path, metadata, classes, imagery type, and environment assumptions before handing off.

## 9. Route reminders

- If the user is only applying raster functions, raster analytics, or orthomapping without a learned model, route to imagery-raster-analysis.
- If the user is manipulating feature layers, spatially enabled DataFrames, or spatial-analysis tools without model training, route to features-dataframes-analysis.
- If the user asks for hosted AI utility services rather than training/deploying `arcgis.learn` models, route to apps-knowledge-ai-services.
