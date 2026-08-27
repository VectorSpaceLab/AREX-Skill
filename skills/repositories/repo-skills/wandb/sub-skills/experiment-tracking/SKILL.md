---
name: experiment-tracking
description: "Add, debug, and validate W&B experiment tracking in Python scripts
  or notebooks using runs, metrics, config, summary, tables/media/plots,
  offline/disabled modes, and framework-routing decisions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Experiment Tracking

Use this sub-skill when a task involves instrumenting Python code with `wandb.init()`, `Run.log()`, run config/summary, custom metric axes, tables/media/plots, notebook run lifecycle, or offline-safe tracking. For artifact lineage, model/dataset registries, and `run.log_artifact()`, route to `../artifacts-and-registries/SKILL.md`; for `wandb sync`, `wandb offline`, and local CLI workflows, route to `../cli-and-local-workflows/SKILL.md`; for hyperparameter sweeps or launch queues, route to `../sweeps-and-launch/SKILL.md`.

## Start Here

- Add W&B to scripts with `with wandb.init(project=..., config=...) as run:` and `run.log({...})`; see `references/workflows.md`.
- Use `mode="offline"` for credentials-free local capture and later syncing; use `mode="disabled"` when tracking must become no-op in tests.
- Keep metric steps monotonic. Prefer logging a custom x-axis metric and binding charts with `run.define_metric()` instead of forcing W&B's internal step to equal training step.
- Put hyperparameters and static inputs in `config`; put final scalar outcomes or derived labels in `run.summary`; put time-series values in `run.log()`.
- Use `scripts/offline_tracking_smoke.py` to verify that a Python environment can initialize a local run, log metrics, define custom axes, log a table, and finish without network or credentials.

## Reference Map

- `references/workflows.md`: copyable instrumentation patterns for scripts, notebooks, offline mode, custom axes, config/summary, tables/media/plots, and framework integration routing.
- `references/api-reference.md`: precise signatures, lifecycle semantics, logging rules, settings, data type constraints, and version-specific caveats.
- `references/troubleshooting.md`: diagnosis playbooks for init failures, invalid IDs, unwritable directories, missing API keys, forgotten finish, `reinit`, step/commit misuse, unsupported objects, and optional media dependencies.

## Safe Defaults

```python
import wandb

config = {"epochs": 10, "lr": 3e-4, "batch_size": 32}

with wandb.init(project="my-project", config=config) as run:
    run.define_metric("epoch")
    run.define_metric("train/*", step_metric="epoch")
    for epoch in range(config["epochs"]):
        loss = 1.0 / (epoch + 1)
        run.log({"epoch": epoch, "train/loss": loss})
    run.summary["best_train_loss"] = loss
```

For offline smoke validation:

```bash
python sub-skills/experiment-tracking/scripts/offline_tracking_smoke.py --steps 3
```
