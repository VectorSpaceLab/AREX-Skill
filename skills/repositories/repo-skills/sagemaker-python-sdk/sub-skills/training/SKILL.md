---
name: training
description: "Use SageMaker Python SDK v3 training workflows with ModelTrainer,
  distributed drivers, JumpStart training, HPO, AWS Batch queues, and
  remote-function training concepts."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SageMaker Python SDK v3 Training Sub-skill

Use this sub-skill when the task is about general SageMaker training with the
v3 `sagemaker-train` package. Keep generated code v3-first and SDK-first.
Do not fall back to raw `boto3` training-job requests unless the user explicitly
asks for low-level API calls or the SDK does not expose the needed feature.

## Trigger phrases

Read this sub-skill when the user says or implies:

- "train a model on SageMaker" or "create a training job".
- "use ModelTrainer", "sagemaker-train", or "SDK v3 training".
- "local mode training", "local container training", `local_cpu`, or `local_gpu`.
- "distributed training", "torchrun", "MPI", "SMP", "multi-node", or "multi-GPU".
- "custom training container", "training image URI", or "retrieve a framework image".
- "JumpStart training" or `ModelTrainer.from_jumpstart_config(...)`.
- "hyperparameter tuning", "HPO", `HyperparameterTuner`, `tune()`, or `analytics()`.
- "AWS Batch training queue", `TrainingQueue`, fair-share, priority, or quota share.
- "remote function training job", `@remote`, `RemoteExecutor`, or container drivers.
- "migrate Estimator/framework estimator/fit to v3 training".

## When not to read this sub-skill

- Foundation model customization, evaluation, data mixing, recipe overrides,
  SFT, DPO, RLVR, RLAIF, CPT, or MultiTurnRL: route to
  [`../model-customization/SKILL.md`](../model-customization/SKILL.md).
- Model deployment, endpoint prediction, serverless/async real-time hosting,
  local/in-process inference, or ModelBuilder: route to
  [`../serving/SKILL.md`](../serving/SKILL.md).
- Processing jobs, batch transform, low-level resources, sessions, default
  buckets, image URI internals, or lineage primitives not tied to training:
  route to [`../core-resources/SKILL.md`](../core-resources/SKILL.md).
- Pipelines, workflow steps, model registry, feature store, Clarify, or lineage
  governance around training: route to [`../mlops/SKILL.md`](../mlops/SKILL.md).
- Deprecated v2 maintenance work only: use the root migration reference first,
  then return here only for the v3 replacement.

## V3 default policy

- Use `from sagemaker.train import ModelTrainer` for training orchestration.
- Prefer current config imports from `sagemaker.core.training.configs` for
  `SourceCode`, `Compute`, `InputData`, `StoppingCondition`, `OutputDataConfig`,
  `CheckpointConfig`, and `Networking`. Some examples use
  `sagemaker.train.configs`; it is a v3 compatibility shim in this repo.
- Use `from sagemaker.core import image_uris` and
  `image_uris.retrieve(...)` for framework image URI resolution.
- Use `Session()` and `get_execution_role()` from
  `sagemaker.core.helper.session_helper` rather than hardcoded buckets, regions,
  account IDs, or role ARNs.
- Use placeholders such as `<training-image-uri>`, `<role-name-or-arn>`, and
  `s3://<bucket>/<prefix>` when exact customer resources are unknown.
- Do not introduce v2 `Estimator`, framework estimator classes, `fit()`, v2
  `Model`, v2 `Predictor`, v2 `Processor`, or old workflow imports except in an
  explicitly labeled deprecated migration note.

## Short workflow

1. Classify the training task: single-job ModelTrainer, local container,
   distributed, JumpStart, HPO, AWS Batch queue, remote function, or migration.
2. Confirm required execution substrate: no-submit config drafting, Docker local
   mode, SageMaker cloud job, AWS Batch queue, or MLOps pipeline.
3. Establish AWS prerequisites if any cloud job may be submitted: region,
   credentials, execution role, S3 staging/output location, ECR image access,
   service quotas, and IAM permissions.
4. Build config objects first: `SourceCode`, `Compute`, `InputData`,
   `StoppingCondition`, optional `Networking`, `OutputDataConfig`,
   `CheckpointConfig`, and optional distributed config.
5. Resolve the training image with `image_uris.retrieve(...)` or accept a
   user-provided custom image URI placeholder.
6. Construct `ModelTrainer(...)`; set `role` explicitly outside SageMaker managed
   notebooks if automatic role discovery is not guaranteed.
7. Validate before spend: prefer `trainer.train(..., dry_run=True)` for cloud
   job configuration checks; for local mode also verify Docker/compose and local
   paths before calling `train()`.
