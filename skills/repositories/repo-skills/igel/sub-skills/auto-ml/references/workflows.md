# Auto-ML Workflows

These workflows are safe operating patterns for Igel's AutoKeras path. They intentionally avoid dataset downloads and long training loops by default.

## 1. Inspect before training

Before promising an Auto-ML run, verify the installed environment and task selector:

```bash
python sub-skills/auto-ml/scripts/inspect_auto_ml.py
python sub-skills/auto-ml/scripts/inspect_auto_ml.py --task ImageClassification
```

The helper imports TensorFlow, AutoKeras, and `igel.auto`, prints the `IgelCNN` signature and supported task names when available, and does not train or read data.

## 2. Choose the correct route

- Use this sub-skill for `IgelCNN`, AutoKeras task names, image/text/structured AutoKeras questions, and Auto-ML save/load behavior.
- Use [tabular-workflows](../../tabular-workflows/SKILL.md) for classic CSV-oriented `igel fit`, `evaluate`, `predict`, `experiment`, model catalogs, metrics, and ONNX/export.
- Use the [root router](../../../SKILL.md) when the user is not explicit about Auto-ML versus classic Igel workflows.

## 3. Image directory workflow

The concrete implemented `IgelCNN.train/evaluate/predict` path calls `autokeras.image_dataset_from_directory(data_path)`. For image classification, arrange a parent directory with one subdirectory per class:

```text
images/
  cat/
    cat_001.jpg
    cat_002.jpg
  dog/
    dog_001.jpg
    dog_002.jpg
```

Minimal programmatic pattern:

```python
from igel.auto import IgelCNN

# Train. This starts an AutoKeras search, so keep data and trial count bounded.
IgelCNN(cmd="train", data_path="images", task="ImageClassification")

# Evaluate or predict after training from a working directory containing the saved model artifacts.
IgelCNN(cmd="evaluate", data_path="eval_images", description_file="model_results/description.json")
IgelCNN(cmd="predict", data_path="predict_images", description_file="model_results/description.json")
```

For bounded testing, prefer a tiny local fixture and a config with a small `max_trials` and epoch count. The distilled example schema is:

```yaml
model:
  type: ImageClassification
  arguments:
    max_trials: 1
training:
  epochs: 1
```

Then pass the config with `yaml_path="igel.yaml"` and optionally override with `task="ImageClassification"`.

## 4. Text directory workflow caveat

The docs describe text classification with class-labeled subfolders, analogous to the image layout:

```text
texts/
  negative/
    review_001.txt
  positive/
    review_002.txt
```

The model registry includes `TextClassification` and `TextRegression`, but the current `IgelCNN` implementation still builds datasets via `ak.image_dataset_from_directory(...)`. Treat text Auto-ML as registered task-selector support plus documented intent, not as a verified turnkey end-to-end loader, unless the installed version you are using proves otherwise.

Recommended response when a user asks for text Auto-ML:

1. Confirm they mean the AutoKeras path, not classic tabular text features.
2. Run the inspection helper and resolve the task string.
3. Warn that the current repo evidence lacks a dedicated text loader/CLI and that the docs' `auto-train` command is absent.
4. If they need a supported production path today, either use raw AutoKeras directly or route classic feature-engineered data to [tabular-workflows](../../tabular-workflows/SKILL.md).

## 5. Structured-data task-selector workflow caveat

`StructuredDataClassification` and `StructuredDataRegression` are registered in `Models.get`, but the repository does not ship a separate structured-data AutoKeras loader or example. Do not confuse these AutoKeras task names with Igel's classic structured/tabular CSV workflow.

Recommended response when a user asks for structured-data AutoKeras:

1. Explain that the selector maps the task name to AutoKeras' structured-data class.
2. Explain that the current `IgelCNN` train/evaluate/predict methods do not provide a dedicated structured-data loader.
3. Route everyday CSV `fit/evaluate/predict` to [tabular-workflows](../../tabular-workflows/SKILL.md).
4. If the user explicitly wants AutoKeras structured-data training, bound the run, verify the installed package version, and avoid claiming support beyond what the environment proves.

## 6. Save/load workflow

A successful `IgelCNN.train()` run writes two kinds of artifacts:

- description JSON, normally under the package's `model_results/description.json` convention;
- exported TensorFlow model artifacts in `model/`, or `model.h5` if SavedModel export fails.

`evaluate()` and `predict()` read the description file during initialization and then load `model/` from the current working directory with AutoKeras custom objects. Keep the working directory and artifact paths stable, or pass an explicit `description_file` and ensure the `model/` path is present where the process runs.

## 7. CLI workflow caveat

The public docs show commands like:

```bash
igel auto-train --data_path path_to_images --task ImageClassification
```

The current Click CLI does not expose `auto-train`. Do not troubleshoot user typos for a command that is missing from this version. Use the programmatic `IgelCNN` path above or route non-AutoKeras commands to the classic workflow skill.
