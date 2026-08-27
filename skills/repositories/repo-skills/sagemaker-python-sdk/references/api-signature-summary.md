# SageMaker Python SDK v3 API signature summary

This summary captures the verified import and signature facts from the local
inspection environment that was used to draft this repo skill. Treat it as a
compact runtime reference, not as a full API spec.

## Verified import surface

The inspection environment successfully imported:

- `sagemaker`
- `sagemaker.core`
- `sagemaker.train`
- `sagemaker.serve`
- `sagemaker.mlops`
- `sagemaker.ai_registry.dataset`
- `sagemaker.train.evaluate`
- `sagemaker.mlops.feature_store`

Import caveats:

- `sagemaker.serve` and `sagemaker.mlops` need `AWS_REGION` or
  `AWS_DEFAULT_REGION` in a fresh environment.
- `ModelTrainer` and `ModelBuilder` can attempt role discovery through STS when
  no explicit role is supplied.
- `EMRServerlessStep` lives in
  `sagemaker.mlops.workflow.emr_serverless_step` and is not re-exported from
  `sagemaker.mlops.workflow.__init__` in this runtime.

## Verified training signatures

- `ModelTrainer.train(input_data_config=None, wait=True, logs=True, dry_run=False)`
- `ModelTrainer.from_jumpstart_config(...)`
- `HyperparameterTuner` is the v3 tuning surface on top of `ModelTrainer`
- `TrainingQueue` and `RemoteExecutor` are available for the advanced AWS Batch
  and remote-function paths
- Specialized trainers available in this checkout:
  `SFTTrainer`, `DPOTrainer`, `RLVRTrainer`, `RLAIFTrainer`, `CPTTrainer`,
  `MultiTurnRLTrainer`

## Verified serving signatures

- `ModelBuilder(...)`
- `ModelBuilder.build(...)`
- `ModelBuilder.deploy(...)`
- `ModelBuilder.deploy_local(...)`
- `ModelBuilder.optimize(...)`
- `ModelBuilder.generate_deployment_recommendations(...)`
- `ModelBuilder.from_jumpstart_config(...)`
- `InferenceSpec.load(...)`
- `InferenceSpec.invoke(...)`
- `SchemaBuilder(sample_input, sample_output, input_translator=None, output_translator=None)`
- `BedrockModelBuilder.deploy(...)`
- `start_benchmark(...)`
- `BenchmarkJob` and `RecommendationJob`

## Verified core resource surface

- `Session`
- `get_execution_role`
- `image_uris.retrieve(...)`
- `model_uris.retrieve(...)`
- `script_uris.retrieve(...)`
- `Processor`, `ScriptProcessor`, `FrameworkProcessor`, `Transformer`
- `ProcessingJob.create/get/get_all/wait`
- `TransformJob.create/get/get_all/wait`
- `TrainingJob.create/get/get_all/wait`
- `Model.create/get/get_all/delete`
- `EndpointConfig.create/get/get_all`
- `Endpoint.create/get/get_all/wait_for_status/invoke/update_weights_and_capacities`
- `HyperParameterTuningJob.create/get/get_all/wait`
- `sagemaker.core.lineage` primitives such as `Context`, `Action`, `Artifact`,
  and `Association`

## Verified workflow surface

The local environment confirmed these `sagemaker.mlops.workflow` exports:

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

## Validation notes

- `DataMixingConfig` requires Nova percentages to sum to 100.
- `sagemaker.train.configs` exists as a compatibility shim; prefer the newer
  core training config module when possible.
- The imported packages were validated with editable local installs in the
  inspection environment; cloud execution was not part of the import smoke.

## Where to go next

- Training workflows: `../sub-skills/training/SKILL.md`
- Model customization workflows: `../sub-skills/model-customization/SKILL.md`
- Serving workflows: `../sub-skills/serving/SKILL.md`
- MLOps workflows: `../sub-skills/mlops/SKILL.md`
- Core resources: `../sub-skills/core-resources/SKILL.md`
