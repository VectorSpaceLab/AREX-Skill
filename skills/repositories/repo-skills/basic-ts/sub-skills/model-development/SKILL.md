---
name: "model-development"
description: "Routes BasicTS built-in model selection and custom model
  authoring, including forward contracts, config classes, and auxiliary-loss
  behavior."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# model-development

Use this sub-skill when the task is about choosing a BasicTS model family, understanding a model config, or authoring a new model that BasicTS can run.

## Typical triggers

- "Which BasicTS model should I use?"
- "How do I implement a custom BasicTS model?"
- "What does a BasicTS model need to return?"
- "How do auxiliary losses work?"
- "Check whether this model matches the BasicTS contract"

## What this sub-skill covers

- built-in model families under `src/basicts/models/`
- model config classes such as `DLinearConfig`, `iTransformerConfig`, `TimesNetConfig`, and `PatchTSTConfig`
- the BasicTS forward contract for `inputs`, optional timestamps, masks, and training-step metadata
- output expectations for prediction tensors, dictionaries, and optional `loss` or auxiliary-loss keys
- CPU-side contract inspection for custom models

## Read these bundled references first

- `references/model-catalog.md` for model families, task support, and entry-point names.
- `references/custom-model-contract.md` for the forward/output contract and custom model checklist.
- `references/troubleshooting.md` for shape, signature, and callback failures.
- `scripts/check_model_contract.py` for a safe inspection helper.

## Route here when the user asks for

- built-in model selection for forecasting, classification, or imputation
- the difference between `*_ForForecasting`, `*_ForClassification`, and `*_ForReconstruction`
- how to implement a custom model class that BasicTS can train or evaluate
- how to inspect a model's accepted inputs or output structure
- how to wire auxiliary losses from the model into the BasicTS callback path

## Route elsewhere when the user asks for

- dataset folders, raw arrays, or conversion scripts → `data-preparation`
- launcher commands, configs, or checkpoint usage → `training-evaluation`
- callbacks, metrics, scalers, taskflows, or config serialization beyond the model contract → `pipeline-extension`

## Working guidance

1. Confirm the target task family first.
2. Pick a built-in model wrapper that matches the task if one exists.
3. Make sure the model's `forward` accepts `inputs` and any extra keys it needs.
4. Return a tensor or a dictionary with `prediction`.
5. If the model computes its own loss, document how that interacts with the BasicTS runner and callbacks.

## When to read the helper script

Use `scripts/check_model_contract.py` when you want to inspect a model class from the installed package, print its forward signature, or run a small dummy forward check.

## Why this sub-skill exists

BasicTS model usage is broader than a single model family. This sub-skill keeps the built-in catalog and the custom model contract separate from dataset and training concerns so future agents can answer model questions quickly and accurately.
