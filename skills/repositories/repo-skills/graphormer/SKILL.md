---
name: graphormer
description: "Routes Graphormer users to fairseq training, dataset
  customization, pretrained evaluation, model extension, and DiG workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Graphormer

Graphormer is a fairseq user-dir graph learning package for molecular modeling,
materials-style structure tasks, and a small set of research-only DiG
workflows. Use this skill when the task mentions Graphormer, Graphormer3D,
fairseq `--user-dir`, ZINC, PCQM4M, MolHIV, OC20, IS2RE, catalyst adsorption,
protein conformation sampling, protein-ligand diffusion, custom Graphormer
datasets, or Graphormer pretrained checkpoints.

This skill is a router, not a monolithic manual. Start with the most specific
sub-skill that matches the workflow, then read the nearest bundled reference or
helper script.

## Start here

- [Installation and environment](references/installation-and-environment.md)
- [Cross-cutting troubleshooting](references/troubleshooting.md)
- [Source script map](references/source-script-map.md)
- [Repository provenance](references/repo-provenance.md)
- [Environment check](scripts/check_graphormer_environment.py)

## Route map

- [fairseq-training](sub-skills/fairseq-training/SKILL.md): Graphormer property-prediction and Graphormer3D training command templates for ZINC, PCQM4M, MolHIV FLAG, and OC20/IS2RE.
- [datasets-and-customization](sub-skills/datasets-and-customization/SKILL.md): built-in dataset selection, custom dataset registration, preprocessing, and batch-schema validation.
- [pretrained-and-evaluation](sub-skills/pretrained-and-evaluation/SKILL.md): pretrained checkpoint selection, fine-tuning, and evaluation.
- [model-extension](sub-skills/model-extension/SKILL.md): Graphormer fairseq registries, model/task/criterion wiring, and extension recipes.
- [distributional-graphormer](sub-skills/distributional-graphormer/SKILL.md): optional DiG catalyst, property-guided, protein, and protein-ligand workflows.

## Minimal environment check

If you only want to confirm that a Graphormer-compatible environment is ready,
run the bundled checker from a shell that can see the target environment:

```bash
python scripts/check_graphormer_environment.py --user-dir <graphormer-package-dir> --format text
```

Add `--require-complete` when you want the script to confirm the expected
Graphormer model, task, criterion, and architecture registries. Add
`--require-cuda` on a CUDA host when you also want a tiny device smoke check.

## What this skill assumes

- Graphormer is loaded through fairseq's `--user-dir` mechanism.
- The user-dir points at the directory that contains Graphormer's `models/`,
  `tasks/`, and `criterions/` packages.
- Full native training, dataset download, checkpoint download, or DiG runs are
  optional and should be handled by a Researcher session only when the required
  data, hardware, and time budget are available.

## How to choose a sub-skill

- Need a training command: start with `fairseq-training`.
- Need to select a dataset or validate a custom data module: start with
  `datasets-and-customization`.
- Need to load a checkpoint or compare evaluation metrics: start with
  `pretrained-and-evaluation`.
- Need to add or inspect a registered model/task/criterion/architecture:
  start with `model-extension`.
- Need the DiG catalyst, protein, or protein-ligand research code: start with
  `distributional-graphormer`.

## When to read provenance

Read [Repository provenance](references/repo-provenance.md) before treating this
skill as current or before refreshing it against a newer Graphormer checkout.
