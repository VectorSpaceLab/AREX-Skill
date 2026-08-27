---
name: fairseq-training
description: "Graphormer fairseq-train templates for graph prediction and
  Graphormer3D IS2RE."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# fairseq-training

Use this sub-skill to build or sanity-check Graphormer `fairseq-train` commands for:
- ZINC
- PCQM4M v1
- PCQM4Mv2
- MolHIV FLAG training portions
- OC20 / IS2RE with Graphormer3D

## Start here
- [Training workflows](references/training-workflows.md)
- [CLI parameters](references/cli-parameters.md)
- [Troubleshooting](references/troubleshooting.md)
- [Command builder](scripts/build_graphormer_train_command.py)

## Command shape
- Graphormer training commands use `fairseq-train --user-dir <graphormer-user-dir> ...`.
- Property prediction workflows use `graph_prediction` or `graph_prediction_with_flag`.
- OC20 / IS2RE uses `is2re` with `graphormer3d_base`.
- Keep the task, criterion, dataset, and architecture aligned with the chosen workflow.

## Route elsewhere
- Custom dataset module contracts: `datasets-and-customization`.
- Pretrained checkpoint loading and evaluation: `pretrained-and-evaluation`.
- Model, task, and criterion internals: `model-extension`.
- Distributional Graphormer / DiG: `distributional-graphormer`.

## Helper
- `python scripts/build_graphormer_train_command.py --help`
- The helper only prints a shell command; it never launches training.
