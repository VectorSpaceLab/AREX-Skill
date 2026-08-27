# MLOps troubleshooting

Use this file when a pipeline, step, feature-store, or lineage workflow fails.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `NoRegionError` during import or pipeline construction | region not set | export `AWS_REGION` or `AWS_DEFAULT_REGION` |
| pipeline create fails on role validation | the role ARN or permissions are wrong | pass a valid `role_arn` and confirm IAM permissions |
| local mode ignores parallelism config | local execution does not support it | remove `ParallelismConfiguration` for local runs |
| step output cannot be read | `JsonGet` / `PropertyFile` path mismatch | verify the property file name and JSON path |
| a step appears twice in a pipeline definition | a step was placed in both the main list and a condition branch | keep it in only one place |
| `EMRServerlessStep` import fails | wrong import path | import from `sagemaker.mlops.workflow.emr_serverless_step` |
| feature-store governance setup fails | Lake Formation / Iceberg dependencies or configuration are incomplete | use `FeatureGroupManager` only when those dependencies are really needed |

## Safe debugging sequence

1. Check the region.
2. Confirm the pipeline session and role.
3. Verify that upstream step args were built in the correct sub-skill.
4. Inspect the pipeline graph before starting the execution.
5. Use the local pipeline path only as a limited validation aid.

## Notes

- `PipelineExecution` is for inspection after `start()`.
- The pipeline step list must not include steps that also live inside a
  `ConditionStep` branch.
- `sagemaker.core.lineage` is the preferred lineage import path.

## Escalation

If the issue is about job construction rather than orchestration, hand the task
back to the training, serving, core-resource, or model-customization sub-skill.
