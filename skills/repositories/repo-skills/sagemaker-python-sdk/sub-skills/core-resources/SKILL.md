---
name: core-resources
description: "Use SageMaker Python SDK v3 core resources for sessions, URI
  retrieval, low-level jobs and endpoints, serverless endpoint config, and
  lineage."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SageMaker Python SDK v3 Core Resources Sub-skill

Use this sub-skill when the task is about foundational `sagemaker-core` APIs:
`Session`, `get_execution_role`, image/model/script URI retrieval, direct
resource objects, processing jobs, batch transform jobs, endpoint lifecycle,
direct training jobs, hyperparameter tuning jobs, serverless or async endpoint
config, resource chaining, or lineage primitives.

## Trigger phrases

- "core resources", "sagemaker-core", "low-level resource", or "resource object".
- "Session", "default bucket", "get_execution_role", `boto_region_name`, or AWS profile.
- "image URI", `image_uris.retrieve`, `model_uris.retrieve`, or `script_uris.retrieve`.
- "ProcessingJob", "batch transform", "TransformJob", or "offline inference".
- "Model", "EndpointConfig", "Endpoint", "invoke", or "update_weights_and_capacities".
- "TrainingJob" or "HyperParameterTuningJob" when the user wants the low-level API.
- "serverless endpoint config", `ProductionVariantServerlessConfig`, or `AsyncInferenceConfig`.
- "resource chaining", "pass a resource object through", or "get_all / refresh / delete".
- "lineage", `sagemaker.core.lineage`, `Context`, `Action`, `Artifact`, or `Association`.
- "migrate from v2 imports" for `sagemaker.session`, `sagemaker.processing`,
  `sagemaker.transformer`, `sagemaker.tuner`, `sagemaker.model`,
  `sagemaker.predictor`, `sagemaker.image_uris`, `sagemaker.model_uris`,
  `sagemaker.script_uris`, or `sagemaker.lineage`.

## Read this when

- The request is direct SageMaker resource management and not a high-level
  `ModelTrainer`, `ModelBuilder`, or MLOps pipeline workflow.
- The user wants a v3 replacement for removed v2 modules or legacy low-level
  calls.
- The task is to create, list, refresh, delete, wait on, or invoke core
  resources.
- The task is to retrieve managed framework images or JumpStart model/script
  artifacts.
- The task is to construct lineage graphs, query associations, or clean up
  lineage entities.

## Do not read this when

- The user wants general training orchestration, local training, distributed
  training, JumpStart training, or HPO with `ModelTrainer`; use
  [`../training/SKILL.md`](../training/SKILL.md).
- The user wants high-level deployment with `ModelBuilder`, inference schema
  inference, in-process serving, or optimization; use
  [`../serving/SKILL.md`](../serving/SKILL.md).
- The user wants SageMaker Pipelines, registry flows, feature store, Clarify,
  or workflow orchestration; use [`../mlops/SKILL.md`](../mlops/SKILL.md).
- The user wants foundation-model customization or evaluation trainers; use
  [`../model-customization/SKILL.md`](../model-customization/SKILL.md).

## Non-negotiable v3 guardrails

- Use `sagemaker.core`, `sagemaker.train`, `sagemaker.serve`, and
  `sagemaker.mlops` imports by default; do not introduce v2 imports in new
  guidance except in explicitly labeled deprecated migration notes.
- Prefer the SDK over raw `boto3.client("sagemaker").create_*` calls for normal
  SageMaker tasks. Raw boto3 is an escape hatch only for unsupported APIs or
  when the user explicitly asks for the service call.
- Do not hardcode real account IDs, role ARNs, regions, bucket names, subnet
  IDs, security group IDs, or credentials. Use `Session()`,
  `get_execution_role()`, `Session().default_bucket()`, placeholders, or AWS
  configuration.
- Treat `create`, `update`, `delete`, `invoke`, and `wait` as cloud operations.
- Old `sagemaker.lineage.*` imports are deprecated compatibility shims. Prefer
  `sagemaker.core.lineage.*` for new lineage code.
- For low-level serverless endpoints, use `ProductionVariantServerlessConfig`
  inside `ProductionVariant`; reserve `ServerlessInferenceConfig` for helper
  flows and higher-level deployment code.

## Short workflow

1. Classify the request. If it is clearly ModelTrainer, ModelBuilder, or MLOps
   orchestration, route to the sibling sub-skill instead of staying here.
2. Establish AWS prerequisites: region, credentials/profile, execution role,
   default bucket/prefix, and whether live service calls are authorized.
3. Create a `Session` and verify `session.boto_region_name`. Use
   `get_execution_role(session)` only when role discovery is expected to work;
   otherwise pass an explicit role ARN.
4. Resolve artifacts with `image_uris.retrieve`, `model_uris.retrieve`, or
   `script_uris.retrieve`. For JumpStart URIs, require `model_id` and
   `model_version`. For serverless image selection, pass a serverless config.
5. Build typed request shapes from `sagemaker.core.shapes` and
   `sagemaker.core.inference_config`.
6. Pick the resource API:
   - `ProcessingJob.create/get/get_all/wait`
   - `TransformJob.create/get/get_all/wait`
   - `TrainingJob.create/get/get_all/wait`
   - `Model.create/get/get_all/delete`
   - `EndpointConfig.create/get/get_all`
   - `Endpoint.create/get/get_all/wait_for_status/invoke/update_weights_and_capacities`
   - `HyperParameterTuningJob.create/get/get_all/wait`
7. Prefer resource chaining when the signature accepts `object` or
   `PipelineVariable`. Pass upstream resource objects directly, then fall back
   to `get_name()` or `.name` only when the target field requires a plain string.
8. For endpoints, create an `EndpointConfig` first, then `Endpoint`, then wait
   for `InService` before invoking.
9. For lineage, use `sagemaker.core.lineage`, delete associations before
   deleting entities, and prefer the new import path over the legacy shim.
10. Validate before returning: v3 imports only, no hardcoded real identifiers,
    cleanup path included, and any billable resources have a delete plan.

## Reference map

- Detailed signatures, imports, and resource semantics:
  [`references/api-reference.md`](references/api-reference.md).
- End-to-end operational recipes:
  [`references/workflows.md`](references/workflows.md).
- Error boundaries, recovery advice, and migration notes:
  [`references/troubleshooting.md`](references/troubleshooting.md).

## Handoff expectations

- Produce self-contained v3 guidance; do not require the original repository
  checkout at runtime.
- Make all AWS calls explicit and distinguish them from local object
  construction.
- Keep cleanup steps in any example that creates jobs, endpoints, or lineage
  entities.
- If a user gives v2 code, convert it to v3 and label the v2 original as
  deprecated before showing the replacement.
