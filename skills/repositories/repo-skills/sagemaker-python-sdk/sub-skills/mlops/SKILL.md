---
name: mlops
description: "Use SageMaker Python SDK v3 MLOps workflows for Pipeline
  orchestration, workflow steps, model registry, monitoring, lineage, triggers,
  and feature store."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SageMaker Python SDK v3 MLOps Sub-skill

Use this sub-skill for `sagemaker-mlops` workflow orchestration. It covers
pipeline definition, step composition, registry flows, monitoring, lineage,
triggers, feature-store-oriented orchestration, and local pipeline execution
limits.

## Trigger phrases

Read this sub-skill when the user says or implies:

- pipeline orchestration, workflow orchestration, or SageMaker Pipelines
- `Pipeline`, `PipelineExecution`, or `PipelineGraph`
- `TrainingStep`, `ProcessingStep`, `TransformStep`, or `TuningStep`
- `ModelStep`, `ConditionStep`, `LambdaStep`, `CallbackStep`, or `FailStep`
- `QualityCheckStep`, `ClarifyCheckStep`, or `MonitorBatchTransformStep`
- `AutoMLStep`, `EMRStep`, `NotebookJobStep`, or `EMRServerlessStep`
- `PipelineSchedule`, triggers, selective execution, retries, or cache config
- model registry, approval workflow, baseline registration, or pipeline gating
- feature store orchestration, `FeatureGroupManager`, or `DatasetBuilder`
- lineage, governance, `sagemaker.core.lineage`, or Lake Formation / Iceberg

## Read this when

- You need to compose a production ML workflow that spans preprocessing,
  training, transform, registry, checks, or triggers.
- You need pipeline DAGs, retries, caching, selective execution, or execution
  inspection.
- You need feature-store orchestration, registry wiring, or governance hooks.
- You need lineage and compliance tracking around a workflow.

## Do not read this when

- You only need low-level jobs or resources such as `ProcessingJob`,
  `TrainingJob`, `TransformJob`, `Endpoint`, or `FeatureGroup` CRUD; use
  [`../core-resources/SKILL.md`](../core-resources/SKILL.md).
- You need to build training `step_args`; use [`../training/SKILL.md`](../training/SKILL.md).
- You need deployment or inference with `ModelBuilder`; use
  [`../serving/SKILL.md`](../serving/SKILL.md).
- You need foundation-model customization or evaluation workflows; use
  [`../model-customization/SKILL.md`](../model-customization/SKILL.md).

## Non-negotiable v3 guardrails

- Use `from sagemaker.mlops.workflow import ...` or explicit workflow modules.
- Do not introduce legacy `sagemaker.workflow.*` imports unless you are writing
  a deprecated migration note and you also give the v3 replacement.
- Keep examples self-contained and placeholder-only.
- If a workflow needs `PipelineSession`, construct it from `sagemaker.core`.
- `EMRServerlessStep` exists in
  `sagemaker.mlops.workflow.emr_serverless_step` but is not re-exported from
  `sagemaker.mlops.workflow.__all__` in this runtime build.
- Set `AWS_DEFAULT_REGION` or `AWS_REGION` before importing or constructing
  high-level workflow objects in a fresh environment.

## Verified API surface

Use these verified imports and signatures from the inspection env as the source
of truth:

