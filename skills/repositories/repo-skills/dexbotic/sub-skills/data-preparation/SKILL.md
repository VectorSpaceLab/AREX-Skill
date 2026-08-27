---
name: data-preparation
description: "Prepare, validate, register, and troubleshoot Dexbotic DexData
  datasets and safe dataset conversions."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Dexbotic data preparation

Use this route when the task is about converting demonstrations, designing a DexData JSONL schema, registering a dataset, computing action/state normalization metadata, or diagnosing data-loader failures. Keep model/trainer selection in [training](../training/SKILL.md), HTTP policy serving in [inference-serving](../inference-serving/SKILL.md), and physical robot topology in [evaluation-deployment](../evaluation-deployment/SKILL.md).

## Operating sequence

1. Decide the action/state convention before conversion: dimensionality, delta versus absolute dimensions, periodic dimensions, gripper convention, and camera order.
2. Produce one JSON object per frame in an episode JSONL file. Keep image/video references and frame indices aligned with the same frame.
3. Validate paths, finite numeric values, frame indices, prompt presence, and consistent state/action dimensions with `scripts/validate_dexdata.py` before registering the dataset.
4. Register a dataset dictionary with `register_dataset(...)`, including `annotations`, optional `data_path_prefix`, positive `frequency`, and action metadata. Import the registration module before constructing `DexDataset`.
5. Generate or load `norm_stats.json` alongside the checkpoint/data contract; never silently reuse statistics from another action space.
6. Run a small loader inspection before expensive training. A missing image, malformed JSONL line, or bad action horizon is a data issue, not a model issue.

Read [DexData and registration](references/dexdata-and-registration.md), [conversion boundaries](references/conversion-boundaries.md), and [troubleshooting](references/troubleshooting.md) for details. The bundled validator is intentionally local, deterministic, and read-only unless an explicit report path is supplied.
