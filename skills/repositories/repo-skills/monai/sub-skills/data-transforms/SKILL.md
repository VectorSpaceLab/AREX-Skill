---
name: data-transforms
description: "Build MONAI preprocessing, IO, metadata, caching, dataset,
  dataloader, decollation, inverse-transform, and lazy-transform workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MONAI Data and Transform Workflows

Use this sub-skill when an agent needs to load medical images or arrays, assemble dictionary transform pipelines, preserve `MetaTensor` metadata, choose MONAI dataset/cache classes, debug collation, or validate inverse/lazy transform behavior.

## Route Here

- Build `monai.transforms.Compose` pipelines for image/label dictionaries, arrays, random crops, intensity transforms, spatial transforms, or post-load channel handling.
- Load file-backed data with `LoadImaged`, create datalists with `load_decathlon_datalist`, and wrap items in `Dataset`, `CacheDataset`, `PersistentDataset`, `SmartCacheDataset`, or `DataLoader`.
- Preserve, inspect, or troubleshoot `MetaTensor` metadata, affine, `applied_operations`, batching, `decollate_batch`, lazy resampling, and inverse transforms.
- Diagnose transform errors: missing keys, channel-first mistakes, optional reader dependencies, cache staleness, multiprocessing/collate issues, and inverse failures.

## Route Elsewhere

- Route model architecture, losses, metrics, sliding-window inference, and prediction postprocessing to `modeling-inference`.
- Route training/evaluation loops, MONAI engines, handlers, checkpointing, AMP, and trainer input batches to `training-evaluation`.
- Route Bundle config syntax, `ConfigParser`, and `python -m monai.bundle` usage to `bundle-config`.
- Route Auto3DSeg, DataAnalyzer, generated bundle orchestration, and app-level dataset analysis to `apps-auto3dseg`.

## Required References and Script

- Read `references/workflows.md` when designing end-to-end data loading, transform, caching, metadata, lazy, inverse, or validation workflows.
- Read `references/api-reference.md` when checking signatures, key arguments, data contracts, shape conventions, and dataset/cache selection notes.
- Read `references/troubleshooting.md` when a pipeline fails from optional readers, missing keys, channel layout, metadata, lazy resampling, cache, collation, or inverse-transform issues.
- Run `scripts/check_data_pipeline.py --help` to inspect the bundled safe validation script, and run the script to verify that installed MONAI can build a tiny dictionary transform `Dataset` returning `MetaTensor` outputs.

## Fast Operating Pattern

1. Start with dictionary items using stable keys such as `"image"` and `"label"`; add optional keys only if transforms set `allow_missing_keys=True` or the data always contains them.
2. Compose deterministic loading and normalization before random augmentation; cache only deterministic work before the first `Randomizable` transform.
3. Prefer `monai.data.DataLoader` over PyTorch's raw dataloader for MONAI random state handling, patch-list collation, and metadata-aware batches.
4. Validate one sample, then one batch, then any inverse/lazy path before embedding the pipeline in a trainer, bundle, or Auto3DSeg workflow.
