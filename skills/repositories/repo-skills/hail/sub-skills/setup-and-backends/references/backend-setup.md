# Backend Setup

This reference covers Hail Query setup: install/import checks, backend choice, minimal initialization patterns, safe shutdown, and tmp/log/reference/requester-pays configuration.

## Installation and Import Baseline

- Install the Python distribution named `hail`; it provides the `hail` and `hailtop` import packages and the `hailctl` console command.
- Use Python `>=3.10`. The inspected package version is `0.2.138`; future refreshes should re-check the installed version and signatures.
- Keep dependency constraints consistent with the package metadata: notable runtime requirements include `pyspark>=3.5,<3.6`, `numpy>=2,<3`, `pandas>=2,<3`, `scipy>1.13,<2`, `bokeh>3.8.2,<4`, and the `hailtop` dependency set.
- Install Java 11 before local or Spark backend startup. Hail warns on other Java feature versions and those versions are unsupported for reliable setup.
- Work from a neutral directory. A source checkout or a local folder named `hail` can make `import hail` partially succeed while generated version modules or packaged backend assets are missing.
- Use a complete installed wheel/package for runtime work. Raw source trees can lack generated `version.py` modules and the bundled backend JAR assets needed by `hl.init`.

Minimal import probe:

```python
import hail as hl
import hailtop

print(hl.version())
```

If the import probe fails, fix installation or import shadowing before debugging any backend-specific failure.

## Backend Choice Matrix

| Task shape | Preferred query backend | Minimal pattern | Notes |
| --- | --- | --- | --- |
| Local notebook exploration, small examples, local ETL, or setup smoke checks | `local` | `hl.init(backend='local')` or `hl.init_local()` | Starts a local JVM backend through Py4J. Use `jvm_heap_size` or `HAIL_LOCAL_BACKEND_HEAP_SIZE` when local memory is the constraint. |
| Spark cluster jobs, local Spark execution, Spark SQL interop, or an existing SparkContext | `spark` | `hl.init(backend='spark', ...)` or `hl.init_spark(...)` | Requires PySpark/Spark 3.5.x. Existing SparkContexts must already include Hail JAR/classpath settings because Hail cannot retrofit every Spark option after context creation. |
| Hail Query execution through Hail Batch service | `batch` | `hl.init(backend='batch', ...)` or `await hl.init_batch(...)` | Requires Hail Batch authentication, billing project, remote tmpdir, and usually region/cloud configuration. This is not the same as authoring `hailtop.batch` DAGs. |

`hl.init` selects a backend in this order:

1. explicit `backend=` argument,
2. `HAIL_QUERY_BACKEND`,
3. `hailctl config get query/backend`,
4. default `spark`.

The public backend choices are `local`, `spark`, and `batch`. Some older internals or errors may say `service`; use `batch` in new user-facing code.

## Minimal Initialization Patterns

Local single-node initialization:

```python
import hail as hl

hl.init(
    backend='local',
    quiet=True,
    log='hail-local.log',
    tmp_dir='file:///tmp/hail-query',
    local_tmpdir='file:///tmp/hail-local',
)
try:
    print(type(hl.current_backend()).__name__)
finally:
    hl.stop()
```

Local backend with explicit JVM heap:

```python
import hail as hl

hl.init_local(
    quiet=True,
    jvm_heap_size='4g',
    tmpdir='file:///tmp/hail-query',
)
try:
    # Hail Table/MatrixTable work goes here.
    pass
finally:
    hl.stop()
```

Spark backend with Hail-managed local Spark:

```python
import hail as hl

hl.init(
    backend='spark',
    app_name='hail-etl',
    master='local[*]',
    spark_conf={'spark.sql.shuffle.partitions': '32'},
    tmp_dir='file:///tmp/hail-query',
    local_tmpdir='file:///tmp/hail-spark-local',
    show_progress=True,
)
try:
    print(type(hl.current_backend()).__name__)
finally:
    hl.stop()
```

Spark backend with an existing SparkContext:

```python
import hail as hl

# The existing SparkContext must already have Hail JAR and classpath settings.
hl.init(sc=sc, backend='spark', quiet=True)
try:
    pass
finally:
    hl.stop()
```

Batch query backend:

