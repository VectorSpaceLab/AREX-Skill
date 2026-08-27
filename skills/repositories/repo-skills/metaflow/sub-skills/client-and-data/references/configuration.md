# Client and Data Configuration

## Profiles and environment variables

Metaflow configuration is exposed through `METAFLOW_*` environment variables and profile files. Common non-secret knobs include:

- `METAFLOW_DEFAULT_DATASTORE`, `METAFLOW_DATASTORE_SYSROOT_LOCAL`, `METAFLOW_DATASTORE_SYSROOT_S3`, `METAFLOW_DATASTORE_SYSROOT_AZURE`, `METAFLOW_DATASTORE_SYSROOT_GS`.
- `METAFLOW_DEFAULT_METADATA`, `METAFLOW_SERVICE_URL`.
- `METAFLOW_CLIENT_CACHE_PATH`, `METAFLOW_CLIENT_CACHE_MAX_SIZE`.
- `METAFLOW_S3_ENDPOINT_URL`, `METAFLOW_S3_RETRY_COUNT`, `METAFLOW_S3_WORKER_COUNT`.
- `METAFLOW_CARD_LOCALROOT`, `METAFLOW_CARD_S3ROOT`, `METAFLOW_CARD_AZUREROOT`, `METAFLOW_CARD_GSROOT`.
- `METAFLOW_PROFILE` to select a configuration profile.

Do not print or store secret-bearing values such as service auth keys, cloud credentials, or API tokens in generated artifacts or logs.

## Diagnostic order

1. Print `get_metadata()` and `get_namespace()`.
2. Confirm the pathspec shape and namespace visibility.
3. Confirm the datastore root and backend service credentials if artifact/log reads fail.
4. For S3-compatible storage, confirm endpoint URL, bucket/prefix, and boto3 availability.
