# SageMaker Python SDK v3 troubleshooting

Use this reference for cross-cutting installation, import, region, credential,
and optional-dependency issues across the SageMaker Python SDK v3 packages.
For workflow-specific failures, also read the matching sub-skill troubleshooting
file.

## Fast triage

| Symptom | Likely cause | What to do |
| --- | --- | --- |
| `ModuleNotFoundError` or stale imports | packages not installed in the active environment | reinstall `sagemaker` or the modular packages, then run `pip check` |
| `NoRegionError` when importing `sagemaker.serve` or `sagemaker.mlops` | no AWS region set in a fresh environment | set `AWS_REGION` or `AWS_DEFAULT_REGION` before import |
| `NoCredentialsError` during `ModelTrainer` or `ModelBuilder` construction | role discovery or AWS API access needs credentials | pass an explicit role, or configure credentials before constructing the object |
| Docker/local container example fails | Docker or local image/runtime not present | install and start Docker, then verify local paths and image availability |
| `DataMixingConfig` validation error | Nova percentages do not add up to 100 | fix the percentage split before dry-run or submission |
| `EMRServerlessStep` import missing from `sagemaker.mlops.workflow` | the class is defined in a nested module, not re-exported | import it from `sagemaker.mlops.workflow.emr_serverless_step` |
| local CUDA smoke fails | torch/CUDA mismatch or no GPU available | treat CUDA as optional and fall back to CPU checks |

## Install and environment checks

1. Confirm the right environment is active.
2. Install the needed package set:
   - `pip install sagemaker`
   - or install the modular packages directly when you only need one area:
     `pip install sagemaker-core`, `pip install sagemaker-train`,
     `pip install sagemaker-serve`, `pip install sagemaker-mlops`
3. Run `python -m pip check`.
4. Use the bundled smoke helper:

```bash
python skills/disco/sagemaker-python-sdk/scripts/check_sagemaker_v3_imports.py
```

If you are testing a fresh checkout of this repo, make sure the editable local
packages are installed into the inspection environment before expecting the
imports to work.

## Region and credential issues

- `sagemaker.serve` and `sagemaker.mlops` need a region in a fresh environment.
- `ModelTrainer` and `ModelBuilder` may resolve a role through STS when a role is
  not supplied explicitly.
- Cloud examples should use placeholders unless the user has already authorized
  live AWS execution.
- For job, endpoint, or pipeline examples, always state the required AWS
  identity, IAM permissions, and cleanup step.

## Optional dependency issues

- `torch` is required for many training and serving workflows, especially local
  and GPU-adjacent examples.
- `mlflow` and `sagemaker-mlflow` support experiment tracking and MLOps cases.
- `pyiceberg`, `s3fs`, and `pyarrow` support MLOps and feature-store-adjacent
  workflows.
- Docker is required for local container serving and local container training
  examples.

If a feature depends on one of these extras, say so explicitly instead of
implying that the base import should be enough.

## Workflow-specific follow-up

- Training issues: see `sub-skills/training/references/troubleshooting.md`
- Model customization issues: see
  `sub-skills/model-customization/references/troubleshooting.md`
- Serving issues: see `sub-skills/serving/references/troubleshooting.md`
- MLOps issues: see `sub-skills/mlops/references/troubleshooting.md`
- Core resource issues: see `sub-skills/core-resources/references/troubleshooting.md`

## Safe recovery pattern

When a task fails because of a transient import or local environment problem:

1. Re-run the failing command once in the same environment.
2. Check the region, credentials, and optional dependencies.
3. Avoid launching cloud jobs until the import or configuration error is fixed.
4. If the issue remains, isolate it in the matching sub-skill and keep the root
   guidance brief.
