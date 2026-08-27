---
name: data-structures-and-io
description: "Design, validate, and troubleshoot MMEngine datasets, transforms,
  samplers, collate functions, data elements, and backend-agnostic file IO."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMEngine Data Structures and IO

Use this sub-skill when work mentions `BaseDataset`, `load_data_list`, `full_init`, `Compose`, data pipelines, `DefaultSampler`, `pseudo_collate`, `default_collate`, `BaseDataElement`, `InstanceData`, `PixelData`, `LabelData`, `mmengine.fileio`, `backend_args`, or legacy `FileClient` behavior.

## Read Order

1. `references/dataset-and-transform-workflows.md` — Build and validate dataset annotations, `BaseDataset` subclasses, transform pipelines, samplers, and collate choices.
2. `references/data-elements-and-fileio.md` — Use data element containers and backend-agnostic file IO helpers safely.
3. `references/troubleshooting.md` — Diagnose common dataset, transform, collate, data element, and file backend failures.
4. `scripts/data_contract_smoke.py` — Run a tiny local smoke check for a `BaseDataset` subclass, `InstanceData` constraints, and JSON/text/bytes file IO.

## Scope Boundaries

- Owns `mmengine.dataset`, `mmengine.structures`, `mmengine.fileio`, dataset metadata, lazy/full initialization, serialization, samplers/collation, and backend-agnostic path helpers.
- Route runner config placement for `train_dataloader`, `val_dataloader`, and `test_dataloader` to `../runner-and-training/SKILL.md`.
- Route `BaseModel`, data preprocessor, evaluator, metric, and inference expectations for samples to `../models-metrics-and-inference/SKILL.md`.
- Route registry and config syntax fundamentals for registering datasets/transforms/functions to `../configuration-and-registry/SKILL.md`.

## Fast Workflow

1. Define the sample contract first: raw annotation fields, `metainfo`, transformed data dict keys, data sample objects, and collated batch shape/type.
2. Validate the dataset independently with `len(dataset)`, `dataset.metainfo`, `dataset.get_data_info(0)`, and `dataset[0]` before wiring it into a runner.
3. Choose `pseudo_collate` when downstream code expects lists of per-sample tensors/data elements; choose `default_collate` only when stackable tensor/number/array shapes are consistent.
4. Use `backend_args` and unified `mmengine.fileio` helpers for IO; treat `FileClient` and `file_client_args` as legacy compatibility only.
5. Use the bundled smoke script as a package/API sanity check before debugging larger project-specific data code.
