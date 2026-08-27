# Troubleshooting Setup and Backends

Use this reference when `import hail as hl` succeeds but `hl.init` fails, when a script selects an unexpected backend, or when package assets, Java/Spark/PySpark, tmp/log paths, requester-pays settings, or Batch query configuration behave unexpectedly.

## Fast Triage

1. Run or adapt the root diagnostic [check_hail_environment.py](../../../scripts/check_hail_environment.py) and inspect Python version, import location, package version, generated metadata, Java, PySpark, `hailctl`, backend configuration, and packaged JAR asset status.
2. Confirm the current directory and `PYTHONPATH` do not point to a source checkout or local directory that shadows the installed `hail` package.
3. Confirm Python is `>=3.10`, Java is 11, and PySpark/Spark are in the Hail-supported 3.5.x family when using local or Spark startup.
4. Choose the backend explicitly in the failing script: `backend='local'`, `backend='spark'`, or `backend='batch'`.
5. Use simple writable local paths for `log` and `local_tmpdir`, and a backend-visible `tmp_dir` while debugging.
6. Call `hl.stop()` before retrying changed backend or init configuration in the same Python process.

## Symptom Matrix

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `import hail as hl` works but `hl.version()` or metadata access fails | Python imported a source namespace or partial checkout instead of a complete installed package | Change to a neutral working directory, remove checkout paths from `PYTHONPATH`, reinstall `hail`, and rerun the import probe. |
| `ModuleNotFoundError` for `hail.version`, `hailtop.version`, or missing `__version__` | Raw source tree lacks generated version files | Use a complete installed wheel/package or a fully built development install. Do not troubleshoot backend code until metadata exists. |
| `RuntimeError: Hail requires either ... HAIL_JAR, hail.jar or hail-all-spark.jar` | Backend JAR asset is missing, or `HAIL_JAR` points to a nonexistent file | Reinstall a complete `hail` package. If using a development JAR intentionally, set `HAIL_JAR` to a valid matching JAR. |
| `Hail version mismatch between JAR and Python library` | Python package and backend JAR come from different builds/releases | Remove stale `HAIL_JAR` or classpath entries, reinstall one Hail version, and restart Python. |
| Java warning says Hail was built and tested with Java 11 | Java feature version is not 11 | Install Java 11 and set `JAVA_HOME`/`PATH` so Hail starts Java 11. Treat other Java versions as unsupported. |
| `No py4j JAR found in .../jars` or Py4J gateway launch fails | PySpark/Spark installation is incomplete, missing JARs, or outside Hail's supported range | Install Hail dependencies in one environment, verify `pyspark>=3.5,<3.6`, and avoid mixing Spark installations. |
| Spark init cannot find Hail classes or `is.hail` | Existing SparkContext lacks Hail JAR/classpath settings | Restart and let Hail create Spark with `hl.init(backend='spark', ...)`, or create the SparkContext with the Hail JAR in `spark.jars`, driver classpath, and executor classpath. |
| Spark class loading or serializer errors appear after startup | Spark/PySpark version or Scala/Spark cluster mismatch | Use PySpark `>=3.5,<3.6` and Spark 3.5.x with Scala 2.12 for cluster deployments. Avoid arbitrary Spark versions. |
| `hl.init` uses Spark when local or Batch was expected | Backend selected by default, environment, or `hailctl config` | Pass `backend='local'`, `backend='spark'`, or `backend='batch'` explicitly. Check `HAIL_QUERY_BACKEND` and `hailctl config get query/backend`. |
| Re-running `hl.init` does not change configuration | Hail is already initialized, or `idempotent=True` made later init calls no-ops | Call `hl.stop()` before changing backend, Spark conf, tmp/log paths, requester-pays settings, or default reference. |
| Startup fails with `PermissionError`, `FileNotFoundError`, or log creation errors | `log`, `HAIL_LOG_DIR`, `tmp_dir`, or `local_tmpdir` is missing, unwritable, or not visible to workers | Use explicit writable local `log`/`local_tmpdir`; use backend-visible shared `tmp_dir`; create directories or fix permissions. |
| Error mentions invalid local tmp scheme | `local_tmpdir` used a non-`file://` URI scheme | Use a plain local path or `file:///...` for `local_tmpdir`; reserve cloud paths for shared `tmp_dir` or Batch remote tmpdir. |
| GCS requester-pays read fails with billing or user-project errors | Requester-pays project is missing, scoped to wrong buckets, or overridden by config precedence | Pass `gcs_requester_pays_configuration='PROJECT'` or `(PROJECT, ['bucket'])` directly to `hl.init`, then inspect `hailctl config` and `HAIL_GCS_REQUESTER_PAYS_*` variables. |
| Cold-storage or bucket policy errors on cloud reads | GCS bucket allow-list is absent or incorrectly shaped | Supply bucket names without `gs://` prefixes in the allow-list shape expected by the init path. Recheck whether the generic `hl.init` or direct `hl.init_batch` path is being used. |
| Batch backend says no billing project | Query-on-Batch lacks Hail Batch billing config | Pass the billing project where supported or run `hailctl config set batch/billing_project YOUR-HAIL-BATCH-BILLING-PROJECT`. |
| Batch backend says remote tmpdir is missing or invalid | Query-on-Batch lacks `batch/remote_tmpdir` or received a bucket name instead of a URI | Set a full remote tmpdir URI such as `gs://YOUR-BUCKET/prefix/` with `hailctl config set batch/remote_tmpdir ...` or pass an explicit supported tmp path. |
| A local notebook asks for Batch auth, billing, or remote tmpdir | Global query backend points to `batch` | Override with `hl.init(backend='local')` or `hl.init(backend='spark')`, then clean global config if Batch should not be the default. |
| `hl.spark_context()` fails under local or Batch | Spark-only helper called with a non-Spark backend | Use a Spark backend for Spark-specific interop, or use `hl.current_backend()` for generic post-init introspection. |
| `hl.debug_info()` starts unwanted default initialization or fails before planned init | Introspection happened before explicit setup | Call `hl.init(...)` explicitly first, or use the root diagnostic script for pre-init environment checks. |

