# Setup and Backend API Reference

This reference lists the setup/backend APIs and configuration surfaces verified for the inspected `hail` distribution. Keep examples short; route workflow depth to [Backend Setup](backend-setup.md) and symptom recovery to [Troubleshooting](troubleshooting.md).

## Verified Public Signatures

| API | Verified signature |
| --- | --- |
| `hl.init` | `hl.init(sc=None, app_name=None, master=None, local=None, log=None, quiet=False, show_progress=None, append=False, min_block_size=None, branching_factor=50, tmp_dir=None, default_reference=None, idempotent=False, global_seed=None, spark_conf=None, skip_logging_configuration=False, local_tmpdir=None, *, backend=None, driver_cores=None, driver_memory=None, worker_cores=None, worker_memory=None, batch_id=None, max_read_parallelism=None, gcs_requester_pays_configuration=None, regions=None, gcs_bucket_allow_list=None, copy_spark_log_on_error=None, copy_log_on_error=None)` |
| `hl.init_local` | `hl.init_local(log=None, quiet=False, append=False, branching_factor=50, tmpdir=None, default_reference='GRCh37', global_seed=None, skip_logging_configuration=False, jvm_heap_size=None, requester_pays_config=None, copy_log_on_error=None)` |
| `hl.init_spark` | `hl.init_spark(sc=None, app_name=None, master=None, local=None, log=None, quiet=False, append=False, show_progress=None, min_block_size=None, branching_factor=50, tmp_dir=None, default_reference='GRCh37', global_seed=None, spark_conf=None, skip_logging_configuration=False, local_tmpdir=None, requester_pays_config=None, copy_log_on_error=False)` |
| `hl.init_batch` | `await hl.init_batch(*, billing_project=None, remote_tmpdir=None, log=None, quiet=False, append=False, tmpdir=None, default_reference='GRCh37', global_seed=None, show_progress=None, driver_cores=None, driver_memory=None, worker_cores=None, worker_memory=None, batch_id=None, name_prefix=None, token=None, requester_pays_config=None, regions=None, gcs_bucket_allow_list=None, branching_factor=None, max_read_parallelism=None)` |
| `hl.stop` | `hl.stop()` |

The installed package also exposes `hl.current_backend()`, `hl.debug_info()`, `hl.tmp_dir()`, `hl.default_reference(...)`, and `hl.get_reference(...)` for setup introspection and reference handling.

## `hl.init` Parameters by Concern

| Concern | Parameters | Notes |
| --- | --- | --- |
| Backend selection | `backend`, `sc`, `master`, `local`, `spark_conf`, `driver_cores`, `driver_memory`, `worker_cores`, `worker_memory`, `batch_id`, `max_read_parallelism`, `regions` | `backend` accepts `local`, `spark`, or `batch`. Spark-only parameters are ignored by local/Batch paths; Batch-only parameters require Hail Batch service configuration. |
| Logging and console output | `log`, `quiet`, `append`, `show_progress`, `skip_logging_configuration`, `copy_log_on_error`, `copy_spark_log_on_error` | `copy_spark_log_on_error` is deprecated in favor of `copy_log_on_error`; do not pass both. `log` is local filesystem output. |
| Temporary storage | `tmp_dir`, `local_tmpdir` | `tmp_dir` must be visible to the selected backend. `local_tmpdir` is local scratch for Spark driver/executors and must be plain local or `file://` when a scheme is present. |
| References and determinism | `default_reference`, `global_seed`, `branching_factor`, `min_block_size` | `default_reference` defaults to `GRCh37`; in `hl.init` it is deprecated in favor of `hl.default_reference(...)` after init. |
| Cloud/requester-pays | `gcs_requester_pays_configuration`, `gcs_bucket_allow_list` | Use a project string for all requester-pays GCS buckets or `(project, [bucket, ...])` for scoped buckets. Bucket allow-list shape differs between generic `hl.init` and direct Batch helpers; prefer verified examples. |

## Backend-Specific APIs

### `hl.init_local`

Use for single-node local work and quick setup smoke checks.

Important parameters:

- `tmpdir`: shared/local Hail scratch, defaulting to `/tmp` if omitted.
- `jvm_heap_size`: max heap passed to the local JVM; `HAIL_LOCAL_BACKEND_HEAP_SIZE` is the environment fallback.
- `requester_pays_config`: string project or `(project, [bucket, ...])` tuple for GCS requester-pays access.
- `copy_log_on_error`: attempts to copy relevant logs on local backend failures.

### `hl.init_spark`

Use for Spark-backed Hail Query execution.

Important parameters:

