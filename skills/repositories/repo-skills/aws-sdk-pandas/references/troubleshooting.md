# Cross-Cutting Troubleshooting

## Purpose

Read this when a user hits an install, import, credential, region, or optional-dependency failure before the request is narrowed to a single sub-skill.

## Common symptoms and recoveries

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'boto3'`, `botocore`, `pandas`, `numpy`, or `pyarrow` | Base runtime dependencies are missing | Install `awswrangler` into a fresh environment and rerun the import check. |
| `Missing optional dependency 'pymysql'` / `pg8000` / `pyodbc` / `oracledb` / `redshift_connector` / `opensearchpy` / `gremlin_python` / `SPARQLWrapper` / `deltalake` / `pyiceberg` | The relevant extra is not installed | Install the matching project extra, for example `awswrangler[mysql]` or `awswrangler[pyiceberg]`. |
| `NoCredentialsError: Unable to locate credentials` | AWS credentials are missing or expired | Configure a default boto3 session, profile, or environment credentials before calling live AWS helpers. |
| `NoRegionError: You must specify a region` | The default region is missing | Set `AWS_DEFAULT_REGION` or use an explicit `boto3.Session(region_name=...)`. |
| `Missing optional dependency ...` only when calling a feature, not on import | The project uses lazy optional imports | Install the extra for the feature family instead of expecting the base import to bring every backend. |
| `InvalidArgumentValue` / `InvalidArgumentCombination` | The request passed invalid API arguments | Re-check the target sub-skill’s API reference and the helper’s argument compatibility rules. |
| `PyODBC` import errors on macOS about `unixODBC` | The system ODBC driver or library is missing | Install the native ODBC runtime first; the project docs call out `brew install unixodbc` as the usual fix. |
| Ray-mode calls reject `boto3_session` or `s3_additional_kwargs` | Distributed mode has specific unsupported kwargs | Switch back to Python/pandas mode or remove the unsupported arguments before retrying. |
| Excel helpers fail when reading S3 objects | `openpyxl` is missing or the object access is not configured | Install `awswrangler[openpyxl]` and confirm S3 credentials / region. |
| Athena or Glue calls fail immediately even with valid SQL/text | The database, workgroup, output bucket, or IAM permissions are missing | Check `catalog-and-query` for the required service prerequisites and retry with explicit session settings. |

## When to stop and escalate

Stop and ask for more information when the request needs:

- live AWS resources that do not exist in the current account,
- a private database endpoint or other managed service that is not reachable,
- a system-level library that cannot be installed without host authorization,
- or a required optional backend that the user has not asked to install.

## Related guides

- `runtime-overview.md` for install and extra selection.
- `../sub-skills/runtime-and-config/references/troubleshooting.md` for config and engine-specific issues.
- `../sub-skills/s3-lakehouse/references/troubleshooting.md` for S3/object-format issues.
- `../sub-skills/catalog-and-query/references/troubleshooting.md` for Athena/Glue/clean-room issues.
- `../sub-skills/sql-connectors/references/troubleshooting.md` for connector and ODBC issues.
- `../sub-skills/service-integrations/references/troubleshooting.md` for service-specific AWS failures.
