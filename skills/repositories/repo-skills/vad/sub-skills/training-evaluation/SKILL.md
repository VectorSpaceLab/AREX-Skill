---
name: training-evaluation
description: "Guides VAD training, checkpoint loading, safe configuration
  overrides, single-GPU evaluation, result formatting, and diagnosis of
  legacy-stack runtime failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# VAD training and evaluation

Use this route for launch commands, work directories, resume/override behavior, checkpoint evaluation, metrics, or result formatting.

## Route

1. Prepare and validate data with [data-preparation](../data-preparation/SKILL.md).
2. Select and parse a VAD config with [architecture-configuration](../architecture-configuration/SKILL.md) and its safe checker.
3. Read [workflow-reference.md](references/workflow-reference.md) and [cli-reference.md](references/cli-reference.md).
4. Run `python scripts/check_training_contract.py CONFIG` before an expensive command.
5. Train with the selected single/distributed launch recipe; evaluate with **one non-distributed GPU** unless you have independently verified a compatible alternative. The repository warns that distributed evaluation can produce inaccurate results.

Full training/evaluation was not run during construction: it needs external nuScenes data, checkpoints, and CUDA/native operators.

## Scope boundaries

- Raw data and temporal PKLs: [data-preparation](../data-preparation/SKILL.md).
- Model graph and config semantics: [architecture-configuration](../architecture-configuration/SKILL.md).
- Rendering result artifacts: [visualization](../visualization/SKILL.md).

Use [troubleshooting.md](references/troubleshooting.md) for import, launcher, normalization, and output failures.
