# Deep Learning Troubleshooting

Use this reference before running expensive notebooks, service calls, or model publishing. The fastest safe diagnostic is `python scripts/check_learn_optional_deps.py`, which performs import/CUDA probes only.

## Import and optional-dependency gates

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `import arcgis` works but `import arcgis.learn` or `from arcgis.learn import ...` fails with `No module named 'torchvision'` | The optional deep-learning stack is incomplete; this exact failure was observed in the inspection environment. | Stop at the import gate. Install a compatible `torch`/`torchvision` pair for the target Python/CUDA runtime, then rerun `scripts/check_learn_optional_deps.py`. Do not claim `arcgis.learn` support until the probe passes. |
| `No module named 'torch'` | `arcgis.learn` optional dependencies are not installed. | Install a compatible `torch` distribution before training or importing deep-learning families. If the user only needs routing or model choice, continue with planning only. |
| `torch` imports but CUDA is unavailable | CPU-only runtime, incompatible CUDA wheel, missing driver, or no GPU assignment. | Treat GPU notebooks as unverified. Either switch to an approved GPU runtime or report that training/inference is limited to import-only or CPU-compatible planning. |
| Fastai, model-backbone, MMDetection, MMSegmentation, SAM, or custom model import errors | Family-specific dependency stack is missing or mismatched. | Do not substitute a different model silently. Identify the missing framework and ask whether the user wants to install that exact stack or choose a simpler built-in family. |

## Data-preparation failures

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `prepare_data` returns an empty data object or raises shape/layout errors | Exported chips, masks, boxes, image pairs, class folders, or `dataset_type` do not match the model family. | Recheck label geometry and export format before training. Instance masks, ordinary pixel masks, object boxes, image pairs, before/after images, videos, and point clouds are not interchangeable. |
| Imagery model sees wrong band count or poor results immediately | Imagery type, multispectral bands, chip size, or normalization does not match the exported training data. | Confirm band order, imagery type, `chip_size`, transforms, and class mapping before `fit(...)`. |
| `prepare_tabulardata` fails or model sees no target | Target field, explanatory variables, categorical fields, date fields, or SEDF/feature-layer schema are invalid. | Validate table columns, missing values, date parsing, target type, train/validation split, and scaler choices. Route pure feature/SEDF cleaning to features-dataframes-analysis. |
| `prepare_textdata` fails | Text training files are unlabeled, malformed, encoded incorrectly, or use an entity/span format that does not match the model. | Validate labels before fitting. Use `TextClassifier` for document labels, `EntityRecognizer` for spans, and sequence-to-sequence/custom NLP paths for generated output text. |
| Point-cloud training fails early | Wrong point-cloud `dataset_type`, class mapping, coordinate/attribute layout, or memory budget. | Match classification, segmentation, or object-detection dataset type to the chosen family; check labels and GPU memory before training. |

## Training, evaluation, and inference failures

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `lr_find()` or `fit(...)` fails immediately | Empty training set, unsupported backbone/model architecture, missing labels, missing GPU memory, or optional dependency mismatch. | Check data object size/classes, target family, backend probe, and `backbone`/`model_arch` values before retrying. |
| Metrics are empty or misleading | Validation split has too few positives/classes, class mapping is wrong, or model family does not match labels. | Inspect class balance and validation examples. Use model-appropriate metrics: average precision for detectors, precision/recall for NER/change detection, accuracy for text classification, or forecasting diagnostics for time series. |
| `predict(...)` fails | Input type does not match the trained model, model was not trained/saved, or required metadata is missing. | Confirm the model family and input format. Use `predict_video(...)` only when video path and metadata requirements are satisfied. |
| `show_results()` fails or displays nonsense | Data transforms, class maps, or inference input shape do not match training. | Rebuild the data object with the correct preprocessing and inspect a small batch before training again. |

## Save, publish, deploy, and registry failures

| Symptom | Likely cause | Safe action |
| --- | --- | --- |
| `save(...)` succeeds locally but server inference is unavailable | A local saved model is not automatically deployed. | Record the saved artifact and deployment assumptions. Do not promise ArcGIS Pro/Enterprise import or Image Server inference without deployment validation. |
| `save(..., publish=True)` fails | Publishing requires credentials, portal/server access, compatible model metadata, and sometimes Image Server resources. | Stop and ask for explicit credentials/service approval before any publish attempt. Do not publish during import-only verification. |
| `list_models()` returns nothing | The model was never published to the Image Server or the query is aimed at the wrong GIS/server context. | Verify the deployment target and credentials. `list_models()` is a deployed-model registry check, not a local artifact check. |
| `uninstall_model()` is requested | This is a destructive server-side cleanup operation. | Require explicit target confirmation before calling it. Never use it as a troubleshooting shortcut. |

## Fast support cases

### Missing `torchvision`
1. Run `python scripts/check_learn_optional_deps.py`.
2. If `arcgis.learn` fails with `ModuleNotFoundError: No module named 'torchvision'`, report that base `arcgis` can still work but `arcgis.learn` is unavailable.
3. Install or request a compatible `torch`/`torchvision` pair for the target runtime, then rerun the probe.
4. Do not execute notebooks, train, or download models while the gate is failing.

### Choosing data prep and model workflow
1. Determine the input object: image chips, table rows, text documents, point clouds, video, or custom model package.
2. Pick the prep helper: `prepare_data`, `prepare_tabulardata`, `prepare_textdata`, point-cloud `prepare_data(..., dataset_type=...)`, or `ModelExtension`.
3. Pick the model family using `references/model-catalog.md`.
4. Only then discuss `fit`, metrics, `predict`, `save`, or publish/deploy.

## Route reminders

- If the task is raster analytics without `arcgis.learn`, route to imagery-raster-analysis.
- If the task is feature engineering, hosted feature-layer editing, or spatially enabled DataFrame analysis before/without model training, route to features-dataframes-analysis.
- If the task is AI utility services, dashboards, Knowledge Graphs, or app automation, route to apps-knowledge-ai-services.
