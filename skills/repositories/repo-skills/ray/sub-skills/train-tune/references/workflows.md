# Ray Train And Tune Workflows

Use these recipes as starting points for bounded, self-contained Train/Tune tasks. Expand framework-specific trainer code only after the minimal Tune/Train wiring works.

## 1. Build A Minimal Tune Sweep

```python
from ray import tune


def objective(config):
    width = config["width"]
    penalty = 0.1 if config["kind"] == "small" else 0.0
    for step in range(2):
        loss = (width - 3) ** 2 + penalty + (1 - step) * 0.01
        tune.report({"loss": loss, "step": step})

trainable = tune.with_resources(objective, {"cpu": 1, "gpu": 0})

results = tune.Tuner(
    trainable,
    param_space={
        "width": tune.grid_search([2, 3, 4]),
        "kind": tune.choice(["small", "large"]),
    },
    tune_config=tune.TuneConfig(metric="loss", mode="min", num_samples=1),
    run_config=tune.RunConfig(name="tiny_tune", storage_path="./ray_results"),
).fit()

best = results.get_best_result()
print(best.config, best.metrics["loss"])
```

Checklist:

- Keep the objective deterministic until the scheduler/result plumbing is proven.
- Use `tune.with_resources` even for small examples so trial resource ownership is explicit.
- Set `metric` and `mode` in `TuneConfig` or pass both to `get_best_result`.
- Set `storage_path` and `name` when you need predictable output locations.

## 2. Add An Early-Stopping Scheduler

```python
from ray import tune
from ray.tune.schedulers import AsyncHyperBandScheduler

scheduler = AsyncHyperBandScheduler(
    metric="loss",
    mode="min",
    max_t=3,
    grace_period=1,
)

results = tune.Tuner(
    tune.with_resources(objective, {"cpu": 1, "gpu": 0}),
    param_space={"width": tune.grid_search([1, 2, 3, 4])},
    tune_config=tune.TuneConfig(
        metric="loss",
        mode="min",
        scheduler=scheduler,
        num_samples=1,
        max_concurrent_trials=2,
    ),
    run_config=tune.RunConfig(stop={"training_iteration": 3}),
).fit()
```

Checklist:

- Report the scheduler metric every iteration.
- Align scheduler `metric`/`mode` with `TuneConfig` unless the scheduler intentionally uses a different signal.
- Set `grace_period` low for tiny smoke tests and higher for real training so early bad noise does not kill promising trials.
- Add `max_concurrent_trials` when each trial is expensive or launches nested Ray work.

## 3. Control Tune Trial Resources

```python
trainable = tune.with_resources(objective, {"cpu": 2, "gpu": 0})
results = tune.Tuner(
    trainable,
    tune_config=tune.TuneConfig(num_samples=8, max_concurrent_trials=2),
).fit()
```

Guidelines:

- Tune defaults to one CPU per trial. If a machine has four CPUs, four one-CPU trials may run concurrently.
- `tune.with_resources(trainable, {"cpu": 2})` reduces parallelism because each trial reserves two CPUs.
- Use fractional CPUs for lightweight trainables only when the code is genuinely low CPU.
- Set `"gpu": 1` to expose one GPU to each trial; otherwise Tune may set `CUDA_VISIBLE_DEVICES` empty for GPU isolation.
- If the trainable starts Ray Data, Ray Core remote tasks, Modin, or a Train trainer, reserve nested resources with a placement group factory or cap concurrency so nested work can schedule.

## 4. Analyze `ResultGrid`

```python
results = tuner.fit()

if results.num_errors:
    for error in results.errors:
        print(error)

best_last = results.get_best_result(metric="loss", mode="min", scope="last")
best_any = results.get_best_result(metric="loss", mode="min", scope="all")
print(best_last.config)
print(best_last.checkpoint)

df = results.get_dataframe(filter_metric="loss", filter_mode="min")
print(df[["config/width", "loss"]])
print(results.experiment_path)
```

