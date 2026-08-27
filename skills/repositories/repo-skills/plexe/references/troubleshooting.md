# Plexe Troubleshooting

Cross-cutting Plexe issues that show up before the workflow-specific references.
Use this file for install, backend, provider, and general runtime failures.
For phase-specific or dashboard-specific problems, jump to the nearest sub-skill
troubleshooting reference.

## Install and import problems

### `ImportError` on `plexe` or one of its runtime modules

Likely causes:

- The package is not installed in the active environment.
- Optional extras such as Spark, dashboard, or model-framework dependencies are missing.
- The interpreter is older than Python 3.10 or newer than 3.12.

What to do:

- Install the core package first: `pip install plexe`
- Add the extras you actually need: `pip install "plexe[pyspark,aws,catboost,lightgbm,pytorch]" streamlit plotly`
- Re-run the bundled smoke check: `scripts/check_env.py --cli --dashboard`

### `pip check` reports broken requirements

Likely causes:

- Mixing an old environment with a newer Plexe install.
- Partial installation of optional model packages.
- Incompatible TensorFlow, PyTorch, or Spark wheels.

What to do:

- Prefer a fresh private environment for Plexe inspection.
- Reinstall only the extras needed for the chosen workflow.
- Run `scripts/check_env.py --all` after reinstalling.

## Provider and agent runtime problems

### Missing API keys or LiteLLM provider errors

Likely causes:

- The workflow uses model-selection and search agents, but no provider credentials are set.
- The routing config points at a provider name that does not exist.
- The provider key is present, but the model name is invalid for that provider.

What to do:

- Set the provider credentials required by your routing choice.
- If you use custom routing, verify the model-to-provider mapping in `routing_config`.
- Check `plexe/config.py` for the accepted routing structure.

### OpenTelemetry settings fail at startup

Likely causes:

- Malformed OTLP headers.
- Invalid endpoint URL.
- Environment variables override the YAML config unexpectedly.

What to do:

- Prefer a single source of truth for OTEL headers.
- Validate header syntax as `KEY=VALUE` pairs.
- Confirm `OTEL_EXPORTER_OTLP_ENDPOINT` and `OTEL_EXPORTER_OTLP_HEADERS` are correct.

## Spark and Java problems

### `Java 17+ is required for PySpark 4.0+`

Likely causes:

- The local environment has no Java runtime.
- A Java version older than 17 is installed.
- `spark-mode local` was selected without the required JVM.

What to do:

- Install Java 17 and make sure it is on `PATH`.
- Re-run `scripts/check_env.py --spark`.
- If you do not need local Spark, switch to a non-Spark path only when the workflow allows it.

### Spark session startup is slow or Maven downloads JARs every run

Likely causes:

- The environment has not cached the Hadoop/S3/Avro JARs yet.
- The Docker image or local setup does not preload Spark dependencies.

What to do:

- Expect the first local Spark start to be slower.
- Reuse the same private environment once the JARs have been resolved.
- If you are packaging a reusable environment, consider the PySpark extra.

### `databricks-connect is not installed`

Likely causes:

- The Databricks workflow is selected without the Databricks extra.

What to do:

- Install the Databricks extra only when you need the remote runtime.
- Re-check the host/token/profile/cluster settings in the configuration reference.

## Data, config, and backend problems

### `train_dataset_uri is required`

Likely causes:

- The CLI was called without a training dataset.
- Deprecated `data_refs` was not provided either.

What to do:

- Pass `--train-dataset-uri` or update the caller to supply `train_dataset_uri=`.
- Use the model-building workflow reference for accepted inputs.

### Unsupported dataset layout

Likely causes:

- The data does not match the supported layouts: flat numeric, image path, or text string.
- The dataset is multi-column structured data that Plexe cannot interpret as a supported layout.

What to do:

- Restructure the data or choose a different workflow.
- Review the supported layouts in `sub-skills/model-building/references/data-formats.md`.

### `No compatible model types for task`

Likely causes:

- `allowed_model_types` conflicts with the detected data layout.
- The dataset layout only allows a subset of the available frameworks.

What to do:

- Remove the restrictive filter or choose a compatible model family.
- Check the model-building data-formats reference for layout-to-model mapping.

### `No model types remain after applying allowed_model_types on resume`

Likely causes:

- The resumed checkpoint contains a model family that the new filter excludes.

What to do:

- Loosen the filter or start a new run.
- Confirm the checkpoint's viable model types before resuming.

### `nn_default_epochs must be <= nn_max_epochs`

Likely causes:

- A config override lowered the max epochs below the default value.

What to do:

- Set both values explicitly so the default does not exceed the cap.
- Use the configuration reference to check the precedence rules.

## Storage and backend problems

### `Unsupported storage URI scheme`

Likely causes:

- `StandaloneIntegration` was given an `az://` or `gs://` URI.
- The workflow expects S3-backed storage but the integration only supports local or `s3://`.

What to do:

- Use `s3://` with the standalone integration.
- For Azure or GCS, implement a custom `WorkflowIntegration`.

### `S3 dataset requires --external-storage-uri`

Likely causes:

- Input data lives in S3, but the workflow has no place to persist intermediate artifacts.

What to do:

- Provide `--external-storage-uri s3://...`.
- Make sure your credentials allow both read and write access.

### S3 download or upload failures

Likely causes:

- Missing AWS credentials or bucket permissions.
- Invalid S3 URI structure.
- Network access is blocked.

What to do:

- Check the URI format and your AWS credentials.
- Re-run the workflow after confirming read/write permissions.
- Use the S3 notes in the model-building troubleshooting reference for details.

## Keras and PyTorch backend problems

### Keras import or backend errors

Likely causes:

- Keras was imported before `KERAS_BACKEND=tensorflow` was set.
- TensorFlow is missing from the environment.

What to do:

- Set `KERAS_BACKEND=tensorflow` before importing Keras.
- Use the Keras-specific notes in the model-building troubleshooting reference.

### PyTorch training complains about CUDA or DDP

Likely causes:

- `--ddp` was enabled on a CPU-only machine.
- Mixed precision was requested without a CUDA device.

What to do:

- Remove `--ddp` for CPU training.
- Only enable mixed precision when CUDA is available.

## Dashboard and artifact discovery problems

- Empty dashboards, missing checkpoints, and malformed workdirs are covered in
  [`../sub-skills/dashboard/references/troubleshooting.md`](../sub-skills/dashboard/references/troubleshooting.md).
- Model package layout, retraining failures, and phase-specific workflow errors are covered in
  [`../sub-skills/model-building/references/troubleshooting.md`](../sub-skills/model-building/references/troubleshooting.md).

## Quick recovery checklist

1. Confirm the right extra set is installed for the chosen workflow.
2. Verify Python 3.10-3.12, Java 17, and Spark support if local Spark is needed.
3. Confirm provider credentials or routing config if the workflow needs agent calls.
4. Check the data layout and model-type filter before resuming or retraining.
5. Use the bundled smoke check or workdir inspector before opening the dashboard.

