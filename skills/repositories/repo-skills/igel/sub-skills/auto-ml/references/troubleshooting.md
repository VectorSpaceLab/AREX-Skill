# Auto-ML Troubleshooting

Use this reference when Igel Auto-ML import checks, task selection, data layout, model artifacts, or CLI expectations fail.

## Missing TensorFlow, AutoKeras, or package imports

Symptoms:

- `ModuleNotFoundError: No module named 'tensorflow'`
- `ModuleNotFoundError: No module named 'autokeras'`
- `import igel.auto` fails before reaching `IgelCNN`
- TensorFlow imports but reports CPU-only execution

What to do:

1. Run the safe helper:

   ```bash
   python sub-skills/auto-ml/scripts/inspect_auto_ml.py
   ```

2. Install/activate an environment with Igel's runtime dependency stack, including TensorFlow and AutoKeras. A failure in a non-AutoML dependency can still break `igel.auto` because importing a Python subpackage executes the top-level package initializer first.
3. CPU-only TensorFlow is acceptable for import/signature checks and small CPU smoke tests. Do not claim GPU acceleration unless the environment reports a usable GPU and the run actually uses it.
4. Do not start AutoKeras training to test imports; imports and task-selector checks are enough for this failure class.

## Unsupported task names

`Models.get` supports only these exact names:

- `ImageClassification`
- `ImageRegression`
- `TextClassification`
- `TextRegression`
- `StructuredDataClassification`
- `StructuredDataRegression`

The selector is case-sensitive in practice because it checks dictionary keys. If a user supplies `image_classification`, `image classification`, `image-classification`, `classification`, or lowercase names, normalize only after confirming the intended task, then use the exact PascalCase string.

Safe check:

```bash
python sub-skills/auto-ml/scripts/inspect_auto_ml.py --task ImageClassification
python sub-skills/auto-ml/scripts/inspect_auto_ml.py --task NotATask
```

The first command should resolve to an AutoKeras class in a correctly installed environment; the second should fail cleanly and list the supported names.

## Unsupported or malformed directory layouts

The implemented `IgelCNN` train/evaluate/predict path currently uses `autokeras.image_dataset_from_directory(data_path)`. For image classification, the expected shape is:

```text
parent_dir/
  class_a/
    sample_001.jpg
  class_b/
    sample_002.jpg
```

For text classification, the docs describe the same class-subfolder idea with text files, but the current implementation does not expose a text-specific dataset loader. Treat text layouts as documented intent and task-selector support until the installed version proves end-to-end behavior.

Common layout failures:

- files placed directly under the parent directory with no class subfolders;
- one class folder only when the task is classification;
- empty class folders;
- non-image files on the current image-loader path;
- structured CSV/Parquet-like data sent to Auto-ML when the user actually needs classic tabular Igel.

Route classic CSV/structured data to [tabular-workflows](../../tabular-workflows/SKILL.md).

## Long training or download cost

AutoKeras searches candidate models and can run for a long time. Training examples may also trigger dataset downloads if copied from generic AutoKeras examples. For this skill:

- default to `inspect_auto_ml.py` and task-selector checks;
- avoid the original example script as a runtime helper because it loads MNIST and trains immediately;
- if a bounded train smoke is explicitly approved, use a tiny local fixture, `max_trials: 1`, and very few epochs;
- document CPU-only runs as slow and do not imply they represent production search quality.

## Model save/load assumptions

Symptoms:

- `description.json` or `model_results/description.json` is missing;
- `load_model("model", custom_objects=ak.CUSTOM_OBJECTS)` cannot find the model;
- `evaluate()` or `predict()` fails after moving artifacts to another directory;
- predictions run but are not written to the expected `predictions.csv` file.

What to know:

- `save_desc_file()` writes task/model/dataset/model metadata to the description file path.
- `save_model()` exports the best AutoKeras model and saves `model/` in TensorFlow SavedModel format, or `model.h5` if that save fails.
- `load_model()` currently loads from the literal `model` path in the current working directory.
- `predict()` calls the loaded model's `predict(...)` method; it does not persist a prediction CSV by itself.

Keep the training/evaluation/prediction working directory consistent, copy description and model artifacts together, and verify paths before diagnosing model-quality issues.

## Docs/source mismatch: missing `igel auto-train`

The docs mention `igel auto-train --data_path ... --task ImageClassification` and similar text-classification commands. The current Click CLI surface does not define `auto-train`; it defines classic commands such as `init`, `fit`, `evaluate`, `predict`, `experiment`, `export`, `serve`, `models`, `metrics`, `gui`, `help`, `version`, and `info`.

If a user reports `No such command 'auto-train'`:

1. Confirm they are using this Igel version rather than a newer one with a changed CLI.
2. Explain that this is a docs/source mismatch, not a user typo.
3. Use `IgelCNN` programmatically for AutoKeras guidance.
4. Route ordinary CLI `fit/evaluate/predict` to [tabular-workflows](../../tabular-workflows/SKILL.md).

## Boundary reminders

- ONNX/model export is not owned by Auto-ML; route it to the classic tabular workflow skill.
- FastAPI serving and HTTP clients are not owned by Auto-ML.
- Docker and GUI guidance are not owned by Auto-ML.
- The current Auto-ML skill should never require the original source checkout to answer runtime questions.