Use `scope="last"` when final validation score is authoritative. Use `scope="all"` when any intermediate metric value is meaningful. Use `get_dataframe(filter_metric=..., filter_mode=...)` when comparing each trial's best reported value.

## 5. Configure Train Scaling And Storage

```python
from ray import train

scaling_config = train.ScalingConfig(
    num_workers=2,
    use_gpu=False,
    resources_per_worker={"CPU": 1},
    placement_strategy="PACK",
)

run_config = train.RunConfig(
    name="train_run",
    storage_path="s3://bucket/path",  # Or a shared filesystem URI/path.
    checkpoint_config=train.CheckpointConfig(
        num_to_keep=2,
        checkpoint_score_attribute="val_loss",
        checkpoint_score_order="min",
    ),
)
```

Storage rules:

- Single-node development may use local storage such as `./ray_results` or another local directory.
- Multi-node Train with checkpoints requires storage every worker can write to, such as object storage or a shared filesystem mounted identically on all nodes.
- Local head-node storage is not sufficient for multi-node checkpointing because workers on other nodes cannot reliably upload to the same path.
- When passing a custom `pyarrow.fs.FileSystem`, format `storage_path` as that filesystem expects; custom filesystem examples often omit the URI protocol prefix.

## 6. Report Train Metrics And Checkpoints

The core lifecycle is: write framework state into a temporary local directory, create a Train checkpoint object from that directory, and call `train.report(metrics, checkpoint=checkpoint)`.

```python
import json
import tempfile
from pathlib import Path

from ray import train


def train_loop_per_worker(config):
    for epoch in range(2):
        metrics = {"epoch": epoch, "val_loss": 1.0 / (epoch + 1)}
        if epoch == 1:
            with tempfile.TemporaryDirectory() as tmpdir:
                Path(tmpdir, "state.json").write_text(json.dumps(metrics))
                checkpoint = train.Checkpoint.from_directory(tmpdir)
                train.report(metrics, checkpoint=checkpoint)
        else:
            train.report(metrics)
```

Distributed checkpointing notes:

- For standard data-parallel training where every worker has the full state, report the checkpoint from one worker, often rank 0.
- For sharded strategies, each worker may report its shard; ensure rank-specific file names if files differ.
- Metrics attached to checkpoints are what `CheckpointConfig(checkpoint_score_attribute=...)` uses for retention.
- For large checkpoints, review upload mode and cleanup options in the installed Train API before changing defaults.

## 7. Integrate Train Inside Tune

Use a Tune trainable as a lightweight driver that builds and runs a Train trainer with sampled hyperparameters.

```python
from ray import train, tune


def train_driver_fn(config):
    scaling_config = train.ScalingConfig(
        num_workers=config["num_workers"],
        use_gpu=config.get("use_gpu", False),
        resources_per_worker={"CPU": 1},
    )
    run_config = train.RunConfig(
        name="inner_train",
        checkpoint_config=train.CheckpointConfig(
            num_to_keep=1,
            checkpoint_score_attribute="val_loss",
            checkpoint_score_order="min",
        ),
    )
    # Create the selected Ray Train trainer here, passing scaling_config,
    # run_config, and train_loop_config derived from config.
    # result = trainer.fit()
    # tune.report({"val_loss": result.metrics["val_loss"]})
    tune.report({"val_loss": 1.0 / config["num_workers"]})

results = tune.Tuner(
    tune.with_resources(train_driver_fn, {"cpu": 1}),
    param_space={"num_workers": tune.grid_search([1, 2]), "use_gpu": False},
    tune_config=tune.TuneConfig(
        metric="val_loss",
        mode="min",
        max_concurrent_trials=1,
    ),
).fit()
```

Integration rules:

