# Core resource troubleshooting

Use this file for issues that arise while working directly with sessions,
resource objects, URI retrieval, or lineage.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `NoCredentialsError` when constructing a session or resolving a role | AWS credentials are missing or role discovery is unavailable | provide credentials or pass an explicit role/role ARN |
| `default_bucket()` is not usable | session setup is incomplete | create the `Session` first and verify its region and credentials |
| `image_uris.retrieve(...)` fails | region, framework version, or instance type is invalid | check the requested framework tuple and region |
| `Endpoint.invoke(...)` fails | endpoint not yet in service or payload format mismatch | wait for `InService` and verify `content_type` / `accept` |
| lineage delete operations fail | associations still exist | delete associations before deleting the linked entities |
| serverless config validation fails | shape or required field mismatch | build the config from the verified low-level shapes |

## Safe debugging steps

1. Verify `Session().boto_region_name`.
2. Confirm the active environment has AWS credentials if the code needs STS or
   real resource calls.
3. Re-run the bundled root import smoke helper.
4. Check whether the task should actually be routed to training, serving, or
   MLOps instead of staying in core resources.

## Notes on helpers

- `Processor` and `ScriptProcessor` are helper wrappers around processing jobs;
  they are not the same thing as the low-level `ProcessingJob` resource.
- `Transformer` is the batch-transform helper wrapper.
- `sagemaker.core.lineage` is the preferred import path for new code.

## Escalation path

If the issue is not clearly a core-resource problem, hand the task to the
matching sibling sub-skill:

- training: `../training/SKILL.md`
- serving: `../serving/SKILL.md`
- MLOps: `../mlops/SKILL.md`
