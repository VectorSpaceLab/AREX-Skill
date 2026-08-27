# Serving troubleshooting

Use this file when a deployment, local inference, or recommendation flow fails.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `NoRegionError` on import | region not set | export `AWS_REGION` or `AWS_DEFAULT_REGION` first |
| `NoCredentialsError` during `ModelBuilder` construction | role discovery or AWS access is unavailable | pass `role_arn` explicitly or configure credentials |
| local deploy fails | Docker or local runtime is missing | install/start Docker for `LOCAL_CONTAINER` |
| `deploy_local()` rejected | mode is not local | rebuild with `Mode.LOCAL_CONTAINER` or `Mode.IN_PROCESS` |
| schema mismatch | sample input/output do not match the real payload | adjust `SchemaBuilder` or `InferenceSpec` |
| recommendation job fails | inference recommender feature not enabled or inputs incomplete | check account access and required parameters |
| Bedrock deploy fails | invalid source, region, or permissions | verify model source and Bedrock permissions |

## Safe debugging steps

1. Check the region first.
2. Check the credentials and role ARN.
3. Confirm the model source exists and is accessible.
4. Verify the transport contract with a local mode before launching cloud
   deployment.
5. Use the root smoke helper to confirm imports still work.

## Notes

- `sagemaker.serve` imports are region-sensitive in fresh environments.
- `ModelBuilder` uses `role_arn`, not the legacy predictor pattern.
- `SchemaBuilder` is only as good as the sample payloads you provide.

## Escalation

- For endpoint CRUD or batch transform, use core resources.
- For training or model customization, use the training or customization
  sub-skill.
- For pipeline wiring, use MLOps.
