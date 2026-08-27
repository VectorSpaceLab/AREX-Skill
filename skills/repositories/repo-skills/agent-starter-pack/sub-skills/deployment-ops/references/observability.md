# Observability

## Two layers to remember
### Cloud Trace telemetry
- Always enabled in generated projects.
- Tracks execution, latency, and request flow.
- Works across templates as the baseline observability layer.

### BigQuery Agent Analytics
- Opt-in ADK feature.
- Adds richer event logging for analysis and dashboards.
- Requires the project to enable the feature during generation and to provision the supporting cloud resources.

## What to explain to a user
- Local development and deployed environments can have different logging defaults.
- ADK-based templates are the primary place where the BigQuery analytics plugin appears.
- The observability setup is part of the generated project, not the source package itself.

## Common environment cues
- `LOGS_BUCKET_NAME`
- `BQ_ANALYTICS_DATASET_ID`
- `BQ_ANALYTICS_GCS_BUCKET`
- `BQ_ANALYTICS_CONNECTION_ID`
- `OTEL_INSTRUMENTATION_GENAI_CAPTURE_MESSAGE_CONTENT`

## Troubleshooting cues
- Logs are missing because the cloud bucket or dataset is not configured.
- Permissions are insufficient for storage or BigQuery access.
- The user expects prompt-response logging in a template that only supports the baseline telemetry layer.
