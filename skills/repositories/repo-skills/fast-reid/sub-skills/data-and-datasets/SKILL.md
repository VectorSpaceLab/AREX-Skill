---
name: data-and-datasets
description: "Operate FastReID dataset registries, built-in layouts, custom
  dataset classes, dataloaders, transforms, samplers, and safe data preflight
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# FastReID data and datasets

Use this sub-skill when a FastReID task involves dataset roots, `FASTREID_DATASETS`, built-in dataset names, custom dataset registration, `ImageDataset`/`CommDataset` tuple shape, train/test dataloader APIs, transforms, samplers, or preflight checks before training/evaluation.

## Start here

1. Identify the dataset name exactly as FastReID expects it, for example `Market1501`, `DukeMTMC`, `MSMT17`, `VeRi`, `VehicleID`, `SmallVehicleID`, `VeRiWild`, or `SmallVeRiWild`.
2. Resolve the dataset root that FastReID will receive: `FASTREID_DATASETS` if set, otherwise a relative `datasets` directory from the process working directory.
3. Validate the tree before launching any train/eval job:

```bash
python sub-skills/data-and-datasets/scripts/validate_dataset_layout.py --root <datasets-root> --dataset Market1501
```

4. If using a custom dataset, import the module that registers it before calling FastReID's train/test loader builders.

## Runtime references and scripts

- [`references/dataset-formats.md`](references/dataset-formats.md): use for built-in dataset names, expected directory/list-file layouts, file-name parsing rules, and the canonical `(img_path, pid, camid)` item schema.
- [`references/data-api.md`](references/data-api.md): use for `DATASET_REGISTRY`, `ImageDataset`, `CommDataset`, `build_reid_train_loader`, `build_reid_test_loader`, transform options, sampler choices, and custom dataset registration patterns.
- [`references/troubleshooting.md`](references/troubleshooting.md): use when FastReID cannot find datasets, parses pid/camid incorrectly, query/gallery is empty, samplers fail because of batch settings, or old dataset tests/imports conflict with this API.
- [`scripts/validate_dataset_layout.py`](scripts/validate_dataset_layout.py): safe no-download validator for selected built-in layout roots; run it before expensive train/eval commands or when diagnosing partial dataset trees.

## Route boundaries

- Training loops, schedulers, checkpoints, distributed launch, evaluator output, and train/eval command construction belong to [`../training-and-evaluation/`](../training-and-evaluation/).
- Model registry, backbone/head/meta-architecture construction, predictors, feature tensors, and checkpoint loading belong to [`../modeling-and-inference/`](../modeling-and-inference/).
- Source-only package setup, config inheritance, YAML merge behavior, and config recipe selection belong to [`../setup-and-configuration/`](../setup-and-configuration/).
- Project-specific datasets under FastReID extension projects belong to [`../deployment-and-projects/`](../deployment-and-projects/); use this sub-skill only for the shared registry/layout mechanics they rely on.

## Verified operating facts

- `FASTREID_DATASETS` defaults to `datasets` when the environment variable is unset.
- Dataset records are tuples `(img_path, pid, camid)`. Training built-ins usually prefix training `pid`/`camid` with a dataset name string before `CommDataset(..., relabel=True)` maps them to contiguous integers.
- Built-in registry keys include person ReID datasets (`Market1501`, `DukeMTMC`, `MSMT17`, `CUHK03`, `VIPeR`, `GRID`, `iLIDS`, etc.) and vehicle ReID datasets (`VeRi`, `VehicleID`, `SmallVehicleID`, `MediumVehicleID`, `LargeVehicleID`, `VeRiWild`, `SmallVeRiWild`, `MediumVeRiWild`, `LargeVeRiWild`).
- API signatures verified for this FastReID version include `build_reid_train_loader(train_set, *, sampler=None, total_batch_size, num_workers=0)` and `build_reid_test_loader(test_set, test_batch_size, num_query, num_workers=4)`; the config system also permits calls such as `build_reid_train_loader(cfg, combineall=...)` and `build_reid_test_loader(cfg, dataset_name=...)`.