```python
import hail as hl

hl.init(
    backend='batch',
    app_name='hail-query',
    tmp_dir='gs://YOUR-BUCKET/hail-query/tmp/',
    driver_cores=1,
    worker_cores=1,
    regions=['us-central1'],
    gcs_requester_pays_configuration='YOUR-GCP-PROJECT',
)
try:
    pass
finally:
    hl.stop()
```

Use `hl.init(backend='batch', ...)` in ordinary scripts. Call `hl.init_batch(...)` directly only in async-aware code that can `await` the coroutine.

## Tmp, Log, Reference, and Progress Options

- `log` is a local filesystem path. If omitted, Hail uses `HAIL_LOG_DIR` when set, otherwise the current directory, with a timestamped `hail-<version>.log` filename.
- `append=True` appends to an existing log file; otherwise the log starts fresh.
- `tmp_dir` on `hl.init` and `tmpdir` on backend-specific init are Hail's shared temporary directory. It must be visible to the selected backend: local paths for local work, paths visible to all Spark workers for Spark, and cloud/object-storage paths for Batch service execution.
- `local_tmpdir` is driver/executor local scratch for Spark and defaults through `TMPDIR` to `file:///tmp`. If a URI scheme is present, it must be `file://`.
- `default_reference` defaults to `GRCh37`; built-ins include `GRCh37`, `GRCh38`, `GRCm38`, and `CanFam3`. In `hl.init`, this argument is deprecated in favor of setting `hl.default_reference(...)` after initialization, but it remains in the verified signature.
- `show_progress` applies to Spark and Batch progress display. It can also be influenced by `query/disable_progress_bar` or `HAIL_QUERY_DISABLE_PROGRESS_BAR`.
- `global_seed` sets deterministic Hail randomness for the initialized session.

## Requester-Pays and Cloud Access

Prefer explicit initialization parameters in reproducible code:

```python
hl.init(
    backend='spark',
    gcs_requester_pays_configuration='YOUR-GCP-PROJECT',
)

hl.init(
    backend='batch',
    gcs_requester_pays_configuration=('YOUR-GCP-PROJECT', ['bucket-a', 'bucket-b']),
)
```

Equivalent user-level settings can be managed with:

```bash
hailctl config set gcs_requester_pays/project YOUR-GCP-PROJECT
hailctl config set gcs_requester_pays/buckets bucket-a,bucket-b
```

Use `gcs_bucket_allow_list` only when Hail refuses access because a bucket's default policy is cold storage; match the shape accepted by the exact init path being called and use bucket names rather than `gs://` URIs. Configuration precedence is explicit `hl.init` arguments, then shell environment variables such as `HAIL_GCS_REQUESTER_PAYS_PROJECT`, then `hailctl config`, then defaults. Some cloud settings are shared between Hail Query and Hail Batch, so route broader CLI configuration and Batch DAG billing to [Batch and CLI](../../batch-and-cli/SKILL.md).

## Batch Query Setup Notes

Batch query initialization needs at least a Hail Batch billing project and remote temporary directory. These may come from explicit arguments where supported or from `hailctl config`:

```bash
hailctl config set batch/billing_project YOUR-HAIL-BATCH-BILLING-PROJECT
hailctl config set batch/remote_tmpdir gs://YOUR-BUCKET/hail-query-temporaries/
hailctl config set query/backend batch
```

Use placeholders in reusable instructions. Do not embed credentials, tokens, private bucket names, or billing identifiers in generated examples.

## Shutdown and Reinitialization

- Call `hl.stop()` at the end of scripts, notebooks, and tests that initialize Hail.
- `hl.stop()` clears the active Hail context and backend. Hail-managed Spark sessions are stopped; externally supplied Spark contexts are not fully owned by Hail.
- Call `hl.stop()` before changing backend, `spark_conf`, `master`, tmp/log locations, requester-pays settings, or default reference in the same Python process.
- Use `hl.init(idempotent=True)` only when repeated setup calls should become no-ops if Hail is already initialized. It will not apply new configuration to an existing context.
- `hl.current_backend()` and `hl.debug_info()` are post-init introspection helpers. Avoid using them as pure pre-init probes because some Hail helpers can trigger default initialization.

## Bundled Diagnostic

Use the root diagnostic script [check_hail_environment.py](../../../scripts/check_hail_environment.py) before backend debugging. Treat it as a read-only environment probe for import source, version metadata, Python version, Java, PySpark, packaged JAR assets, `hailctl` presence, and backend configuration signals before attempting expensive initialization.