- Tune controls the sampled config and outer result selection.
- Train controls distributed workers, worker resources, framework setup, and Train checkpoints.
- The Tune trial driver usually reserves only a small CPU amount; the Train `ScalingConfig` reserves worker resources.
- Calculate `max_concurrent_trials` from the limiting worker resource. Example: with eight GPUs and `ScalingConfig(num_workers=4, use_gpu=True)`, only two Train runs can fit concurrently, so set `max_concurrent_trials=2` or lower.
- Do not add a Tune checkpoint just to duplicate Train worker checkpoints. Report metric summaries and checkpoint paths as metrics if the outer Tune analysis needs them.

## 8. Use Tune With Ray Data Or Nested Ray Work

When a Tune trainable launches Ray Data pipelines or other remote work, avoid consuming every CPU with trial actors.

```python
results = tune.Tuner(
    tune.with_resources(trainable_that_uses_data, {"cpu": 1}),
    tune_config=tune.TuneConfig(num_samples=8, max_concurrent_trials=2),
).fit()
```

Checklist:

- Leave spare CPUs for Ray Data read/map/write tasks or child actors.
- If the trainable needs a fixed bundle of nested resources, use a Tune placement group factory rather than a simple resource dict.
- Start with `max_concurrent_trials=1` when diagnosing hangs, then increase gradually.
- Route Data-specific batching, file IO, and block tuning to the Data sub-skill.

## 9. Restore Or Resume Tune Results

```python
restored = tune.Tuner.restore(
    results.experiment_path,
    trainable=trainable,
    param_space=original_param_space,
)
restored_results = restored.fit()
```

Safety notes:

- Restore only trusted experiment directories because experiment state uses serialized Python objects.
- Keep the trainable and search space compatible with the original run. Changing the hyperparameter space and resuming is not supported.
- When restoring from cloud or a moved location, the full experiment directory including checkpoints must be present.

## 10. Bounded Smoke Validation

Use the bundled helper for fast validation:

Run these commands from the `train-tune` sub-skill directory:

```bash
python scripts/tune_train_smoke.py --help
python scripts/tune_train_smoke.py --check-imports
python scripts/tune_train_smoke.py --run-tune --num-samples 2 --steps 2
```

The default mode performs import and signature checks only. `--run-tune` starts a tiny local Tune run with deterministic metrics, no external ML frameworks, and explicit CPU resources.

## 11. Integrated Data + Tune + Core Laptop Recipe

Use this pattern when a small Ray Data preprocessing step feeds a bounded Tune sweep on a laptop or small development node:

```python
import ray
from ray import tune

ray.init(num_cpus=4, ignore_reinit_error=True)

rows = [{"id": i, "value": float(i)} for i in range(12)]
dataset = ray.data.from_items(rows, override_num_blocks=2)
features = dataset.map(lambda row: {**row, "feature": row["value"] * 2}).take_all()

def objective(config):
    width = config["width"]
    loss = sum((row["feature"] - width) ** 2 for row in features) / len(features)
    tune.report({"loss": loss})

results = tune.Tuner(
    tune.with_resources(objective, {"cpu": 1, "gpu": 0}),
    param_space={"width": tune.grid_search([4.0, 8.0, 12.0])},
    tune_config=tune.TuneConfig(metric="loss", mode="min", max_concurrent_trials=2),
    run_config=tune.RunConfig(name="data_tune_laptop_smoke"),
).fit()
print(results.get_best_result().config)
ray.shutdown()
```

Pre-scale checks:

```bash
python ../../scripts/check_ray_environment.py --require core --require data --require tune
python ../data-pipelines/scripts/data_pipeline_smoke.py --run --rows 4 --num-blocks 2
python scripts/tune_train_smoke.py --run-tune --num-samples 2 --steps 2
```

Keep `max_concurrent_trials` low enough to leave CPUs for Ray Data reads/maps or nested tasks. If the Tune trainable starts additional Ray workers, reduce the trial resources or concurrency before scaling to a cluster.
