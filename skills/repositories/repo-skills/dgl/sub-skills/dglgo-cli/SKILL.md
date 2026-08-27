---
name: dglgo-cli
description: "Use DGL-Go CLI workflows for generating configs, running recipes,
  training from YAML, exporting scripts, and applying checkpoints."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DGL-Go CLI

Use this sub-skill when the task asks to run DGL-Go, generate or repair a DGL-Go YAML file, list or copy recipes, train from a YAML config, export a runnable script, or apply a saved DGL-Go checkpoint to inference data.

## Fast Routing

- For command syntax, flags, and copy-paste examples, read [CLI reference](references/cli-reference.md).
- For YAML keys, pipeline modes, recipes, custom CSV data, and checkpoint fields, read [configuration](references/configuration.md).
- For end-to-end configure/train/export/apply flows, read [workflows](references/workflows.md).
- For install, dependency, dataset, checkpoint, and schema failures, read [troubleshooting](references/troubleshooting.md).
- To lint a config without importing DGL-Go or starting training, run `python scripts/dglgo_config_linter.py path/to/cfg.yaml`.

## Boundaries

- Route low-level graph construction, heterographs, batching, and graph serialization to `graph-apis`.
- Route custom CSV graph layout details and DGL dataset implementation details to `datasets-and-io`.
- Route GNN module internals, exported script edits, and model customization to `message-passing-training`.
- Route multi-machine or distributed launch tasks to `distributed-tools`.

## Safety Notes

DGL-Go training and apply commands may download datasets, load checkpoints, import optional packages such as OGB or RDKit, and execute generated Python. Prefer `dgl export --cfg ... --output ...` for reviewable code before long or unfamiliar runs, and use the bundled linter for safe preflight checks.
