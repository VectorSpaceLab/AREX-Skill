# Plexe model-building troubleshooting

This file covers workflow-specific failures for the main Plexe build, resume, and retrain
paths. For cross-cutting install and backend issues, see the root
[`../../../references/troubleshooting.md`](../../../references/troubleshooting.md).

## Entry-point and config failures

### `train_dataset_uri is required`

Cause:

- The caller omitted `--train-dataset-uri` and did not supply deprecated `data_refs`.

Fix:

- Pass `--train-dataset-uri` or update the Python caller to set `train_dataset_uri=`.

### Deprecated `data_refs` warnings

Cause:

- A caller still passes dataset references through the deprecated fallback.

Fix:

- Migrate to `train_dataset_uri`.
- Keep only the first element if you are still using the fallback for compatibility.

### `nn_default_epochs must be <= nn_max_epochs`

Cause:

- The config override lowered the maximum below the default.

Fix:

- Set both values explicitly so the default remains within the cap.

## Layout and data-shape failures

### `Dataset layout is not supported`

Cause:

- The dataset does not match one of Plexe's supported layouts.

Fix:

- Restructure the data to a supported shape:
  - `flat_numeric`
  - `image_path`
  - `text_string`

### `No compatible model types for task`

Cause:

- `allowed_model_types` conflicts with the detected layout.

Fix:

- Remove the restrictive filter.
- Or choose a compatible set of model families for the detected layout.

### `Target column not found in new data`

Cause:

- Retraining data is missing the original target column.

Fix:

- Make sure the new data uses the same target column name as the original model.

## Spark and backend failures

### `Java 17+ is required for PySpark 3.5+`

Cause:

- The local backend does not have the required JVM.

Fix:

- Install Java 17.
- Re-run the environment smoke check with `--spark`.

### `databricks-connect is not installed`

Cause:

- The Databricks backend was selected without the Databricks extra.

Fix:

- Install `plexe[databricks]` only when you need the remote Databricks path.

### `Unsupported storage URI scheme`

Cause:

- `StandaloneIntegration` only supports local paths and `s3://` URIs.

Fix:

- Use `s3://` for standalone cloud storage.
- For Azure or GCS, implement a custom `WorkflowIntegration`.

### `S3 dataset requires --external-storage-uri`

Cause:

- Input data lives in S3, but the workflow has no external storage prefix for artifacts.

Fix:

- Provide `--external-storage-uri s3://bucket/prefix`.
- Confirm the AWS identity can write to that prefix.

## Resume and checkpoint failures

### `No model types remain after applying allowed_model_types on resume`

Cause:

- The resumed checkpoint's viable model families do not intersect the new filter.

Fix:

- Remove the filter or start a fresh run.
- If you need the filter, choose families already present in the checkpoint.

### `Cannot resume after Phase 4 without valid SearchJournal`

Cause:

- The workflow tried to resume from a search checkpoint that did not contain a valid journal.

Fix:

- Re-run the missing phase or start a fresh build.
- Check that the checkpoint file was not deleted or corrupted.

### `No successful solutions found during search`

Cause:

- Every explored solution was buggy or failed to train.

Fix:

- Inspect the search journal and the training logs.
- Relax the model filter or adjust the data layout if the search space is too narrow.

## Evaluation failures

### Evaluation falls back to validation performance

Cause:

- Final test evaluation failed or was skipped.

Fix:

- Check the evaluation report for the error path.
- If the test split was missing, provide one or let Plexe generate it.

### `Metric requires probability scores`

Cause:

- The chosen metric expects probabilities but the predictor does not implement `predict_proba()`.

Fix:

- Use a classifier that exposes probabilities.
- Confirm the model family can emit `predict_proba()` for the chosen task.

### `predict_proba() is only valid for classification tasks`

Cause:

- A probability metric was used for a regression task.

Fix:

- Switch to a regression-compatible metric.
- Or change the task to a classification problem if that was the intent.

## Retraining failures

### `Model metadata not found`

Cause:

- The original package does not contain `artifacts/metadata.json`.

Fix:

- Use a package built by the current retraining-aware workflow.

### `Training code not found in package`

Cause:

- The original package predates retraining support or is incomplete.

Fix:

- Rebuild the original model with retraining support enabled.

### `Pipeline code not found`

Cause:

- `src/pipeline.py` is missing from the original package.

Fix:

- Repackage the original model and include the feature pipeline.

### Unsupported model type during retraining

Cause:

- The original package advertises a model family Plexe does not know how to recreate.

Fix:

- Restrict retraining to supported model families.
- Inspect the package metadata before retraining.

## Model-family-specific failures

### Keras complaints about backend or model shape

Cause:

- `KERAS_BACKEND` was not set before import.
- The model output shape does not match the task type.

Fix:

- Set `KERAS_BACKEND=tensorflow` before importing Keras code.
- Make sure the output dimension matches the classification or regression task.

### PyTorch complaints about DDP or CUDA

Cause:

- `--ddp` was enabled without CUDA.
- Mixed precision was requested on a CPU-only machine.

Fix:

- Remove `--ddp` on CPU.
- Only use mixed precision when a CUDA device is available.

### CatBoost or LightGBM label encoding issues

Cause:

- The labels are not contiguous or start at 0.

Fix:

- Let the workflow apply label encoding.
- Confirm the training labels are compatible with the chosen classifier.

## Packaging and artifact failures

### Packaged model exists but the dashboard shows no package

Cause:

- The model package was written to a different workdir than the one being inspected.

Fix:

- Check the experiment path and the dashboard workdir root.
- Use the workdir inspector script to confirm the package location.

### The package lacks `predictor.py` or `model.yaml`

Cause:

- Packaging did not complete cleanly.

Fix:

- Review the checkpoint and evaluation logs.
- Re-run the workflow or inspect the failure in the final packaging phase.

## Practical recovery order

1. Check the config and dataset shape.
2. Verify Spark/Java or Databricks backend prerequisites.
3. Verify provider credentials and routing if the workflow needs agent calls.
4. Re-check the checkpoint and model-package files.
5. Use `scripts/inspect_workdir.py` to confirm what was actually written.

