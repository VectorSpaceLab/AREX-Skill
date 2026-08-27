---
name: model-customization
description: "Use SageMaker Python SDK v3 foundation-model customization,
  evaluation, AI Registry assets, recipe overrides, data mixing, notifications,
  and Agentic RFT workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# SageMaker Python SDK v3 Model Customization Sub-skill

Use this sub-skill for foundation model customization with the specialized
`SFTTrainer`, `DPOTrainer`, `RLVRTrainer`, `RLAIFTrainer`, `CPTTrainer`, and
`MultiTurnRLTrainer` APIs, plus evaluation jobs, AI Registry datasets and
evaluators, Nova data mixing, recipe overrides, notifications, and job
monitoring.

## Trigger phrases

Read this sub-skill when the user asks to:

- fine-tune, customize, or align a foundation model with SageMaker v3
- use `SFTTrainer`, `DPOTrainer`, `RLVRTrainer`, `RLAIFTrainer`, `CPTTrainer`,
  or `MultiTurnRLTrainer`
- run Nova data mixing, recipe overrides, or `get_resolved_recipe()`
- validate a training or evaluation config with `dry_run=True`
- create or use AI Registry `DataSet` or `Evaluator` assets
- launch benchmark, custom-scorer, LLM-as-judge, InspectAI, or multi-turn RL
  evaluations
- configure SNS/EventBridge notifications for training jobs
- inspect `show_metrics()`, `stream_logs()`, or `AgentRFTJob` artifacts

## When not to read this sub-skill

- Generic training jobs, local training, distributed training, HPO, or JumpStart
  training: use [`../training/SKILL.md`](../training/SKILL.md).
- Deploying a customized model to an endpoint, local container, or Bedrock
  serving path: use [`../serving/SKILL.md`](../serving/SKILL.md).
- Session/default-bucket/image URI/resource-chain questions: use
  [`../core-resources/SKILL.md`](../core-resources/SKILL.md).
- Pipeline orchestration, registry workflows outside evaluation assets, feature
  store, or governance steps: use [`../mlops/SKILL.md`](../mlops/SKILL.md).

## Short workflow

1. Identify the task family: SFT, DPO, RLVR, RLAIF, CPT, or MultiTurnRL.
2. Pick the compute path:
   - serverless when `compute=None`
   - `TrainingJobCompute`/`Compute` for serverful SMTJ
   - `HyperPodCompute` for cluster-backed jobs
   - CPT is HyperPod-only
   - MultiTurnRL uses `agent_env` and `AgentRFTJob`, not `TrainingJobCompute`
3. Use the right asset type:
   - `DataSet` for registered training/evaluation data
   - `Evaluator` for reward functions, reward prompts, or judge assets
   - `DataMixingConfig` for Nova data mixing
4. Resolve recipe and validation intent early with `get_resolved_recipe()` and
   `dry_run=True` before launching a chargeable job.
5. Keep `accept_eula=True` and explicit role / region / S3 outputs ready for
   gated models and cloud execution.
6. After submission, inspect logs and metrics with `stream_logs()` and
   `show_metrics()`; for MTRL inspect the returned `AgentRFTJob`.
7. When the task becomes deployment, hand it to
   [`../serving/SKILL.md`](../serving/SKILL.md).

## Reference map

- [`references/foundation-model-customization.md`](references/foundation-model-customization.md):
  specialized trainer APIs, compute choices, recipes, data mixing, dry-run, logs,
  and model-specific operating patterns.
- [`references/evaluation-and-ai-registry.md`](references/evaluation-and-ai-registry.md):
  evaluator classes, evaluation execution objects, AI Registry `DataSet` and
  `Evaluator` assets, and multi-turn RL artifacts.
- [`references/recipes-data-mixing-notifications.md`](references/recipes-data-mixing-notifications.md):
  recipe precedence, `get_resolved_recipe()`, `DataMixingConfig`, notifications,
  metrics, and log streaming after restart.
- [`references/troubleshooting.md`](references/troubleshooting.md):
  region, credentials, role, EULA, model access, data validation, recipe,
  notification, and evaluation failure recovery.

## Quick API map

- Training: `SFTTrainer`, `DPOTrainer`, `RLVRTrainer`, `RLAIFTrainer`,
  `CPTTrainer`, `MultiTurnRLTrainer`, `TrainingType`, `CustomizationTechnique`.
- Data and assets: `DataMixingConfig`, `DataSet`, `Evaluator`.
- Evaluation: `BenchMarkEvaluator`, `CustomScorerEvaluator`,
  `LLMAsJudgeEvaluator`, `InspectAIEvaluator`, `MultiTurnRLEvaluator`,
  `EvaluationPipelineExecution`.
- Monitoring: `show_metrics()`, `stream_logs()`, `plot_training_metrics()`,
  `AgentRFTJob.get_training_metrics()`.

## Guardrails

- Use v3 imports only.
- Do not hardcode account IDs, region names, role ARNs, bucket names, subnets,
  or credentials in public guidance.
- Keep deployment guidance out of this sub-skill; route customized-model serving
  to the sibling serving sub-skill.
- If you only need general `ModelTrainer` flow, leave this sub-skill and use the
  training sub-skill instead.
