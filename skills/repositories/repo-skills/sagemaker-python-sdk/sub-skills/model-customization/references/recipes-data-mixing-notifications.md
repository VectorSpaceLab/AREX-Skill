# Recipes, data mixing, and notifications

Use this file for the configuration layer around model customization: recipe
resolution, data mixing, and job notifications.

## Recipe resolution

Use `get_resolved_recipe()` when the job is built from layered configuration and
you need to inspect the merged result before submission.

Typical precedence:

1. explicit SDK arguments
2. override dictionaries
3. recipe defaults
4. model-specific defaults

Keep the merged recipe review step in the workflow before any billable run.

## Data mixing

`DataMixingConfig` blends customer data with Nova-curated data.

Key rules:

- `customer_data_percent` must be between 0 and 100
- each Nova category percentage must be between 0 and 100
- if `customer_data_percent < 100` and Nova percentages are provided, the Nova
  percentages must sum to 100
- the SDK can serialize the config back to recipe form or to serverless
  hyperparameters

Example:

```python
from sagemaker.train import DataMixingConfig

mix = DataMixingConfig(
    customer_data_percent=70,
    nova_data_percentages={"code": 30},
)
```

Serverless Nova data mixing is the main supported path. Use the recipe and job
validation flow before submission to avoid invalid percentage combinations.

## Notifications

Training-job notifications are routed through SNS and EventBridge.
The configuration typically needs:

- `sns_topic_arn`
- optional `events`
- optional `job_name_prefix`
- optional `event_bus_arn`

Notifications are supported for SMTJ serverful and serverless compute, not for
HyperPod jobs.

### Operational checks

- The SNS topic must allow `events.amazonaws.com` to publish.
- The caller needs EventBridge rule-management permissions.
- Reusing the same topic/event/prefix configuration should reuse the same rule.

## Log and metric inspection

After submission, use:

- `show_metrics()` for plotted metrics
- `stream_logs()` for live log streaming
- `plot_training_metrics()` after restart

## What not to do

- Do not skip recipe validation when recipe overrides are involved.
- Do not assume data mixing percentages are optional if custom Nova categories
  were supplied.
- Do not treat HyperPod as a supported target for the notification feature.
