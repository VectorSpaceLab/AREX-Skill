# Catalog and Query Troubleshooting

## Purpose

Use this reference for Glue, Athena, Data Quality, and Clean Rooms failures.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `NoCredentialsError` or `NoRegionError` | The boto3 session is not configured | Set credentials and region, then rerun the query or catalog call. |
| Athena fails immediately with missing database or table errors | The Glue Catalog object does not exist or the database name is wrong | Create or correct the catalog metadata first. |
| Athena query starts but cannot write results | The output bucket is missing, inaccessible, or not allowed by the workgroup | Create the bucket, fix IAM permissions, or use `create_athena_bucket()`. |
| `QueryCancelled` or `QueryFailed` | The query was stopped, timed out, or returned an execution error | Inspect query execution metadata, then rerun with a smaller or corrected SQL statement. |
| `InvalidArgumentCombination` around CTAS/UNLOAD | The query mode flags or parameters are contradictory | Pick one execution mode and remove incompatible flags. |
| Duplicate or undefined column errors in Athena reads | The query result has ambiguous column names or unsupported expressions | Rename the columns in SQL or use an explicit select list. |
| Data Quality ruleset calls fail with IAM or catalog errors | The ruleset needs an IAM role and a real Glue table/database context | Provide the role ARN and verify the catalog object exists. |
| Data Quality `update_ruleset` or `evaluate_ruleset` returns an empty or unexpected frame | The rule format does not match the expected DataFrame or DQDL structure | Rebuild the rules with the documented schema before retrying. |
| Clean Rooms query fails because output files are missing | The output bucket or prefix was wrong, or the member was not authorized | Confirm the membership, output location, and the analysis template / SQL rights. |
| `read_sql_query(..., chunksize=True)` behaves like a normal DataFrame call | Chunked mode returns an iterator | Consume the iterator explicitly and do not expect a single frame. |

## Recovery order

1. Confirm the database, table, and S3 output location.
2. Confirm the workgroup and query mode.
3. Re-run with a tiny SQL statement or a narrow catalog slice.
4. Only then move on to Data Quality or Clean Rooms specifics if the problem persists.

## Related guidance

- `../../../references/runtime-overview.md` for install and extras.
- `../../../references/troubleshooting.md` for cross-cutting import and credential issues.
- `../../s3-lakehouse/references/troubleshooting.md` when the root cause is file layout or dataset shape.
