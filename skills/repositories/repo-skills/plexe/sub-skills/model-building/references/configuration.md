# Plexe configuration

This reference lists the runtime settings that matter most when using Plexe from the CLI
or Python API.

## Configuration sources and precedence

Plexe builds its config from these sources, in order:

1. Explicit CLI/API arguments
2. Environment variables
3. YAML file pointed to by `CONFIG_FILE`
4. Field defaults

A YAML file may interpolate `${VAR_NAME}` references from the environment.

## Main CLI flags

| Flag | Meaning |
| --- | --- |
| `--train-dataset-uri` | Required training dataset path or URI |
| `--val-dataset-uri` | Optional validation dataset |
| `--test-dataset-uri` | Optional test dataset |
| `--intent` | Natural-language description of the task |
| `--experiment-id` | Experiment identifier |
| `--user-id` | User identifier |
| `--work-dir` | Working directory |
| `--max-iterations` | Search iterations |
| `--seed` | Global seed |
| `--spark-mode` | `local` or `databricks` |
| `--allowed-model-types` | Restrict model families |
| `--is-retrain` | Switch to retraining mode |
| `--original-model-uri` | Packaged model to retrain |
| `--original-experiment-id` | Experiment ID to resolve the original package |
| `--enable-final-evaluation` | Force test-set evaluation |
| `--nn-default-epochs` | Default epochs for Keras/PyTorch |
| `--nn-max-epochs` | Upper epoch cap for Keras/PyTorch |
| `--external-storage-uri` | S3 location for intermediate artifacts |
| `--enable-otel` | Enable OpenTelemetry |
| `--otel-endpoint` | OTLP endpoint |
| `--otel-header` | Repeatable `KEY=VALUE` OTLP header |
| `--config-file` | YAML config file path |
| `--csv-delimiter` | CSV delimiter, including `tab` |
| `--csv-header` | Whether CSV files include a header row |

## Important config fields

| Field | Default | Notes |
| --- | --- | --- |
| `max_search_iterations` | 10 | Main search budget |
| `max_parallel_variants` | 3 | Variant concurrency |
| `training_timeout` | 1800 | Training timeout in seconds |
| `nn_default_epochs` | 10 | Default Keras/PyTorch epochs |
| `nn_max_epochs` | 50 | Cap for neural-network epochs |
| `nn_default_batch_size` | 32 | Default batch size |
| `mixed_precision` | true | Auto-disables on CPU-only runs |
| `dataloader_workers` | 4 | Streaming data-loader workers |
| `train_sample_size` | 30000 | Sampling budget for training split |
| `val_sample_size` | 10000 | Sampling budget for validation split |
| `spark_mode` | `local` | Spark backend |
| `spark_local_cores` | 8 | Local Spark worker threads |
| `spark_driver_memory` | `8g` | Local Spark driver memory |
| `csv_delimiter` | `,` | CSV parsing delimiter |
| `csv_header` | `true` | CSV header row flag |
| `allowed_model_types` | `null` | Restrict to specific model families |
| `enable_otel` | `false` | OpenTelemetry toggle |

## Allowed model families

Plexe recognizes these model families in the tabular workflow:

- `xgboost`
- `catboost`
- `lightgbm`
- `keras`
- `pytorch`

The data-layout logic may filter that set further. For example, image and text layouts
only keep Keras and PyTorch.

## Spark and backend settings

### Local Spark

- `spark_mode=local`
- `spark_local_cores`
- `spark_driver_memory`

Local Spark requires Java 17+ and the PySpark extra.

### Databricks Connect

- `spark_mode=databricks`
- `databricks_use_serverless`
- `databricks_cluster_id`
- `databricks_host`
- `databricks_token`
- `databricks_profile`

The Databricks path requires the Databricks Connect extra.

## Environment variables worth knowing

| Variable | Purpose |
| --- | --- |
| `CONFIG_FILE` | YAML config file path |
| `USER_ID` | Default user id for the CLI |
| `EXPERIMENT_ID` | Default experiment id for the CLI |
| `KERAS_BACKEND` | Must be `tensorflow` before Keras imports |
| `OTEL_EXPORTER_OTLP_ENDPOINT` | Alternative OTLP endpoint source |
| `OTEL_EXPORTER_OTLP_HEADERS` | Comma-separated OTLP headers |
| `OPENAI_API_KEY` | Example provider credential |
| `ANTHROPIC_API_KEY` | Example provider credential |

## LiteLLM routing

Plexe can route agent calls through custom provider definitions:

- `routing_config.default`
- `routing_config.providers`
- `routing_config.models`

Use `get_routing_for_model()` when you need to resolve the effective API base and headers
for a given model id.

## Example YAML

```yaml
max_search_iterations: 5
max_parallel_variants: 2
spark_mode: local
spark_local_cores: 2
spark_driver_memory: "4g"
allowed_model_types: [xgboost, lightgbm]
train_sample_size: 10000
val_sample_size: 3000
```

## Validation rules to remember

- `nn_default_epochs` must not exceed `nn_max_epochs`.
- `RoutingConfig.models` must point to provider names that exist in `providers`.
- `agent_verbosity_level` is clamped to the range 0-2.
- Unknown YAML fields are ignored.

