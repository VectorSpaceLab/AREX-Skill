---
name: datasets-and-customization
description: "Route Graphormer dataset source selection, custom registration,
  preprocessing, and validation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Datasets and Customization

Use this sub-skill when you need to:
- choose a built-in DGL, PyG, or OGB dataset
- parse `--dataset-name` and `--dataset-source`
- register a custom dataset with `register_dataset`
- reason about Graphormer preprocessing and batch fields
- validate a user dataset module before training

## Route elsewhere
- Training schedules, optimizer choices, and long-run command building: fairseq-training
- Pretrained checkpoints, evaluation, and fine-tuning: pretrained-and-evaluation
- Model, task, criterion, or architecture internals: model-extension

## Bundled runtime files
- [Dataset sources and formats](references/datasets-and-formats.md)
- [API reference](references/api-reference.md)
- [Troubleshooting](references/troubleshooting.md)
- [Custom dataset validator](scripts/validate_custom_dataset_contract.py)

## Quick rules
- Built-in datasets use `--dataset-source` plus `--dataset-name`.
- Custom datasets use `--user-data-dir` and `--dataset-name`; do not combine them with `--dataset-source`.
- Custom registrations must return `dataset`, `train_idx`, `valid_idx`, `test_idx`, and `source`.
- Allowed custom `source` values are `dgl` and `pyg`.
- Graphormer preprocessing produces `idx`, `attn_bias`, `attn_edge_type`, `spatial_pos`, `in_degree`, `out_degree`, `x`, `edge_input`, and `y`.
- Batch collation drops graphs above `max_nodes`, masks long spatial distances, and truncates multi-hop edge history.

## Validation path
1. Read the dataset source table and syntax guide.
2. Register or locate the dataset module.
3. Run the bundled validator in list-only mode or full validation mode.
4. If validation fails, use the troubleshooting notes before moving to training or evaluation.
5. Run the bundled validator in list-only mode first; rerun with `--execute-registrations` only when dataset construction is safe.
