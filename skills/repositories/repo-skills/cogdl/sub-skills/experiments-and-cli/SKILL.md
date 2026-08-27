---
name: experiments-and-cli
description: "Routes CogDL experiment() and training-CLI workflows for
  comparing, tuning, and launching runs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Experiments and CLI

Use this sub-skill when a user wants to run CogDL's high-level `experiment()` API, preflight the training CLI surface, compare multiple datasets/models/seeds, or add checkpoint, logging, embedding, and AutoML flags.

Typical triggers:
- "Run GCN and GAT on Cora"
- "Compare two datasets with the same model"
- "What does `--use-best-config` do?"
- "How do I pass a custom Optuna search space?"
- "Can I test the CLI flags without starting training?"

Read `references/api-and-cli.md` for verified signatures, CLI flags, result semantics, and AutoML behavior.
Read `references/workflows.md` for the no-network Cora/GAT plan, checkpoint/log/embedding recipes, and the Optuna search pattern.
Read `references/troubleshooting.md` when parser errors, wrapper mismatches, dataset downloads, checkpoint/log writes, device flags, or Optuna compatibility problems appear.

Run `scripts/cogdl_cli_smoke.py` to import the parser path, inspect supported registries, and resolve `--dataset` / `--model` / `--dw` / `--mw` without training or downloads.
Run `scripts/run_tiny_experiment.py` for a CPU-only tiny NodeDataset dry run; add `--run` only when you explicitly want the helper to train.

Route these elsewhere:
- `../training-wrappers-and-customization/SKILL.md` for low-level `Trainer`, wrapper design, and custom training logic.
- `../graph-data-and-datasets/SKILL.md` for custom `Dataset`, `Graph`, and mask/schema work.
- `../models-layers-and-operators/SKILL.md` for model/layer implementation and operator details.
- `../pipelines-and-applications/SKILL.md` for `pipeline()` apps such as dataset stats, embedding generation, and OAG-BERT.

## What this sub-skill covers

- `experiment(dataset, model=None, **kwargs)` and the `args=` reuse path.
- `get_default_args(dataset, model, **kwargs)` as the parser-backed namespace builder.
- `gen_variants(...)` cartesian products over dataset/model/seed/split.
- `AutoML` / `search_space(trial)` runs, including `n_trials` and validation-metric selection.
- CLI flags for datasets, models, wrappers, seeds, devices, CPU/distributed mode, checkpoints, logs, embeddings, best configs, and trial count.
- Returned result dictionaries and the printed metric table.

## Decision rules

- Keep model families wrapper-compatible when you compare several models in one call. `gcn` and `gat` are safe together; mix-wrapper combinations belong in separate runs.
- Treat built-in datasets as potentially cache- or network-backed on first use.
- Use `cpu=True` or `--cpu` when you want the safest fallback; `--devices` only matters when CPU and distributed mode are off.
- Prefer the API for actual execution when the CLI surface is only being preflighted.
