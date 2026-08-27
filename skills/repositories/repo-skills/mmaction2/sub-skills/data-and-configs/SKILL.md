---
name: data-and-configs
description: "Prepare and validate MMAction2 data annotations, pipelines, config
  inheritance, overrides, and safe data/config utilities."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMAction2 data and configs router

Use this sub-skill when the user needs to prepare, inspect, or debug MMAction2 dataset annotations, dataloader sections, transform pipelines, config inheritance, or `--cfg-options` overrides before training, testing, or inference.

## Owned operating references

- [Data and config reference](references/data-config-reference.md): dataset schemas, `data_prefix` keys, pipeline patterns, config families, `_base_` inheritance, naming, and override examples.
- [Tooling reference](references/tooling-reference.md): safe config inspection, safe data-utility decisions, and bounded validation templates.
- [Troubleshooting](references/troubleshooting.md): annotation, prefix, decode, AVA, localization, audio, video-text, pipeline, and config override errors.
- [Config inspector script](scripts/mmaction2_config_inspector.py): parses a user-supplied config and prints a safe summary without building datasets, scanning media, training, testing, or writing outputs.

## Fast routing

Handle here:

- Choosing between `VideoDataset`, `RawframeDataset`, `PoseDataset`, `AudioDataset`, `AVADataset`, `ActivityNetDataset`, and `VideoTextDataset`.
- Writing or validating rawframe/video/skeleton/audio/AVA/localization/video-text annotation files.
- Editing `train_dataloader`, `val_dataloader`, `test_dataloader`, `train_pipeline`, `val_pipeline`, and `test_pipeline` sections.
- Explaining config families, file-name parts, `_base_` inheritance, and `--cfg-options` quoting.
- Safely inspecting a config with `python scripts/mmaction2_config_inspector.py --config CONFIG.py --show-dataloaders --show-pipelines`.

Route elsewhere:

- Actual training, testing, metrics execution, distributed launch, resume, AMP, work directories, checkpoints: `../training-and-evaluation/SKILL.md`.
- Inference APIs, inferencer/demo runtime, checkpoint/config pairing for prediction: `../inference-and-demos/SKILL.md`.
- Custom model classes, registry/export/deployment, or new registered transforms/datasets beyond config usage: `../models-and-extension/SKILL.md`.

## Required safety checks

1. Treat all config files as Python programs. Inspect only trusted user-provided config files, and never run training or dataset builders from this sub-skill.
2. Prefer the bundled config inspector for summaries; it resolves config text and overrides but does not instantiate datasets/models.
3. Before any dataset-scale utility, require explicit user confirmation for input root, output root, write behavior, worker count, expected size, and whether network access is allowed.
4. Never enable destructive delete options while diagnosing data quality unless the user explicitly asks after seeing a dry-run report.
5. Keep evidence self-contained: answer from these references and user-provided files instead of sending future agents to source docs, examples, tests, or config files.
