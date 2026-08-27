---
name: core-api
description: "Use TorchMetrics core APIs for import checks, metric lifecycle,
  custom Metric state, device/DDP behavior, persistence, and Lightning logging."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# TorchMetrics Core API

Use this sub-skill when a task is about the TorchMetrics base API rather than a specific metric family: choosing functional versus module metrics, accumulating batches, writing a custom `Metric`, moving metrics across devices, synchronizing distributed state, saving metric state, or logging metrics from PyTorch Lightning.

## Route map

- Read [references/core-api.md](references/core-api.md) when you need import sanity checks, functional-vs-module selection, `update`/`compute`/`forward`/`reset` semantics, `MetricCollection`, device/dtype rules, or state persistence.
- Read [references/custom-metrics-lightning-ddp.md](references/custom-metrics-lightning-ddp.md) when implementing `Metric` subclasses with `add_state`, list states, `dist_reduce_fx`, cache behavior, DDP controls, or Lightning `self.log`/`self.log_dict` patterns.
- Read [references/troubleshooting.md](references/troubleshooting.md) when you see install/import errors, unexpected keyword arguments, stale computed values, device mismatches, unregistered metrics, Lightning logging failures, or DDP synchronization surprises.
- Run [scripts/core_metric_smoke.py](scripts/core_metric_smoke.py) to verify that the installed package can instantiate and execute `Accuracy`, `MeanSquaredError`, `MetricCollection`, and a small custom list-state metric without downloads.

## Quick usage policy

1. Use functional metrics for one-shot tensor-in/tensor-out calculations that do not need accumulation, object registration, state persistence, or built-in distributed synchronization.
2. Use module metrics for training/evaluation loops, multi-batch accumulation, Lightning logging, `MetricCollection`, device moves, or DDP-aware synchronization.
3. Register module metrics as `nn.Module` children: direct attributes, `nn.ModuleList`, `nn.ModuleDict`, or `MetricCollection`; do not hide metrics inside plain Python containers.
4. Keep separate metric instances for train/validation/test and for each dataloader whose state must not mix.
5. Route detailed domain metric catalogs to sibling domain sub-skills; route wrappers and plotting to `collections-wrappers-plotting`; route metrics that may download models to `model-based-metrics`.
