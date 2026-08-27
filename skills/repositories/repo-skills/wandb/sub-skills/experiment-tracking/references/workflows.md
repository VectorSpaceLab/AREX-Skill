# Experiment Tracking Workflows

## Add W&B to a training script

1. Import `wandb` near other optional telemetry imports.
2. Build a plain dictionary of static inputs: model name, dataset name, seed, learning rate, batch size, epochs, and feature flags.
3. Wrap the training body with `with wandb.init(project=..., entity=..., config=config) as run:` so `run.finish()` is called even when the block exits.
4. Log a compact dictionary once per reporting interval, not every inner-loop operation.
5. Write final outcomes into `run.summary` after training.

```python
import wandb

config = {"epochs": 20, "learning_rate": 3e-4, "seed": 42}

with wandb.init(project="classifier", config=config, tags=["baseline"]) as run:
    run.define_metric("epoch")
    run.define_metric("train/*", step_metric="epoch")
    run.define_metric("val/*", step_metric="epoch")

    best_accuracy = 0.0
    for epoch in range(config["epochs"]):
        train_loss = train_one_epoch(epoch, config)
        val_accuracy = evaluate(epoch)
        best_accuracy = max(best_accuracy, val_accuracy)
        run.log({
            "epoch": epoch,
            "train/loss": train_loss,
            "val/accuracy": val_accuracy,
        })

    run.summary["best_val_accuracy"] = best_accuracy
```

If the code cannot use a context manager, assign `run = wandb.init(...)` and call `run.finish()` in a `finally` block.

## Migrate ad-hoc JSON logging

When replacing JSONL or dictionary accumulation:

- Preserve the user's original keys where possible, but group related metrics with one slash, such as `train/loss` and `val/loss`.
- Keep static metadata in `config`, not repeated in every `run.log()` call.
- If the old logs contain arbitrary step fields, log the field and call `run.define_metric()` to make it the x-axis.
- If the old logs contain per-example predictions, create a `wandb.Table` and log it once per split or evaluation epoch.

```python
with wandb.init(project="migration", config={"dataset": dataset_name}) as run:
    run.define_metric("train_step")
    run.define_metric("train/*", step_metric="train_step")

    for row in legacy_json_rows:
        run.log({
            "train_step": row["step"],
            "train/loss": row["loss"],
            "train/learning_rate": row["lr"],
        })

    predictions = wandb.Table(
        columns=["example_id", "target", "prediction", "confidence"],
        data=[[p.id, p.target, p.label, p.confidence] for p in eval_predictions],
    )
    run.log({"eval/predictions": predictions})
```

## Offline-safe tracking

Use `mode="offline"` when a task must run without credentials, outside CI secrets, on an air-gapped host, or in a verification script. Offline runs write to the local W&B run directory and can be uploaded later with the CLI; sync details belong in `../../cli-and-local-workflows/SKILL.md`.

```python
with wandb.init(project="local-debug", mode="offline", config=config) as run:
    run.log({"debug/loss": 0.5})
```

Use `mode="disabled"` when W&B should become a no-op while preserving code paths, such as unit tests that should not create run directories.

```python
run = wandb.init(mode="disabled")
run.log({"metric": 1})
run.finish()
```

## Notebook lifecycle

Notebook users often prefer explicit lifecycle management because cells are rerun independently:

```python
run = wandb.init(project="notebook-experiments", config=config)
try:
    run.log({"cell_metric": 1})
finally:
    run.finish()
```

When a run is already active, `wandb.init()` may return the previous run, finish the previous run, or create a new run depending on `reinit`. For notebooks, the default behavior is user-friendly and may finish previous runs. Use `reinit="create_new"` only when multiple live runs in one process are intentional; use `reinit="finish_previous"` to make sequential notebook cells deterministic.

## Custom axes and multi-phase metrics

`Run.log()` has a monotonically increasing internal step. For training/evaluation loops with separate counters, log explicit axis metrics and bind namespaces:

```python
with wandb.init(project="multi-phase") as run:
    run.define_metric("train_step")
    run.define_metric("eval_step")
    run.define_metric("train/*", step_metric="train_step")
    run.define_metric("eval/*", step_metric="eval_step")

    for train_step in range(100):
        run.log({"train_step": train_step, "train/loss": train_loss(train_step)})
        if train_step % 10 == 0:
            eval_step = train_step // 10
            run.log({"eval_step": eval_step, "eval/accuracy": evaluate()})
```

Avoid logging to an earlier `step`. To split a single logical step across calls, use `commit=False` followed by a committing call for the same step.

## Config and summary

- `config` is for inputs and hyperparameters. Values should be JSON/YAML-friendly and smaller than the SDK's practical config-size limits.
- Config keys should not contain periods. Use underscores or nested dictionaries instead.
- By default, scripts do not allow changing an existing config value; notebooks are more permissive. For changing training values, log metrics instead of mutating config.
- `run.summary` is for final or aggregate outputs such as `best_accuracy`, `final_loss`, selected checkpoint name, or dataset split counts.

```python
run.config.update({"model_family": "resnet", "optimizer": "adamw"})
run.summary["best_epoch"] = best_epoch
run.summary["best_val_accuracy"] = best_accuracy
```

## Tables, media, and plots

Use `wandb.Table` for structured rows. Tables accept `columns` plus row-oriented `data`, a NumPy array, or a pandas DataFrame. Keep tables bounded; default table logging is immutable, so build the table before logging unless using mutable/incremental modes intentionally.

```python
examples = wandb.Table(
    columns=["id", "text", "label", "prediction"],
    data=[[ex.id, ex.text, ex.label, pred] for ex, pred in batch_predictions],
)
run.log({"eval/examples": examples})
```

Common media and plots:

```python
run.log({"samples/images": [wandb.Image(image, caption=label) for image, label in samples]})
run.log({"charts/loss_curves": wandb.plot.line_series(
    xs=list(range(len(train_losses))),
    ys=[train_losses, val_losses],
    keys=["train", "validation"],
    title="Loss curves",
    xname="epoch",
)})
run.log({"charts/confusion_matrix": wandb.plot.confusion_matrix(
    y_true=y_true,
    preds=y_pred,
    class_names=class_names,
)})
```

Some media paths depend on optional libraries such as Pillow, NumPy, pandas, Plotly, audio/video codecs, or framework-specific tensor packages. If optional dependencies are unavailable, log scalars/tables first and degrade rich media gracefully.

## Framework integration routing

If the user asks for a specific ML framework, first check whether the framework has a native W&B integration or callback. Use this sub-skill for the common tracking concepts and hand-written `wandb.init()`/`run.log()` instrumentation. Use framework-specific integration documentation in the repository or adjacent generated sub-skills when the task is primarily about a trainer callback, environment variable bridge, or framework logger configuration.

Keep these boundaries:

- Artifact lineage, model registry, and dataset versioning: `../../artifacts-and-registries/SKILL.md`.
- CLI sync, local status, offline-to-online upload, and login commands: `../../cli-and-local-workflows/SKILL.md`.
- Sweeps, agents, launch jobs, and queues: `../../sweeps-and-launch/SKILL.md`.
