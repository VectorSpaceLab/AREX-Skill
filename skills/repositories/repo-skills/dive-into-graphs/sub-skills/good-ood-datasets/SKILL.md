---
name: good-ood-datasets
description: "Use DIG's GOOD OOD dataset loaders for domain/shift splits,
  metadata, and graph OOD benchmark access across molecule, node, and synthetic
  graph domains."
disable-model-invocation: true
metadata:
  disco-role: operating
license: GPL 3.0
---

# GOOD OOD Datasets

Use this sub-skill for DIG's GOOD dataset loaders and the metadata they return.

## Include

- `dig.oodgraph`: `GOODHIV`, `GOODPCBA`, `GOODZINC`, `GOODCMNIST`, `GOODMotif`, `GOODCora`, `GOODArxiv`, `GOODCBAS`.
- `GOOD*.load(root, domain, shift='no_shift', generate=False)` dataset constructors and returned `meta_info` dictionaries.
- Domain/shift/subset selection, download handling, and benchmark metadata for graph OOD workflows.

## Exclude

- Molecular generation, SSL, explainability, augmentation, fairness, or large-scale graph workflows.

## Start Here

- Read `references/data-formats.md` for the domain/shift/subset layout.
- Read `references/workflows.md` for the supported load patterns.
- Read `references/troubleshooting.md` when a download or split name is wrong.
- Run `scripts/good_metadata_check.py` for a safe import-and-metadata smoke check.

## Core Workflows

- **Graph OOD loading**: choose a dataset class, call `.load(...)`, and use the returned train/id-val/id-test/val/test mapping plus `meta_info`.
- **Domain and shift selection**: match the dataset-specific allowed domains (`scaffold`, `size`, `color`, `basis`, `word`, `degree`, `time`) and shifts (`no_shift`, `covariate`, `concept`).
- **Benchmark setup**: use `meta_info.dim_node`, `meta_info.dim_edge`, `meta_info.num_envs`, and `meta_info.num_classes` to configure downstream models.
