# Configuration and Distributed Mode

## Purpose

Read this when you need the public `wr.config` surface, environment-variable overrides, or the Ray/Modin execution switches.

## Public configuration surface

The live package exposes these configuration names through `wr.config` and `wr.config.to_pandas()`:

- `catalog_id`
- `database`
- `workgroup`
- `chunksize`
- `concurrent_partitioning`
- `ctas_approach`
- `dtype_backend`
- `suppress_warnings`
- `athena_query_wait_polling_delay`
- `cloudwatch_query_wait_polling_delay`
- `neptune_load_wait_polling_delay`
- `timestream_batch_load_wait_polling_delay`
- `emr_serverless_job_wait_polling_delay`
- `s3_block_size`
- `s3_endpoint_url`
- `athena_endpoint_url`
- `sts_endpoint_url`
- `glue_endpoint_url`
- `redshift_endpoint_url`
- `kms_endpoint_url`
- `emr_endpoint_url`
- `dynamodb_endpoint_url`
- `secretsmanager_endpoint_url`
- `timestream_query_endpoint_url`
- `timestream_write_endpoint_url`
- `s3tables_catalog_endpoint_url`
- `botocore_config`
- `verify`
- distributed controls such as `address`, `redis_password`, `ignore_reinit_error`, `include_dashboard`, `configure_logging`, `log_to_driver`, `logging_level`, `object_store_memory`, `cpu_count`, and `gpu_count`

## Common usage patterns

```python
import awswrangler as wr

wr.config.database = "my_db"
wr.config.workgroup = "primary"
wr.config.reset("database")
wr.config.reset()
wr.config.to_pandas()
```

Environment-variable overrides use the same names with a `WR_` prefix:

- `WR_DATABASE`
- `WR_WORKGROUP`
- `WR_CATALOG_ID`
- `WR_ATHENA_QUERY_WAIT_POLLING_DELAY`
- `WR_CLOUDWATCH_QUERY_WAIT_POLLING_DELAY`
- `WR_S3_ENDPOINT_URL`
- `WR_ATHENA_ENDPOINT_URL`
- `WR_GLUE_ENDPOINT_URL`
- `WR_SECRETSMANAGER_ENDPOINT_URL`
- and the rest of the `wr.config` names listed above

## Distributed mode

If `ray` and `modin` are installed, the package can switch into distributed mode.
The public controls are:

```python
import awswrangler as wr

wr.engine.get()
wr.engine.set("python")
wr.engine.set("ray")
wr.memory_format.get()
wr.memory_format.set("pandas")
wr.memory_format.set("modin")
```

Important runtime facts:

- The default installed mode in a plain environment is `python` + `pandas`.
- `WR_ENGINE` and `WR_MEMORY_FORMAT` can seed the mode before first use.
- `WR_ADDRESS` points the Ray runtime at a remote cluster when one exists.
- Distributed mode changes behavior in selected `wr.s3`, `wr.athena`, `wr.dynamodb`, `wr.neptune`, and `wr.timestream` paths, so route feature questions back to the owning service sub-skill after the mode is settled.

## Verification hints

- `wr.engine.get_installed()` and `wr.memory_format.get_installed()` tell you what is actually available in the current environment.
- `wr.config.to_pandas()` is the fastest way to confirm which defaults are already loaded.
- The shared `scripts/check_runtime.py` helper prints both runtime mode and a redacted config table.
