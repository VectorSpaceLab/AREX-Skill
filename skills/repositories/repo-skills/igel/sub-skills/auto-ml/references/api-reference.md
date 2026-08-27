# Igel Auto-ML API Reference

This reference covers the AutoKeras-backed code path owned by the `auto-ml` sub-skill. It is intentionally separate from classic `Igel`/CSV workflows; for those, route to [tabular-workflows](../../tabular-workflows/SKILL.md).

## Public import surface

- `igel.auto.__all__` exposes `IgelCNN`.
- `IgelCNN` is initialized as `IgelCNN(**cli_args)`. The verified callable signature is `(**cli_args)`.
- `igel.auto.models.Models.get(model_type, *args, **kwargs)` selects an AutoKeras class from a fixed task-name map and returns the class, not an already-fitted model. Extra args/kwargs are accepted by the signature but are not used by the current selector logic.

## Supported task names

Use the exact PascalCase task names below; aliases such as `image-classification`, `image_classification`, or lowercase variants are not supported by `Models.get`.

| Task string | AutoKeras class selected | Notes |
| --- | --- | --- |
| `ImageClassification` | `autokeras.ImageClassifier` | Concrete repo docs and example config target this path. |
| `ImageRegression` | `autokeras.ImageRegressor` | Registered selector; use the same artifact and loader caveats as the image path. |
| `TextClassification` | `autokeras.TextClassifier` | Registered selector; docs describe class-subfolder text datasets, but the current `IgelCNN` loader is image-directory oriented. Verify before claiming turnkey text training. |
| `TextRegression` | `autokeras.TextRegressor` | Registered selector; no repo-shipped end-to-end example. |
| `StructuredDataClassification` | `autokeras.StructuredDataClassifier` | Registered selector; no repo-shipped dedicated structured-data AutoKeras loader/example. Do not confuse with classic tabular `igel fit`. |
| `StructuredDataRegression` | `autokeras.StructuredDataRegressor` | Registered selector; no repo-shipped dedicated structured-data AutoKeras loader/example. |

`Models.get` raises an exception for any unsupported task string and includes the supported keys in the message.

## `IgelCNN` constructor and dispatch

`IgelCNN(**cli_args)` records command/config/data inputs and immediately dispatches to a method named by `cmd` via `getattr(self, self.cmd)()`. Important arguments:

| Argument | Used when | Meaning |
| --- | --- | --- |
| `cmd` | all modes | Must match an implemented method such as `train`, `evaluate`, or `predict`; invalid commands fail during dispatch. |
| `data_path` | train/evaluate/predict | Directory used by the current loader. The current implementation calls `autokeras.image_dataset_from_directory(data_path)`. |
| `task` | train | Task string used when no config file is supplied, or used to override the config's `model.type`. |
| `yaml_path` | train | Optional YAML/JSON config. Extension must be `.yaml`, `.yml`, or `.json`. |
| `model_path` | non-train init | Accepted as a pre-fitted model path argument, but `load_model()` currently loads from `model` in the current working directory. |
| `description_file` | evaluate/predict | JSON file that stores the task and dataset properties from training. Defaults to the package's `model_results/description.json` convention. |
| `prediction_file` | predict init | Accepted from defaults, but current `predict()` returns Keras predictions and does not write a prediction file itself. |

When `cmd == "train"`:

1. If `yaml_path` is omitted, `model_type` is taken from `task`.
2. If `yaml_path` is supplied, the file must be YAML or JSON. `dataset`, `model`, and `training` sections are read when present.
3. `model_type` becomes `task` if provided, otherwise `model.type` from the config.
4. `model.arguments` becomes constructor kwargs for the AutoKeras class.
5. `training` becomes kwargs for `model.fit(...)`.

When `cmd != "train"`, the constructor reads `description_file`, recovers `task` and `dataset_props`, and then dispatches to `evaluate()` or `predict()`.

## Method behavior

| Method | Behavior | Operational caveats |
| --- | --- | --- |
| `_create_model()` | Calls `Models.get(self.model_type)`, then instantiates the selected AutoKeras class with `model.arguments` when provided. | It does not validate data layout or tune budget; validate those before training. |
| `train()` | Builds `train_data = ak.image_dataset_from_directory(data_path)`, fits the AutoKeras model with `training_args`, writes a description JSON, and saves the exported model. | This is the concrete implemented loader path. Treat text/structured task names as selector support unless the installed version proves additional loaders. |
| `save_desc_file()` | Writes JSON with `task`, model class name, `dataset_props`, and `model_props`. | The default description path follows the package's `model_results/description.json` convention. Ensure the directory exists when running outside helper code that creates it. |
| `save_model()` | Calls `model.export_model()`, then tries to save TensorFlow SavedModel format to `model/`; if that fails, saves `model.h5`. | Artifacts are written relative to the current working directory. Move/copy both description and model artifacts together. |
| `load_model()` | Loads TensorFlow SavedModel from `model/` using `tensorflow.keras.models.load_model(..., custom_objects=ak.CUSTOM_OBJECTS)`. | It does not use `model_path` for the actual load path in the current implementation. |
| `evaluate()` | Loads the saved model, builds test data with `ak.image_dataset_from_directory(data_path)`, and calls `trained_model.evaluate(test_data)`. | Requires the `model/` SavedModel path and description JSON expected by init. |
| `predict()` | Loads the saved model, builds prediction data with `ak.image_dataset_from_directory(data_path)`, and calls `trained_model.predict(pred_data)`. | The method does not persist predictions by itself. |

## CLI caveat

The docs describe commands such as `igel auto-train --data_path ... --task ImageClassification` and `igel auto-train -dp ...`. The current Click CLI does not define an `auto-train` command. Future agents should not send users down that CLI path unless a newer installed version proves the command exists. Use the programmatic `IgelCNN` path for Auto-ML, or route classic CLI operations to [tabular-workflows](../../tabular-workflows/SKILL.md).
