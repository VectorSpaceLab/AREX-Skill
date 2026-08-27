---
name: tuning-optimization
description: "Build and validate Optuna hyperparameter optimization commands,
  study reuse, and report artifacts for RL Zoo."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# tuning-optimization

Use this sub-skill when a task is specifically about RL Zoo Optuna hyperparameter optimization (HPO): starting `-optimize` / `--optimize-hyperparameters`, choosing sampler/pruner/budget flags, coordinating shared studies, loading a stored trial, or interpreting HPO report artifacts.

## Route first

- Base training flags, run budgets, device/thread/vector-env choices, resume/checkpoint flags, and ordinary training lifecycle: [`../training-cli/SKILL.md`](../training-cli/SKILL.md).
- YAML/Python hyperparameter files, `-params` override grammar, wrappers/callbacks, and config syntax: [`../config-hyperparams/SKILL.md`](../config-hyperparams/SKILL.md).
- Plotting or benchmarking the resulting files: [`../plotting-benchmarking/SKILL.md`](../plotting-benchmarking/SKILL.md).
- Optional dependency and console-entry caveats: [`../../references/install-and-environment.md`](../../references/install-and-environment.md).

## Runtime entry points

Prefer installed-package commands:

- `python -m rl_zoo3.train ... --optimize-hyperparameters` is the safest base command for HPO because it targets the train module directly.
- `rl_zoo3 train ... --optimize-hyperparameters` is equivalent when the console entry point and optional plot-import path are available.

Use the bundled non-executing helper to build and validate command strings:

```bash
python scripts/tuning_command_builder.py --help
```

The helper does not start training or optimization. It validates high-risk HPO combinations such as `--pruner halving` with too few jobs, `--sampler auto` without `optunahub`, unsupported HPO algorithms, and `--trial-id` without a reusable study.

## References

- [`references/optuna-tuning.md`](references/optuna-tuning.md) — HPO command patterns, flag semantics, lifecycle, and search-space notes.
- [`references/optuna-study-artifacts.md`](references/optuna-study-artifacts.md) — report files, per-trial evaluation logs, storage reuse, and deprecated study-parser handling.
- [`references/troubleshooting.md`](references/troubleshooting.md) — common HPO failures and fast fixes.

## Operating boundaries

- HPO is distinct from ordinary training: always make the training timestep budget and Optuna trial budget explicit before proposing a real run.
- Treat search spaces as algorithm-specific; if an algorithm is not in the HPO sampler/converter map, do not claim it is tunable through RL Zoo HPO without extending that map.
- Do not copy or rely on deprecated source helper scripts for new workflows. Use storage plus `--study-name` / `--trial-id` for trial reuse.
