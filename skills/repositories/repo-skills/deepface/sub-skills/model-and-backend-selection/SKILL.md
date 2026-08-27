---
name: model-and-backend-selection
description: "Select and troubleshoot DeepFace models, detector backends,
  optional dependencies, model weights, TensorFlow/Keras compatibility,
  normalization, and encryption."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Model And Backend Selection

Use this sub-skill when the user task needs Supported recognition, demography, spoofing, and detector names; DeepFace.build_model; base versus optional dependencies; TensorFlow/Keras/tf-keras; weight cache; CPU/GPU; normalization and encrypted embeddings.

## Route Here

- Answer package-user questions for the owned DeepFace functions and parameters.
- Select safe minimal code patterns before running heavy model builds, weight downloads, database connections, Docker, or webcam/video operations.
- Diagnose workflow-specific errors using the linked troubleshooting reference.
- Cross-link to sibling sub-skills when a workflow spans detection, recognition, persistence, serving, and optional model/dependency setup.

## Reroute

Detailed task workflows route to sibling sub-skills; database clients and services go to `../datastore-search/SKILL.md`; REST startup goes to `../api-service/SKILL.md`.

## First Checks

1. Confirm `from deepface import DeepFace` works; otherwise use `../../references/troubleshooting.md`.
2. Identify whether the user wants static guidance, code generation, environment diagnosis, or runtime execution.
3. Keep network/model-weight/database/camera side effects explicit and ask before running them in constrained environments.
4. Use the nearest bundled helper for safe validation before recommending a heavier run.

## Reference Map

- `references/api-reference.md` documents signatures, parameters, outputs, and API-specific behavior for this sub-skill.
- `references/workflows.md` or the focused workflow reference contains practical recipes and decision patterns.
- `references/troubleshooting.md` maps common errors to concrete recovery steps.
- `scripts/inspect_deepface_models.py` is the safe bundled helper for this sub-skill.

## Safety

Do not tell future agents to open or run original repository tests, examples, notebooks, scripts, or local checkout files. Use this self-contained sub-skill, its references, and its bundled helper scripts instead.
