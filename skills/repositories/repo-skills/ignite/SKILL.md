---
name: ignite
description: "Routes PyTorch Ignite training, handlers, metrics, distributed,
  and legacy contrib workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# PyTorch Ignite

PyTorch Ignite is a high-level library for training and evaluating neural networks in PyTorch. This runtime skill routes common user requests to focused sub-skills and keeps the package self-contained.

## Install and confirm the package

- Install the package in the active environment with `python -m pip install pytorch-ignite`.
- If you are working from the source checkout, `python -m pip install -e .` is the most direct editable install.
- Minimal import check: `python -I -c "import ignite; print(ignite.__version__)"`.
- For a quick end-to-end smoke check, run `scripts/core_smoke.py`.
- For focused handler, metric, or distributed checks, run `sub-skills/handlers/scripts/smoke_handlers.py`, `sub-skills/metrics/scripts/metric_smoke.py`, or `sub-skills/distributed/scripts/distributed_smoke.py`.

Read `references/repo-provenance.md` when you need to confirm that this skill matches the checked-out repository, and read it again before refreshing the skill after repo changes.
Read `references/repo-routing-metadata.json` when you need the structured router placement, read-when signals, and selection guidance that keep this repo skill aligned with managed scenario routing.

Read `references/optional-dependencies.md` before enabling advanced metrics, distributed backends, logger integrations, or example workflows that need extra packages.

Read `references/troubleshooting.md` for import failures, missing optional packages, backend selection issues, and common runtime errors.

## Route map

- `sub-skills/engine/` — Engine, Events, supervised trainer/evaluator helpers, deterministic runs, resume logic, custom events, gradient accumulation, and AMP/TPU/MPS variants.
- `sub-skills/handlers/` — Checkpointing, early stopping, EMA, progress bars, loggers, parameter schedulers, LR finder, time profiling, and termination helpers.
- `sub-skills/metrics/` — Metric attachment, direct update/compute/reset, metric arithmetic, and the curated classification/regression/NLP/vision/GAN metric families.
- `sub-skills/distributed/` — `Parallel`, `auto_dataloader`, `auto_model`, `auto_optim`, distributed backends, rank helpers, and launcher/debugging workflows.
- `references/legacy-contrib.md` — Older `ignite.contrib.*` imports, TBPTT helpers, and deprecation guidance for legacy code.
- `references/utils-reference.md` — Cross-cutting tensor, logging, seed, deprecation, and checkpoint helpers shared across routes.

## How to choose a route

Use the engine route when the request is about constructing or debugging the training loop itself. Use handlers when the request is mostly about checkpointing, logging, schedules, progress, or early stopping around that loop. Use metrics when the task is about computing or validating model outputs. Use distributed when the task names `Parallel`, `idist`, `torchrun`, `horovodrun`, `gloo`, `nccl`, `mpi`, or `xla-tpu`.

If the user mentions old `ignite.contrib` imports, start with `references/legacy-contrib.md` and then jump to the modern sub-skill that owns the replacement API.

## Shared notes

- The package version in this repository is `0.6.0`.
- Advanced logger integrations such as ClearML, MLflow, Neptune, Polyaxon, W&B, TensorBoard, and Visdom are handled inside `sub-skills/handlers/`.
- GPU/TPU/Horovod-specific behavior is optional and may be absent in a CPU-only environment.
