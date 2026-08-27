---
name: configuration-model-zoo
description: "Select, inspect, and adapt MMDetection3D configs and model-zoo entries."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Configuration and Model Zoo

Use this sub-skill when the task is to choose, inspect, compare, or lightly adapt an MMDetection3D v1.x config or model-zoo entry before running another workflow.

## Load this when

- A user names a model family, config filename, checkpoint alias, metric table row, dataset, or modality and asks which MMDetection3D config to use.
- A user needs to inspect a config's inherited model, dataset, dataloader, evaluator, runtime, or schedule fields.
- A user wants a safe child config or `--cfg-options` override for dataset roots, classes, batch size, work directory, test-time options, AMP, or other config-only changes.
- A user needs to understand config inheritance, `_delete_=True`, naming conventions, model-index entries, or model-zoo checkpoint/config matching.

## Route elsewhere

- Raw dataset download, conversion, info-file generation, or layout validation: use the `data-preparation` sub-skill.
- Launching train/test/evaluation/distributed jobs after the config is chosen: use the `training-evaluation` sub-skill.
- Inference API calls, demo-style prediction, or visualization outputs from a selected config/checkpoint: use the `inference` sub-skill.
- Custom Python modules, registry implementations, optional project packages, or new components: use the `customization-extensions` sub-skill.
- Box/coordinate-system or visualizer API reasoning: use the `structures-visualization` sub-skill.

## Operating workflow

1. Identify the task axis: modality, dataset, model family, metric target, available hardware/backend, and whether the request is selection, inspection, or adaptation.
2. If a config path is available, inspect it with [`scripts/check_config.py`](scripts/check_config.py) before recommending overrides.
3. Use [`references/model-overview.md`](references/model-overview.md) to map model aliases, checkpoint names, and dataset/task families to likely config folders.
4. Use [`references/configuration.md`](references/configuration.md) to reason about `_base_`, top-level keys, child-config edits, `--cfg-options`, and class/dataset changes.
5. Use [`references/troubleshooting.md`](references/troubleshooting.md) when parsing fails, overrides do not apply, legacy fields appear, model/checkpoint pairs mismatch, or optional sparse/project backends are involved.
6. Hand off the selected config, checkpoint expectation, and concrete overrides to `training-evaluation` or `inference` when execution is requested.

## Default deliverables

For config/model-zoo tasks, produce one or more of:

- A short recommendation naming the config family, expected dataset/task, checkpoint compatibility, and any backend caveats.
- A compact child-config patch or override list, not a full copied config unless the user asks for a standalone file.
- A `check_config.py` summary with suspicious fields highlighted.
- A routing handoff to the next sub-skill for data preparation, training/evaluation, inference, or customization.
