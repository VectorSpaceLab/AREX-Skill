# Integrations and Extensibility Troubleshooting

Start with the smallest failing layer: package import, Feast config validation, service credentials, then workflow semantics. Avoid jumping directly to `apply`, `materialize`, or server commands when a no-service preflight would isolate the issue faster.

## Quick Triage

```bash
feast version
feast --help
feast validate
python scripts/check_optional_extra.py --extras redis snowflake dbt mlflow openlineage ge
```

Interpretation:

- `feast` command missing: Feast is not installed in the active Python environment or the console script is not on `PATH`.
- Helper reports `MISSING`: install the named extra, for example `pip install 'feast[redis]'`.
- `feast validate` fails before service calls: fix `feature_store.yaml`, object definitions, or missing optional imports.
- Validation passes but live operation fails: inspect backend credentials, network, permissions, warehouse/schema/table existence, or service readiness.

## Optional Extra and Import Errors

Common signals:

```text
ModuleNotFoundError: No module named 'redis'
ModuleNotFoundError: No module named 'snowflake'
FeastExtrasDependencyImportError: redis
ImportError: dbt-artifacts-parser is not installed
```

Fix pattern:

```bash
pip install 'feast[redis]'
pip install 'feast[snowflake,redis]'
pip install 'feast[dbt]'
python scripts/check_optional_extra.py --extras redis snowflake dbt
```

Do not install `feast[ci]` or `feast[dev]` for ordinary user tasks unless the user explicitly needs the whole contributor/test environment.

## Config Selector Errors

Feast maps short names to backend classes. If a selector is wrong, validation may fail with invalid-name or config-construction errors.

Check these exact selector families:

- Offline Snowflake: `snowflake.offline`, not `snowflake`.
- Online Snowflake: `snowflake.online`.
- Spark compute: `spark.engine`.
- Ray compute: `ray.engine`.
- Snowflake compute: `snowflake.engine`.
- Flink compute: `flink.engine`.
- Default local online store: `sqlite`.
- Default local offline store: `dask`.

Minimal validation:

```bash
feast validate
feast plan
```

If a private extension is not registered as a short selector, use its fully qualified class path and ensure the class name suffix follows Feast loader conventions (`OnlineStore`, `OfflineStore`, or `Engine`).

## Backend Credential and Service Failures

### Snowflake

Likely signals:

- Authentication or account errors.
- Warehouse/database/schema not found.
- Permission denied creating stages or writing online/offline tables.
- Missing `snowflake.connector` import.

Checklist:

```bash
python scripts/check_optional_extra.py --extras snowflake
feast validate
```

Review YAML fields: `account`, `user`, one of `password` or key-pair settings, `warehouse`, `database`, and `schema`. For Snowflake compute, ensure the role can create stages and execute Snowpark objects.

### Redis

Likely signals:

- Connection refused or timeout.
- Authentication failed.
- TLS mismatch.
- Cluster/sentinel connection string errors.
- Missing `redis` or `hiredis` import.

Checklist:

```bash
python scripts/check_optional_extra.py --extras redis
```

Review `connection_string`, for example `redis.internal:6379,db=0,ssl=true,password=...`. Keep secrets out of committed YAML.

### Spark, Ray, and Flink

Likely signals:

- Missing runtime packages (`pyspark`, `ray`, `pyflink`).
- Cluster/session not configured.
- Staging or remote path unavailable.
- Unsupported feature view mode or transformation shape.
- `pyarrow` version conflict with the Flink extra.

Checklist:

```bash
python scripts/check_optional_extra.py --extras spark ray flink
feast validate
```

Start with local/small jobs before remote clusters. For materialization semantics route to `../../retrieval-and-materialization/SKILL.md`.

## dbt Import Failures

Signals and fixes:

| Signal | Likely cause | Fix |
| --- | --- | --- |
| `dbt manifest not found` | `target/manifest.json` does not exist at the path passed to `feast dbt` | Run `dbt compile` or pass the correct manifest path. |
| Missing `dbt_artifacts_parser` | `dbt` extra not installed | `pip install 'feast[dbt]'`. |
| Models skipped | Tag filter too narrow or entity columns absent | Check `--tag-filter` and `--entity-column` values. |
| Unsupported data source type | Generated source target is not `bigquery`, `snowflake`, or `file` | Use a supported target or manually adapt definitions. |
| Generated file fails compile | Type mapping or template mismatch | Run `python -m py_compile <file>` and inspect generated imports/schema. |

Safe commands:

```bash
feast dbt list target/manifest.json --tag-filter feast
feast dbt import target/manifest.json --entity-column user_id --data-source-type file --dry-run
```

## MLflow Failures

Signals and fixes:

- `store.mlflow is None`: set `mlflow.enabled: true` in `feature_store.yaml`.
- Missing `mlflow` import: install `feast[mlflow]`.
- Module-level `feast.mlflow` raises runtime guidance: create `FeatureStore(repo_path=...)` with MLflow enabled or explicitly initialize the module with the store.
- No feature lineage logged: use Feast retrieval APIs inside an active MLflow run and log through the configured store.
- Tracking server unreachable: verify `tracking_uri`, environment variables, network, and credentials.

Minimal config check:

```bash
python scripts/check_optional_extra.py --extras mlflow
python - <<'PY'
from feast import FeatureStore
store = FeatureStore(repo_path='.')
print(bool(store.mlflow))
PY
```

## OpenLineage Failures

Signals and fixes:

- Missing `openlineage.client`: install `feast[openlineage]`.
- `transport_url is required for HTTP transport`: add `transport_url` when `transport_type: http`.
- No emitted events: ensure `openlineage.enabled` is true, transport config is reachable, and the operation emits lineage.
- File transport writes nowhere expected: set `log_file_path` in the OpenLineage block.

Minimal file-transport smoke config:

```yaml
openlineage:
  enabled: true
  transport_type: file
  namespace: feast-local
  log_file_path: openlineage_events.json
```

## DQM / Great Expectations Failures

Signals and fixes:

- Missing `great_expectations`: install `feast[ge]`.
- Validation does not run: confirm `enable_validation=True` on `FeatureView`, `BatchFeatureView`, or `StreamFeatureView` and that validation references/profiles are wired into the workflow.
- Schema errors: compare entity join keys, `Field` declarations, source columns, and timestamp columns.
- Validation output confusing: inspect the underlying Great Expectations expectation suite and result object.

## Custom Extension Failures

Signals and fixes:

- Invalid class name: online store classes must end with `OnlineStore`, offline store classes with `OfflineStore`, and compute classes with `Engine` for config class derivation.
- Config class not found: ensure `<ClassName>Config` is importable from the same module or adapt the loader path.
- Private package not found: install the private package in the active environment; do not assume the source repo is importable.
- Runtime mode unsupported: fail with a clear `NotImplementedError` or Feast-specific error naming the unsupported operation.
- Live service tests flaky: add fake-client unit coverage and mark service-backed checks separately.

## Escalation Routes

- Need to write retrieval or materialization code after backend setup: `../../retrieval-and-materialization/SKILL.md`.
- Need server deployment, remote store clients, or TLS/auth serving: `../../servers-and-remote/SKILL.md`.
- Need to add the implementation to Feast and run tests/lint/docs: `../../repo-development/SKILL.md`.
- Need vector retrieval or RAG backend guidance: `../../rag-and-vector-search/SKILL.md`.