- `Pipeline(name='', parameters=None, pipeline_experiment_config=..., mlflow_config=None, steps=None, sagemaker_session=None, pipeline_definition_config=...)`
- `PipelineExecution(arn, sagemaker_session=Session())`
- `PipelineGraph(steps)` and `PipelineGraph.from_pipeline(pipeline)`
- `TrainingStep(name, step_args=None, display_name=None, description=None, cache_config=None, depends_on=None, retry_policies=None)`
- `ProcessingStep(...)`, `TransformStep(...)`, and `TuningStep(...)`
- `ModelStep(name, step_args, depends_on=None, retry_policies=None, display_name=None, description=None, repack_model_step_settings=None)`
- `ConditionStep(name, depends_on=None, display_name=None, description=None, conditions=None, if_steps=None, else_steps=None)`
- `QualityCheckStep(...)`, `ClarifyCheckStep(...)`, `AutoMLStep(...)`, `EMRStep(...)`, `NotebookJobStep(...)`, `CallbackStep(...)`, `LambdaStep(...)`, `FailStep(...)`
- `MonitorBatchTransformStep(...)`
- `CacheConfig(enable_caching=False, expire_after=None)`
- `RetryPolicy(...)`, `StepRetryPolicy(...)`, and `SageMakerJobStepRetryPolicy(...)`
- `ParallelismConfiguration(max_parallel_execution_steps)`
- `SelectiveExecutionConfig(selected_steps, reference_latest_execution=True, source_pipeline_execution_arn=None)`
- `PipelineExperimentConfig(experiment_name, trial_name)`
- `PipelineDefinitionConfig(use_custom_job_prefix)`
- `PipelineSchedule(name=None, enabled=True, start_date=None, at=None, rate=None, cron=None)`
- `Trigger(name=None, enabled=True)`
- `CheckJobConfig(role, instance_count=1, instance_type='ml.m5.xlarge', volume_size_in_gb=30, volume_kms_key=None, output_kms_key=None, max_runtime_in_seconds=None, base_job_name=None, sagemaker_session=None, env=None, tags=None, network_config=None)`

## Short workflow

1. Classify the task: pipeline assembly or execution control, monitoring or
   governance, feature store or registry orchestration, or EMR / notebook /
   callback / Lambda routing.
2. Identify the upstream step args. Do not build them here:
   - `processor.run(...)` from [`../core-resources/SKILL.md`](../core-resources/SKILL.md)
   - `model_trainer.train(...)` from [`../training/SKILL.md`](../training/SKILL.md)
   - `transformer.transform(...)` from [`../core-resources/SKILL.md`](../core-resources/SKILL.md)
   - `model_builder.build()` / `register()` from [`../serving/SKILL.md`](../serving/SKILL.md)
3. Import only the workflow classes needed for the branch you are building.
4. Create `PipelineSession`, parameters, property files, retry policies, cache
   config, and selective-execution settings as required.
5. Wire step dependencies by using upstream `step_args` and `properties`,
   especially `ProcessingStep` property files plus `JsonGet` for conditions.
6. Use `Pipeline.create()`, `update()`, `upsert()`, and `start()` in the correct
   order. `PipelineExecution` is for inspection after start.
7. For feature store, choose `FeatureGroupManager` when Lake Formation or Iceberg
   governance is part of the task; otherwise prefer the core `FeatureGroup`
   resource and helper functions.
8. For lineage, create `Context` / `Action` / `Artifact` / `Association` records
   with `sagemaker.core.lineage`, not the old shim.
9. Validate against local-mode limits before returning. If the workflow crosses
   into lower-level resources, training config construction, or deployment, hand
   off to the sibling sub-skill.

## Reference map

- [`references/pipeline-workflows.md`](references/pipeline-workflows.md)
- [`references/processing-feature-store-and-registry.md`](references/processing-feature-store-and-registry.md)
- [`references/lineage-monitoring-and-governance.md`](references/lineage-monitoring-and-governance.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)

## Handoff notes

- Keep this file router-like; put recipes, matrices, and failure recovery in the
  references.
- Do not link to the source checkout from runtime guidance.
- Use v3 replacements when the task mentions v2 pipeline, workflow,
  feature-store, or lineage APIs.
- Mention any unsupported local-mode or optional-dependency path explicitly.
- If a user asks for a direct `FeatureGroup`, `TrainingJob`, `TransformJob`,
  `Endpoint`, `ModelBuilder`, or `ModelTrainer` build path, route to the sibling
  sub-skill instead of expanding this one.