8. Submit only when authorized: `train(wait=True, logs=True)` for a blocking job,
   `train(wait=False, logs=False)` for fire-and-check-later, or use HPO/Batch
   entry points when the task requires them.
9. After training, route deployment to
   [`../serving/SKILL.md`](../serving/SKILL.md) and route pipeline integration to
   [`../mlops/SKILL.md`](../mlops/SKILL.md).

## Reference map

- [`references/modeltrainer-workflows.md`](references/modeltrainer-workflows.md):
  ModelTrainer signatures, imports, region/role/session setup, image retrieval,
  hyperparameters, local/SageMaker training, JumpStart, and validation.
- [`references/distributed-training.md`](references/distributed-training.md):
  Torchrun, MPI, SMP, custom `DistributedConfig`, driver environment variables,
  local multi-container training, and distributed troubleshooting.
- [`references/hyperparameter-tuning.md`](references/hyperparameter-tuning.md):
  `HyperparameterTuner`, parameter ranges, metrics, `tune()`, `analytics()`,
  warm starts/autotune, and MLOps handoff.
- [`references/remote-function-and-advanced-training.md`](references/remote-function-and-advanced-training.md):
  AWS Batch `TrainingQueue`, remote function and `RemoteExecutor`, container
  driver concepts, queue monitoring, and advanced routing boundaries.
- [`references/troubleshooting.md`](references/troubleshooting.md):
  region, credentials, role, Docker/local mode, image URI, source packaging,
  hyperparameters, distributed, HPO, JumpStart, Batch, and remote-function fixes.

## Migration guardrail

Deprecated v2 training patterns map as follows; keep details concise here and
route broader migrations to [`../../references/migration-v2-to-v3.md`](../../references/migration-v2-to-v3.md).

- Deprecated `sagemaker.estimator.Estimator` -> v3 `sagemaker.train.ModelTrainer`.
- Deprecated framework estimators such as PyTorch, TensorFlow, SKLearn, XGBoost,
  and HuggingFace classes -> v3 `ModelTrainer` plus `image_uris.retrieve(...)`.
- Deprecated `estimator.fit(...)` -> v3 `model_trainer.train(...)` with
  `InputData(channel_name=..., data_source=...)`.
- Deprecated `instance_type`/`instance_count` on estimators -> v3
  `Compute(instance_type=..., instance_count=...)`.
- Deprecated `entry_point`/`source_dir` estimator parameters -> v3
  `SourceCode(entry_script=..., source_dir=...)`.

## Quality checks before returning training guidance

- Confirm examples use v3 imports and do not contain real account IDs, role
  ARNs, bucket names, subnet IDs, security group IDs, regions hardcoded as the
  only option, or credentials.
- If examples use `sagemaker.train.configs`, consider replacing with
  `sagemaker.core.training.configs` unless compatibility with an existing
  notebook is the explicit goal.
- Verify `SourceCode.source_dir` contains the named `entry_script` and optional
  `requirements` file, or explain that cloud validation will fail.
- For local mode, say Docker and Docker Compose are required and set
  `local_container_root` deliberately when output location matters.
- For distributed jobs, require `source_code.entry_script` and pick one driver:
  `Torchrun`, `MPI`, or a custom `DistributedConfig`.
- For HPO, define metric regexes that match the training script logs and use
  `tuner.analytics()` only after a tuning job exists.
- For AWS Batch, require `Mode.SAGEMAKER_TRAINING_JOB`; Batch queues do not
  accept local-container ModelTrainer jobs.

## Common safe defaults

- Start with `Compute(instance_type="ml.m5.xlarge", instance_count=1)` for CPU
  examples unless the user asks for GPU or a framework requires GPU.
- Use `StoppingCondition(max_runtime_in_seconds=3600)` in examples to bound cost.
- Use `Session().boto_region_name` for region and `Session().default_bucket()`
  for sample S3 URI assembly.
- Use `dry_run=True` when the user asks to validate configuration without
  launching a chargeable job.
- Use `wait=False` only when the user wants asynchronous submission and you also
  show how to inspect or wait for the resulting job/tuner/queue object.

## Handoff after training

- For deployment from a completed training job or model artifact, load
  [`../serving/SKILL.md`](../serving/SKILL.md).
- For a train/tune step inside a SageMaker Pipeline, load
  [`../mlops/SKILL.md`](../mlops/SKILL.md).
- For low-level inspection of `TrainingJob` resources or image URI behavior,
  load [`../core-resources/SKILL.md`](../core-resources/SKILL.md).
- For foundation model customization/evaluation recipes, do not duplicate here;
  load [`../model-customization/SKILL.md`](../model-customization/SKILL.md).
