# Service Integrations Troubleshooting

## Purpose

Use this reference when a service-specific wrapper fails after the package import already succeeded.

## Common failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Missing optional dependency ...` for OpenSearch, Neptune, or related graph/search packages | The matching extra is not installed | Install the connector extra that matches the service family. |
| `NoCredentialsError` or permission errors | AWS credentials or IAM permissions are missing | Configure a valid boto3 session and confirm the needed AWS permissions. |
| `STS` identity helpers return nothing useful | The current session is not authenticated | Confirm the session, region, and account context first. |
| `SecretsManager` reads fail or return the wrong shape | The secret name is wrong or the secret is not JSON | Check the secret name and use `get_secret` vs `get_secret_json` appropriately. |
| `Chime` posting fails immediately | The webhook or message input is invalid | Validate the webhook URL and message string before posting. |
| DynamoDB reads are empty or partial | The table key schema, item shape, or key condition does not match | Check the key schema and the `allow_full_scan` / filter settings. |
| DynamoDB PartiQL or item writes fail on the keys | The item lacks the required key attributes | Ensure every item includes the table's hash key and sort key if one exists. |
| Timestream writes or queries fail on measure/dimension columns | The table schema and the DataFrame shape do not match | Reconcile the time column, measure column, and dimension columns first. |
| OpenSearch indexing or search fails | The client endpoint, auth, or mapping is wrong | Confirm the client connection, index name, and response shape. |
| Neptune bulk load or graph export fails | The data is not flattened or the parser configuration is wrong | Flatten the data first and verify the parser configuration or load parameters. |
| CloudWatch query is cancelled or never completes | The query was stopped, timed out, or the log group selection was wrong | Inspect the query state and retry with a smaller log window. |
| EMR cluster or EMR Serverless job creation fails | The subnet, role, application, or S3 logging path is missing | Confirm the cluster/application prerequisites before retrying. |
| QuickSight creation or ingestion fails | The account, namespace, or source Athena dataset is missing | Check the resource IDs and AWS permissions. |

## Recovery order

1. Confirm the right connector or service family.
2. Confirm the AWS session, region, and permissions.
3. Confirm the resource identifiers and input shape.
4. Retry with the smallest possible payload or query.

## Related guidance

- `../../../references/runtime-overview.md` for extras and basic runtime facts.
- `../../../references/troubleshooting.md` for the cross-cutting install/import and credential checks.
- `../../s3-lakehouse/references/troubleshooting.md` when the service workflow depends on S3 staging or file layout.
- `../../catalog-and-query/references/troubleshooting.md` when Athena or Glue is in the path.
