---
name: sagemaker-python-sdk
description: "Route SageMaker Python SDK v3 tasks to self-contained guidance for
  core resources, training, model customization, serving, MLOps, migration, and
  troubleshooting."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SageMaker Python SDK v3 Repo Skill

Use this skill when the task involves the Amazon SageMaker Python SDK v3:
training, fine-tuning, deployment, inference, pipelines, Feature Store, model
registry, low-level SageMaker resources, image URI retrieval, or V2-to-V3
migration. The SDK is v3-first and modular: `sagemaker-core`,
`sagemaker-train`, `sagemaker-serve`, and `sagemaker-mlops`.

## Mandatory v3 policy

- Default to SageMaker Python SDK **v3** (`pip install sagemaker`).
- Use the SDK before raw `boto3`, AWS CLI, or hand-written service requests
  unless the user explicitly asks for those lower-level interfaces.
- Do not generate v2 imports such as estimator, model, predictor, processing,
  workflow, or framework-estimator modules except inside clearly labeled
  deprecated migration notes.
- Do not hardcode real account IDs, role ARNs, regions, buckets, subnets,
  security groups, or credentials. Use `Session()`, `get_execution_role()`,
  `Session().default_bucket()`, and placeholders.
- If the user asks to run cloud jobs, stop to confirm region, AWS credentials,
  execution role, S3 staging/output paths, service quotas, and billable-resource
  cleanup before submission.

## Quick route map

| User intent | Load this |
| --- | --- |
| Install/import smoke, v3-vs-v2 decision, or broad SDK selection | Stay in this root and read [`references/v3-interface-selection.md`](references/v3-interface-selection.md) |
| Retrieve framework image/model/script URIs, use `Session`, low-level jobs/resources, processing, transform, endpoints, or lineage | [`sub-skills/core-resources/SKILL.md`](sub-skills/core-resources/SKILL.md) |
| Train a model with `ModelTrainer`, local/distributed training, JumpStart training, HPO, AWS Batch training queues, or remote function | [`sub-skills/training/SKILL.md`](sub-skills/training/SKILL.md) |
| Fine-tune/customize foundation models with SFT/DPO/RLVR/RLAIF/CPT/MultiTurnRL, run evaluations, recipes, data mixing, or notifications | [`sub-skills/model-customization/SKILL.md`](sub-skills/model-customization/SKILL.md) |
| Deploy or serve with `ModelBuilder`, `InferenceSpec`, local/in-process/container mode, serverless/async/batch inference, JumpStart, optimization, Bedrock, or recommendations | [`sub-skills/serving/SKILL.md`](sub-skills/serving/SKILL.md) |
| Build SageMaker Pipelines, workflow steps, model registry flows, Feature Store orchestration, quality/Clarify checks, lineage/governance, triggers, retries, or local pipeline execution | [`sub-skills/mlops/SKILL.md`](sub-skills/mlops/SKILL.md) |
| Convert old SDK code to v3 | [`references/migration-v2-to-v3.md`](references/migration-v2-to-v3.md), then route to the owning sub-skill |
| Debug install/import/region/role/credentials/optional deps | [`references/troubleshooting.md`](references/troubleshooting.md) |

## Intent-to-interface defaults

- Train / fine-tune / managed training: `sagemaker.train.ModelTrainer` or the
  specialized customization trainers in the model-customization sub-skill.
- Distributed training: `ModelTrainer` with `Compute(instance_count=...)` and a
  `Torchrun`, `MPI`, `SMP`, or custom `DistributedConfig`.
- Hyperparameter tuning: `sagemaker.train.tuner.HyperparameterTuner` or
  `sagemaker.core.resources.HyperParameterTuningJob` for low-level control.
- Deploy / host / endpoint inference: `sagemaker.serve.ModelBuilder`.
- Endpoint invocation after deployment: `Endpoint.invoke(...)`.
- Processing / batch transform / resource CRUD: `sagemaker.core.resources` and
  helper classes such as `ScriptProcessor` or `Transformer`.
- Pipelines / registry / monitoring / Feature Store: `sagemaker.mlops.workflow`
  and `sagemaker.mlops.feature_store`.
- Container image URI: `sagemaker.core.image_uris.retrieve(...)`.

## Before writing code

1. Determine whether the user wants **usage guidance**, **migration**, or
   **repository maintenance**. For repository edits, still obey this repo's v3
   default and run focused tests under the relevant package.
2. Identify execution substrate: local-only object construction, Docker local
   mode, SageMaker cloud job/endpoint, HyperPod, AWS Batch, Bedrock, Feature
   Store, EMR, or a Pipeline.
3. Confirm whether the task can be answered without cloud execution. Many
   examples can be drafted with placeholders and `dry_run=True`; do not submit
   billable jobs unless explicitly authorized.
4. Open exactly the sub-skill and references needed for the intent. Do not
   duplicate full workflows across sub-skills.
5. Self-check generated code for banned v2 patterns and missing resource
   placeholders before returning.

## Shared references and helpers

- [`references/v3-interface-selection.md`](references/v3-interface-selection.md):
  package selection, install choices, and v3-first intent routing.
- [`references/migration-v2-to-v3.md`](references/migration-v2-to-v3.md):
  deprecated v2 pattern mappings and migration workflow.
- [`references/api-signature-summary.md`](references/api-signature-summary.md):
  verified public signatures and import caveats for this checkout.
- [`references/troubleshooting.md`](references/troubleshooting.md):
  install/import/region/role/credentials, optional dependency, Docker, and cloud
  service failure recovery.
- [`scripts/check_sagemaker_v3_imports.py`](scripts/check_sagemaker_v3_imports.py):
  safe import/version/CUDA probe for an installed SDK environment; it does not
  make cloud service calls.
- [`references/repo-provenance.md`](references/repo-provenance.md): source
  commit, versions, evidence paths, and refresh baseline.

## High-risk boundaries

- `sagemaker.serve` and `sagemaker.mlops` may need `AWS_REGION` or
  `AWS_DEFAULT_REGION` set even for import in a fresh environment.
- `ModelTrainer` and `ModelBuilder` can try role discovery through STS when no
  explicit role is supplied; outside SageMaker-managed environments this can
  fail before any job is submitted.
- Docker/local-container examples require Docker, images, local paths, and
  cleanup; in-process serving is the safer local path when it fits.
- Feature Store, Bedrock, SNS/EventBridge notifications, EMR, HyperPod, Batch,
  and SageMaker cloud jobs need AWS identity, IAM permissions, and service
  quotas; treat native runs as opt-in.
- Root and sub-skill runtime instructions must remain self-contained; do not
  tell future agents to reopen this source repository for examples.

## Handoff after using this skill

Return the sub-skill(s) consulted, the v3 interfaces selected, any assumptions
about region/role/S3/compute, the validation path used (`dry_run`, local smoke,
or no-submit review), and any cloud/Docker/native checks intentionally skipped.