## Import Shadowing

Hail's source layout includes a top-level `hail` directory. If Python starts from a source checkout or a checkout path appears in `PYTHONPATH`, `import hail` can resolve to source files instead of the installed distribution. This often produces partial success: import works, but generated version metadata, package resources, or backend JAR assets are absent.

Safe private diagnostic:

```bash
python - <<'PY'
import hail as hl
print(getattr(hl, '__file__', '<no file>'))
print(hl.version())
PY
```

If the printed module location is an unexpected local source tree, change directories, clean `PYTHONPATH`, and reinstall the package. Do not copy local paths from this diagnostic into reusable code or public instructions.

## Generated Version and JAR Assets

Complete Hail runtime installs should include generated Python version modules and backend JAR package data. Backend startup searches for a JAR in this order:

1. `HAIL_JAR` environment variable,
2. development resource `backend/hail.jar`,
3. packaged resource `backend/hail-all-spark.jar`.

If none exists, `hl.init` cannot start local or Spark query backends. If the JAR exists but reports a different Hail version than Python, startup raises a version mismatch. Recovery is to use one consistent installed package or one matched development build, then restart the process.

The live inspection for this generated skill found that `import hail`, `import hailtop`, and `import hailtop.batch` succeeded, but the inspected package did not expose the `hail.backend.hail-all-spark.jar` resource. Treat backend tests that require the JAR as conditional until a complete runtime package or matching development JAR is available.

## Java, Spark, and PySpark Pitfalls

- Hail is built and tested with Java 11; other Java versions are unsupported.
- Local backend startup still launches a Py4J gateway and needs Spark/PySpark JAR assets for its classpath.
- Spark backend startup can configure Spark only before SparkContext creation. Existing Spark contexts must already include the Hail JAR and classpath settings.
- The package pins PySpark to `>=3.5,<3.6`; clusters should be Spark 3.5.x with Scala 2.12 for source-built cluster deployments.
- Prefer ordinary `python`, IPython, notebooks, `hl.init(backend='spark')`, or properly configured `spark-submit` over starting Hail from an unmanaged `pyspark` shell.

## Tmp and Log Failures

- `log` and `HAIL_LOG_DIR` are local filesystem locations, not GCS/S3/HDFS paths.
- `tmp_dir` or backend-specific `tmpdir` is shared scratch and must match the backend's storage world.
- `local_tmpdir` is local scratch; for Spark it affects Spark local directory behavior and must be a local path or `file://` URI.
- If initialization fails while creating tmp directories, simplify to known-good local paths for local/Spark or known-good cloud tmp paths for Batch, then reintroduce custom paths one at a time.

## Requester-Pays and Configuration Precedence

For Hail Query, explicit `hl.init(...)` keyword arguments override environment variables, which override `hailctl config`, which override defaults. Some GCS and Batch settings are shared between Hail Query and Hail Batch. When cloud access fails, inspect:

- `HAIL_QUERY_BACKEND`, `HAIL_GCS_REQUESTER_PAYS_PROJECT`, `HAIL_GCS_REQUESTER_PAYS_BUCKETS`, and `HAIL_GCS_BUCKET_ALLOW_LIST`.
- `HAIL_BATCH_BILLING_PROJECT`, `HAIL_BATCH_REMOTE_TMPDIR`, and `HAIL_BATCH_REGIONS` when using Query-on-Batch.
- `hailctl config get query/backend`, `hailctl config get gcs_requester_pays/project`, `hailctl config get gcs_requester_pays/buckets`, `hailctl config get batch/billing_project`, and `hailctl config get batch/remote_tmpdir`.

Prefer direct `hl.init` arguments in scripts that must be reproducible. Use bucket-name lists where the API expects bucket names and full `gs://...` URIs only where the API expects paths.

## Backend Selection Mistakes

Batch query backend is for Hail Query execution through Hail Batch service, not for every `hailtop.batch` DAG. If local work unexpectedly asks for auth, billing, remote tmpdir, or regions, override the query backend locally:

```python
import hail as hl
hl.init(backend='local', quiet=True)
```

Then inspect global configuration and clean it if the user did not intend Batch as the default. Route actual Batch DAG construction, `hailctl batch`, and `ServiceBackend` billing workflows to [Batch and CLI](../../batch-and-cli/SKILL.md).

## Backend-Starting Checks

Treat backend-starting checks as conditional. Do not use them as final verification unless the verification environment has a complete matching Hail backend JAR and safe tmp/log settings. Help-only checks that do not start a backend are safer for minimal environments.
