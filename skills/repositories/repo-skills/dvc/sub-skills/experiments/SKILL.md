---
name: experiments
description: "Run, queue, compare, promote, share, and clean up DVC experiments
  without confusing them with ordinary pipeline reproduction."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# DVC Experiments

Use this sub-skill when a user asks to run, queue, compare, apply, branch, push, pull, rename, remove, save, or clean DVC experiments with the `dvc exp`/`dvc experiments` command family or the public experiments API.

## Route Here For

- Running experiments with `dvc exp run`, including `--name`, `--set-param`, `--queue`, `--run-all`, `--jobs`, `--temp`, `--copy-paths`, `--message`, and `--no-hydra`.
- Comparing and inspecting experiments with `dvc exp show`, `dvc exp diff`, `dvc exp list`/`ls`, and the bundled `scripts/inspect_experiments.py` helper.
- Promoting or restoring experiment results with `dvc exp apply`, `dvc exp branch`, and `dvc exp save`.
- Sharing and maintaining experiment refs with `dvc exp push`, `dvc exp pull`, `dvc exp rename`, `dvc exp remove`/`rm`, and `dvc exp clean`.

## Route Elsewhere

- Use `../data-and-pipelines/` for creating stages, `dvc.yaml`, dependencies, outs, and normal `dvc repro` pipeline design.
- Use `../metrics-params-plots/` for interpreting metrics, params, and plots beyond how `dvc exp show` surfaces them.
- Use `../remotes-and-cache/` for configuring remotes, credentials, cache layout, and storage backends used by `exp push/pull --remote`.

## Read Next

- Read `references/workflows.md` for concrete run, queue, compare, promote, share, and cleanup recipes.
- Read `references/api-reference.md` for `dvc.api.exp_save()` and `dvc.api.exp_show()` signatures, returns, and safe usage.
- Read `references/troubleshooting.md` when experiments are hidden, stale, queued, failed, blocked by workspace state, missing copied files, or affected by Hydra/network boundaries.
- Run `python scripts/inspect_experiments.py --help` to inspect experiments as JSON through the public API without network access by default.

## Default Decision Pattern

1. Confirm that the user already has a DVC project with a pipeline; if not, route to `data-and-pipelines` first.
2. Use `dvc exp run` for a one-off experiment that should execute now, `dvc exp run --queue` for parameter sweeps or deferred execution, and `dvc exp run --run-all -j <n>` to execute queued experiments.
3. Use `dvc exp show --json` or the bundled inspector for machine-readable comparison; use `dvc exp diff` for pairwise metric/param changes.
4. Use `dvc exp apply` for workspace inspection, `dvc exp branch` for durable Git review, and `dvc exp push/pull` only after remote and cache behavior are clear.
