---
name: pytorch-metric-learning
description: "Routes PyTorch Metric Learning tasks across metric-learning
  components, training workflows, embedding evaluation, dataset loading, and
  sampling."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# PyTorch Metric Learning

Use this skill for the `pytorch-metric-learning` package when the task is about metric-learning losses, miners, trainers, testers, inference, datasets, or samplers.

## Install

For most workflows, install the package with the CPU-friendly hooks extra so the evaluation utilities and logging helpers are available:

```bash
pip install pytorch-metric-learning[with-hooks-cpu]
```

If you are working from a local checkout, editable install works well too:

```bash
pip install -e .[with-hooks-cpu]
```

Install a compatible `torch` / `torchvision` pair first if your environment does not already have them. The repository's docs and tests assume those packages are available for the trainer, tester, and example workflows.

Use the GPU hooks extra only when you explicitly need the faiss GPU path. Read `references/repo-provenance.md` when you need to compare this skill with the source checkout or decide whether it should be refreshed.

## Quick smoke check

Run the bundled import check when you want to confirm that the package and its main public submodules are available from the current environment:

```bash
python scripts/check_import.py
```

## Route map

### `components`
Use for choosing, combining, or customizing losses, miners, distances, reducers, regularizers, `CrossBatchMemory`, `SelfSupervisedLoss`, or custom component classes.

### `training`
Use for `MetricLossOnly`, `TrainWithClassifier`, `CascadedEmbeddings`, `DeepAdversarialMetricLearning`, `TwoStreamMetricLoss`, hook wiring, checkpointing, and logging.

### `evaluation`
Use for `AccuracyCalculator`, the tester classes, nearest-neighbor inference, and faiss-backed search or clustering.

### `data`
Use for packaged datasets, dataset extension, class-balanced sampling, hierarchical sampling, and fixed-triplet or offline-mining samplers.

## How to route

- Start with the most specific sub-skill when the user already knows the workflow family.
- If the user only names a loss, miner, or tuple-shape error, start with `components`.
- If the user only names a trainer, hook, or logging problem, start with `training`.
- If the user only names precision@1, mAP, a tester, or an index/search question, start with `evaluation`.
- If the user only names a dataset, split, or sampler, start with `data`.

## When to read more

- `references/troubleshooting.md` for install/import and package-wide failure patterns.
- `references/repo-provenance.md` when you need to decide whether this skill matches the current repository state.
- The relevant sub-skill `SKILL.md` and its bundled `references/` / `scripts/` for workflow details.

## Public package surface

The package exports separate modules for losses, miners, reducers, regularizers, samplers, trainers, testers, datasets, and utilities. The most common entry points are:

- `pytorch_metric_learning.losses`
- `pytorch_metric_learning.miners`
- `pytorch_metric_learning.reducers`
- `pytorch_metric_learning.regularizers`
- `pytorch_metric_learning.samplers`
- `pytorch_metric_learning.trainers`
- `pytorch_metric_learning.testers`
- `pytorch_metric_learning.datasets`
- `pytorch_metric_learning.utils.accuracy_calculator`
- `pytorch_metric_learning.utils.inference`

Use the appropriate sub-skill reference for the deeper API map instead of trying to memorize every class here.