- `sc`: an existing `pyspark.SparkContext`; if supplied, it must already include Hail classpath/JAR configuration.
- `app_name`, `master`, `local`: Spark application and master/local-mode settings.
- `spark_conf`: Spark configuration dictionary applied before Hail creates Spark.
- `tmp_dir`: backend-visible shared scratch.
- `local_tmpdir`: local scratch mapped into Spark local directory behavior.
- `min_block_size`: sets minimum input split size in MB when provided.
- `requester_pays_config`: GCS requester-pays config for Spark-backed file access.

### `hl.init_batch`

Use for Query-on-Batch from async-aware code. For ordinary scripts, prefer `hl.init(backend='batch', ...)`.

Important parameters:

- `billing_project`: Hail Batch billing project. If omitted, Hail reads `batch/billing_project` configuration.
- `remote_tmpdir` / `tmpdir`: cloud/object-storage temporary path for Query-on-Batch intermediates.
- `driver_cores`, `driver_memory`, `worker_cores`, `worker_memory`: Query-on-Batch resource hints.
- `batch_id`: attach work to an existing Batch id when intentionally doing so.
- `name_prefix`: job/batch naming prefix; `hl.init(..., app_name=...)` maps to this path.
- `token`: credentials token for Batch client creation; prefer user-managed auth/config over hard-coded tokens.
- `regions`: allowed execution regions; defaults may come from Batch service/config.
- `gcs_bucket_allow_list`: list of bucket names for direct `hl.init_batch`; generic `hl.init` accepts a dictionary-shaped allow-list.

## Configuration Variables and Environment Names

`hailctl config` variables map to environment variables by uppercasing the section and option and prefixing `HAIL_`.

| Purpose | `hailctl config` variable | Environment variable |
| --- | --- | --- |
| Query backend | `query/backend` | `HAIL_QUERY_BACKEND` |
| Batch remote tmpdir | `batch/remote_tmpdir` | `HAIL_BATCH_REMOTE_TMPDIR` |
| Batch billing project | `batch/billing_project` | `HAIL_BATCH_BILLING_PROJECT` |
| Batch regions | `batch/regions` | `HAIL_BATCH_REGIONS` |
| Query Batch driver cores | `query/batch_driver_cores` | `HAIL_QUERY_BATCH_DRIVER_CORES` |
| Query Batch worker cores | `query/batch_worker_cores` | `HAIL_QUERY_BATCH_WORKER_CORES` |
| Query Batch driver memory | `query/batch_driver_memory` | `HAIL_QUERY_BATCH_DRIVER_MEMORY` |
| Query Batch worker memory | `query/batch_worker_memory` | `HAIL_QUERY_BATCH_WORKER_MEMORY` |
| Query name prefix | `query/name_prefix` | `HAIL_QUERY_NAME_PREFIX` |
| Disable progress bar | `query/disable_progress_bar` | `HAIL_QUERY_DISABLE_PROGRESS_BAR` |
| Requester-pays project | `gcs_requester_pays/project` | `HAIL_GCS_REQUESTER_PAYS_PROJECT` |
| Requester-pays buckets | `gcs_requester_pays/buckets` | `HAIL_GCS_REQUESTER_PAYS_BUCKETS` |
| GCS bucket allow-list | `gcs/bucket_allow_list` | `HAIL_GCS_BUCKET_ALLOW_LIST` |

Explicit Python arguments override environment variables, which override `hailctl config`, which override defaults.

## Introspection and Lifecycle Helpers

- `hl.stop()` stops the active Hail session if one is initialized. Use it before changing backend or init configuration in the same process.
- `hl.current_backend()` returns the active backend object after initialization. Use it for backend-aware branching only after explicit init.
- `hl.debug_info()` returns setup metadata such as Hail version, local JAR information, and backend-specific details. Treat paths from this output as private diagnostics.
- `hl.tmp_dir()` returns the active Hail shared temporary directory after initialization.
- `hl.default_reference()` returns the active default reference; `hl.default_reference(hl.get_reference('GRCh38'))` changes it after init.
- `hl.get_reference('default')` returns the current default reference. Built-in references include `GRCh37`, `GRCh38`, `GRCm38`, and `CanFam3`.

## Package and Asset Facts

- The distribution name is `hail`; verified imports include `hail`, `hailtop`, and `hailtop.batch`.
- The package metadata requires Python `>=3.10`.
- The package declares `hailctl = hailtop.hailctl.__main__:main` as its console script.
- Complete runtime packages should include `hail.backend` package data for `hail-all-spark.jar`. If this asset is absent, backend initialization can fail even when `import hail` succeeds.
