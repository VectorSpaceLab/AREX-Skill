# Training troubleshooting

Use this file for issues that happen while configuring or running `ModelTrainer`
and its training-adjacent workflows.

## Common failures

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `ValueError` from `SourceCode` | `entry_script` or `command` is missing | provide one of them before training |
| distributed training fails to start | `distributed` was set without `source_code` | add a proper training script and entrypoint |
| local training fails | Docker or local image prerequisites are missing | start Docker and verify the local framework image |
| `dry_run=True` still fails | config, URI, or role validation failed | fix the validation issue before submitting a job |
| HPO search does not find metrics | regex does not match the logs | adjust `metric_definitions` |
| `TrainingQueue` rejects a job | the trainer is not in SageMaker training mode | use `Mode.SAGEMAKER_TRAINING_JOB` |
| remote-function import looks legacy | the shim path is being used | import from `sagemaker.core.remote_function.client` instead |

## Safe debugging steps

1. Check the region and credentials before constructing the trainer.
2. Use `dry_run=True` to validate a configuration without launching a billable
   job.
3. Verify that the source directory actually contains the declared entry
   script.
4. Confirm the compute mode matches the intended execution path.
5. Re-read the root migration guide if the problem is really a v2-to-v3 port.

## Notes

- `sagemaker.train.configs` is a compatibility shim; prefer
  `sagemaker.core.training.configs` in new examples.
- `TrainingQueue` only supports SageMaker training jobs.
- For JumpStart, ensure the model identifier and version are valid before
  tuning or training.

## Escalation

If the issue is about foundation-model customization, deployment, or low-level
resource control, hand the task to the sibling sub-skill instead of expanding
this file.
