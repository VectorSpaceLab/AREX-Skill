---
name: auto-ml
description: "Use Igel's AutoKeras-backed Auto-ML helpers for image, text, and
  structured-data task selection, IgelCNN train/evaluate/predict behavior, and
  current Auto-ML CLI caveats."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Auto-ML

Use this sub-skill when the task is about Igel's AutoKeras path: `IgelCNN`, `igel.auto.models.Models.get`, image classification/regression, text classification/regression, structured-data AutoKeras task names, or the documented-but-missing `igel auto-train` command.

Start here:

- Use [references/api-reference.md](references/api-reference.md) for exact `IgelCNN` constructor/method behavior, save/load assumptions, and supported task names.
- Use [references/workflows.md](references/workflows.md) for the safe operating sequence, directory layouts, and bounded examples.
- Use [references/troubleshooting.md](references/troubleshooting.md) when imports, task names, data layout, artifacts, or CLI expectations fail.
- Use [scripts/inspect_auto_ml.py](scripts/inspect_auto_ml.py) for an import/signature/task-selector smoke check that does not train, download data, or require the original source checkout.

Route boundaries:

1. Route classic CSV/tabular `igel fit`, `evaluate`, `predict`, `experiment`, `models`, `metrics`, and ONNX/export work to [tabular-workflows](../tabular-workflows/SKILL.md); those are not AutoKeras workflows.
2. Route repo-wide skill selection back to the [root router](../../SKILL.md) when the user is not clearly asking for Auto-ML.
3. Route FastAPI serving, Docker, GUI, and client-request tasks away from this sub-skill; this sub-skill only covers the AutoKeras-backed training/evaluation/prediction helpers and task registry.
4. Treat AutoKeras training as potentially expensive. Prefer import/signature and task-selector checks before starting any run, and never make dataset downloads or long tuning loops the default helper path.
5. Do not rely on `igel auto-train` as a real current Click CLI command. The docs mention it, but the current CLI surface does not expose that command; use the programmatic `IgelCNN` path or route to classic tabular commands when appropriate.
