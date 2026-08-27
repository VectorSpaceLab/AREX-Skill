---
name: train-tune
description: "Use Ray Train and Ray Tune for distributed training,
  checkpointing, hyperparameter tuning, resources, and result analysis."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Ray Train And Tune

Use this sub-skill when the task mentions `ray.train`, `ScalingConfig`, `RunConfig`, `CheckpointConfig`, `train.report`, `ray.tune.Tuner`, `TuneConfig`, `tune.report`, search spaces, schedulers, `with_resources`, `ResultGrid`, `max_concurrent_trials`, or `storage_path`.

## Fast Routing

- Use Ray Train when the main problem is distributed training orchestration: training workers, scaling configs, checkpoints, fault tolerance, persistent storage, and training callbacks.
- Use Ray Tune when the main problem is experiment execution or hyperparameter tuning: trainables, search spaces, schedulers/search algorithms, per-trial resources, concurrency, output folders, and best-result analysis.
- Use Train and Tune together by letting Tune launch trials and letting each trial create a Train trainer or training driver; cap `max_concurrent_trials` so inner Train workers can acquire resources.
- Route Ray Data input pipeline construction to `../data-pipelines/SKILL.md`, Ray Core placement/resource semantics to `../core-runtime/SKILL.md`, trained artifact serving to `../serve-deployments/SKILL.md`, and RLlib `AlgorithmConfig` work to `../rllib-workloads/SKILL.md`.

## Minimal Tune Pattern

```python
from ray import tune


def objective(config):
    score = (config["width"] - 3) ** 2
    tune.report({"loss": score})

results = tune.Tuner(
    tune.with_resources(objective, {"cpu": 1, "gpu": 0}),
    param_space={"width": tune.grid_search([2, 3, 4])},
    tune_config=tune.TuneConfig(metric="loss", mode="min"),
    run_config=tune.RunConfig(name="small_sweep", storage_path="./ray_results"),
).fit()
print(results.get_best_result().config)
```

## Read Next

- Read `references/api-reference.md` for verified signatures and how Train/Tune objects relate.
- Read `references/workflows.md` for checkpoint/storage recipes, Tune sweeps, scheduler/resource examples, ResultGrid analysis, and Train+Tune integration.
- Read `references/troubleshooting.md` for missing extras, storage mistakes, metric/mode mismatches, resource deadlocks, GPU visibility, checkpoint/report misuse, and output locations.
- Run `python scripts/tune_train_smoke.py --help` for a safe helper. Add `--run-tune` only when starting a tiny local Ray Tune run is acceptable.

## Installation Notes

- Prefer narrow extras: `ray[train]` for Train workloads and `ray[tune]` for Tune workloads. Add framework extras or packages only for the selected trainer/search algorithm.
- Python support for this Ray family is `>=3.10`.
- Avoid recommending `ray[all]` by default; it can install unnecessary dependencies for unrelated Ray libraries.
