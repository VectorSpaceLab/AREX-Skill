---
name: modeling-and-layers
description: "Understand Scenic model registry contracts, BaseModel task bases,
  Flax module construction, layers, attention, matchers, and tiny smoke checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Modeling and Layers

Use this sub-skill when the task is about Scenic model selection, BaseModel contracts, task-specific model bases, Flax module construction, layer/attention/matcher APIs, or tiny smoke checks.

## Start here

- Read [`references/modeling-api.md`](references/modeling-api.md) for the registry, model-class contracts, loss/metric conventions, and model-init/apply patterns.
- Read [`references/layers-and-matchers.md`](references/layers-and-matchers.md) for attention/layer/matcher APIs, optional dependencies, and tiny validation patterns.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) when a model name is missing, a Flax/JAX shape or RNG issue appears, metrics aggregate incorrectly, or a checkpoint does not load cleanly.
- Run [`scripts/model_registry_probe.py`](scripts/model_registry_probe.py) to list registered model names or resolve a single model class without instantiating it.

## Scope and routing

- In scope: model registry lookups, BaseModel and task-base contracts, loss/metric normalization, Flax module construction, layer/attention/matcher APIs, and smoke-test patterns for tiny inputs.
- Out of scope: training orchestration, launch commands, schedules, checkpoint lifecycle, dataset builders, project selection, and paper/baseline choice.
- Route training/runtime execution to `running-and-training`.
- Route dataset builders and input-pipeline work to `data-pipelines`.
- Route project-level or paper-level model selection to `baselines-and-projects`.

## Operating rules

1. Begin with the registry; an unrecognized model name is usually a registry or config problem, not a training problem.
2. Treat `build_flax_model()` as the construction boundary. Build the Flax module, then use tiny `init`/`apply` checks instead of a full run.
3. Keep loss functions local and scalar; keep metrics cross-device safe by returning sum/normalizer pairs.
4. Use tiny dummy inputs for smoke checks and shape assertions. Prefer `init_with_output`, `init`, and `apply` on minimal batches.
5. Keep optional matcher dependencies explicit. Do not promise `scipy` or `ott-jax` behavior unless the target matcher requires it.

## When to read what

| Need | Read |
| --- | --- |
| Registry, BaseModel, task bases, loss/metric rules, smoke-init pattern | [`references/modeling-api.md`](references/modeling-api.md) |
| Attention, layer, masked-layer, and matcher APIs plus tiny validation patterns | [`references/layers-and-matchers.md`](references/layers-and-matchers.md) |
| Common failure modes and recovery | [`references/troubleshooting.md`](references/troubleshooting.md) |
| List registered models or resolve one class | [`scripts/model_registry_probe.py`](scripts/model_registry_probe.py) |
