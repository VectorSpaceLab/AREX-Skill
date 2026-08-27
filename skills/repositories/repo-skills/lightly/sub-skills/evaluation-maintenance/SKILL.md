---
name: evaluation-maintenance
description: "Use LightlySSL evaluation utilities and choose safe repository
  maintenance checks for tests, docs, notebooks, and CI variants."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# evaluation-maintenance

Use this sub-skill when a task asks how to evaluate LightlySSL representations, wire benchmarking callbacks/classifiers, or maintain the LightlySSL repository with scoped tests, static checks, docs builds, generated notebooks, and dependency-variant awareness.

For a fresh public package environment, start with `pip install lightly`. Add `lightly[timm]` only for TIMM / MAE / ViT-style optional modules, and `lightly[video]` only for video/PyAV data workflows. Repository-development checks need the project's development dependencies; use the maintenance reference before selecting broad commands.

## Route here for

- KNN feature-bank evaluation, linear evaluation, finetuning evaluation, online classifiers, `BenchmarkModule`, and `MetricCallback`.
- Choosing between `make format`, `make format-check`, `make lint`, `make type-check`, `make static-checks`, `make test-fast`, `make test`, `make test-distributed`, and `make all-checks`.
- Planning targeted pytest commands for changed Lightly source, tests, examples, docs, benchmarking utilities, or dependency metadata.
- Slow-test and DDP marker behavior, including when `--runslow`, `USE_PYTEST_POOL=1`, and `python -m pytest` are required.
- Generated notebook freshness after `examples/` changes, docs build checks after `docs/source` changes, CI dependency variants, and contributor/PR constraints.
- Benchmark caveats for dataset-scale or accelerator-dependent workflows.

## Route elsewhere

- End-to-end SSL training recipes, custom training loops, trainer configuration, and distributed training recipes: use `training-workflows`.
- `lightly-ssl-train`, `lightly-embed`, `lightly-magic`, `lightly-crop`, input data layout, and embedding CSV operations: use `cli-data-embedding`.
- Low-level transforms, losses, model heads/modules, datasets, collates, memory banks, tensor shapes, TIMM modules, or video dataset APIs: use `ssl-building-blocks`.
- PyPI release, package publishing, notifications, or credentialed maintainer operations: treat as out of scope unless a human maintainer explicitly owns the release process.

## First actions

1. Identify whether the user is evaluating model outputs or maintaining the repository.
2. Read the nearest bundled reference:
   - [Evaluation and benchmarks](references/evaluation-and-benchmarks.md)
   - [Maintenance workflows](references/maintenance-workflows.md)
   - [Troubleshooting](references/troubleshooting.md)
3. For repository-maintenance planning, use the bundled dry-run helper. It prints commands and never executes them:
   - `python scripts/check_repo_dev_commands.py --help`
   - `python scripts/check_repo_dev_commands.py lightly/utils/benchmarking/knn.py tests/utils/benchmarking/test_knn.py`
4. Keep checks scoped first. Escalate to `make all-checks` only when the user needs pre-PR confidence or the change crosses many surfaces.

## Common safe patterns

- Representation evaluation: use `knn_predict` for tensor-level KNN, `KNNClassifier` for Lightning validation over train/validation dataloaders, `LinearClassifier` to freeze a backbone, `FinetuneClassifier` to update backbone plus head, and `OnlineLinearClassifier` inside a parent LightningModule.
- Metrics capture: attach `MetricCallback` to a Lightning `Trainer` when the task needs per-epoch scalar logs collected from `trainer.callback_metrics`.
- Source change: run formatting/static checks plus the most relevant targeted pytest subtree before broader suites.
- Example change: regenerate notebooks with `make generate-example-notebooks` and include the tracked notebook diff in the change.
- Docs change: build docs locally with the lightweight no-plot target before PR handoff.
- Distributed tests: only run DDP-marked tests when the environment supports multiprocessing; use `USE_PYTEST_POOL=1 python -m pytest tests --runslow -m DDP`.
