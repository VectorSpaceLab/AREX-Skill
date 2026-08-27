---
name: serving
description: "Use SageMaker Python SDK v3 serving workflows for ModelBuilder,
  local inference, JumpStart, optimization, Bedrock, and inference recommender."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SageMaker Python SDK v3 Serving Sub-skill

Use this sub-skill for model deployment and inference with `sagemaker-serve`.
It covers `ModelBuilder`, `InferenceSpec`, `SchemaBuilder`, `ModelServer`,
`build()`, `deploy()`, `deploy_local()`, local container mode, in-process mode,
JumpStart deployment, train-to-inference, optimization, recommendation-driven
deployments, Bedrock deployment, and inference pipelines.

## Trigger phrases

Read this sub-skill when the user says or implies:

- deploy a model, serve a model, or create an endpoint
- `ModelBuilder`, `ModelServer`, `InferenceSpec`, or `SchemaBuilder`
- `deploy_local()`, local container mode, or in-process mode
- real-time, serverless, async, or batch transform deployment
- train-to-inference or deploy from `ModelTrainer` / `TrainingJob`
- JumpStart deployment or `ModelBuilder.from_jumpstart_config(...)`
- optimization, quantization, compilation, sharding, or speculative decoding
- `BedrockModelBuilder` or deployment to Amazon Bedrock
- inference recommender, right sizing, or deployment recommendations
- inference pipelines, multi-container serving, or chained models

## Read this when

- You need the v3 deployment flow built around `ModelBuilder`.
- You need a custom `InferenceSpec` or `SchemaBuilder` for request/response
  marshalling.
- You need local testing without cloud calls, either in Docker or in-process.
- You need JumpStart, train-to-inference, optimization, or Bedrock serving.
- You need recommendation-driven deployment selection before creating an endpoint.

## Do not read this when

- You need `ModelTrainer` setup, training jobs, distributed training, or HPO;
  use [`../training/SKILL.md`](../training/SKILL.md).
- You need low-level `Endpoint`, `EndpointConfig`, `TransformJob`, or direct
  resource chaining; use [`../core-resources/SKILL.md`](../core-resources/SKILL.md).
- You need foundation-model customization or evaluation first; use
  [`../model-customization/SKILL.md`](../model-customization/SKILL.md).
- You need SageMaker Pipelines or workflow orchestration; use
  [`../mlops/SKILL.md`](../mlops/SKILL.md).

## Short workflow

1. Identify the source of the serving artifact: raw model object, trained job,
   `ModelTrainer`, JumpStart config, custom `InferenceSpec`, or fine-tuned
   model package.
2. Pick the transport contract early: define `SchemaBuilder(sample_input,
   sample_output)` or a custom `InferenceSpec.load()` / `invoke()` pair. If the
   runtime should serialize itself, choose the right `content_type` and
   `accept_type` up front.
3. Build with `ModelBuilder(...)` or `ModelBuilder.from_jumpstart_config(...)`.
   If the source is a `ModelTrainer` or `TrainingJob`, make sure training has
   completed before build.
4. Choose the deployment mode:
   - `Mode.SAGEMAKER_ENDPOINT` for cloud serving
   - `Mode.LOCAL_CONTAINER` for Docker-based local serving
   - `Mode.IN_PROCESS` for pure Python local serving
5. Use `build()` before `deploy()` for normal serving flows. Use
   `deploy_local()` only for `LOCAL_CONTAINER` or `IN_PROCESS`.
6. Route the deployment type:
   - no `inference_config` or `ServerlessInferenceConfig` / `AsyncInferenceConfig`
     -> real-time `Endpoint`
   - `BatchTransformInferenceConfig` -> `Transformer`
   - `ResourceRequirements` -> inference-component-based endpoint path
7. Invoke with `endpoint.invoke(body=..., content_type=..., accept=...)` or
   `local_endpoint.invoke(...)`. Keep transport examples self-contained and use
   placeholders for all real AWS identifiers.
8. For optimization, recommendations, or Bedrock, read the dedicated reference
   before calling `optimize()`, `generate_deployment_recommendations()`, or
   `BedrockModelBuilder.deploy()`.
9. If the request becomes a low-level endpoint or batch job task, hand it off
   to the sibling sub-skill instead of expanding this one.

## Verified API surface

Use these signatures as the source of truth for runtime-safe guidance:

- `ModelBuilder(...)`
- `ModelBuilder.build(...)`
- `ModelBuilder.deploy(...)`
- `ModelBuilder.deploy_local(...)`
- `ModelBuilder.optimize(...)`
- `ModelBuilder.from_jumpstart_config(...)`
- `InferenceSpec.load(...)` / `InferenceSpec.invoke(...)`
- `SchemaBuilder(...)`
- `BedrockModelBuilder.deploy(...)`

See the bundled references for the full verified signatures and examples.

## Common guardrails

- Use v3 imports only. Do not introduce v2 `Model`, `Predictor`, `Processor`,
  or `Estimator` patterns except in a clearly labeled deprecated migration note.
- Do not hardcode real account IDs, role ARNs, regions, bucket names, subnet
  IDs, security group IDs, or credentials.
- Remember that `ModelBuilder` may resolve a role during construction if no
  `role_arn` is provided; without credentials, that can fail before `build()` or
  `deploy()` runs.
- Prefer `endpoint.invoke()` over deprecated `predictor.predict()` patterns.
- If a user asks for `Endpoint` or `TransformJob` creation directly, route to
  `../core-resources/SKILL.md`.

## Reference map

- [`references/modelbuilder-workflows.md`](references/modelbuilder-workflows.md)
- [`references/deployment-modes-and-inference-spec.md`](references/deployment-modes-and-inference-spec.md)
- [`references/optimization-bedrock-and-recommendations.md`](references/optimization-bedrock-and-recommendations.md)
- [`references/troubleshooting.md`](references/troubleshooting.md)

## Handoff notes

- Keep detailed APIs, matrices, and failure recovery in the references.
- Keep this file router-like: classify the request, point to the right flow,
  and stop.
- When a deployment question crosses into training, model customization, or
  low-level resources, hand off to the sibling sub-skill instead of duplicating
  that logic here.
