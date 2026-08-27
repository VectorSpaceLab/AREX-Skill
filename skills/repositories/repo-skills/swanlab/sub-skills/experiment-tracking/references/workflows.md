# Experiment Tracking Workflows

Use these recipes to add SwanLab to training/evaluation code without requiring credentials or network access during development. Replace `mode="disabled"` with `"local"`, `"offline"`, or `"online"` only after deciding the runtime mode in the `settings-and-modes` sub-skill.

## 1. Credential-safe quick start

The public quick start initializes a project, logs a config, then logs metrics in a loop. For examples, tests, and user code where credentials may be absent, keep the same structure but choose a safe mode explicitly:

```python
import swanlab

run = swanlab.init(
    mode="disabled",          # safe for smoke tests; use "offline" or "local" for local records
    project="my-first-ml",
    config={"learning-rate": 0.003},
)
try:
    for step in range(10):
        swanlab.log({"loss": 10 - step, "acc": step / 10}, step=step)
finally:
    if swanlab.has_run():
        swanlab.finish()
```

When the user asks for the cloud quick start but has not provided credential setup, produce offline-safe or disabled-safe code first and explain that online mode requires login/API-key setup handled by `settings-and-modes`.

## 2. Local/offline training template

Use `offline` when the user wants records saved locally for later sync. Use `local` when the user wants local-only visualization/runtime files. Both modes create run directories, so choose a writable `log_dir` when running in restricted environments.

```python
import swanlab

with swanlab.init(
    mode="offline",
    project="resnet-ablation",
    name="baseline-lr3e-4",
    description="Baseline run without cloud upload during training.",
    config={
        "model": "resnet18",
        "learning_rate": 3e-4,
        "batch_size": 64,
    },
) as run:
    for step in range(num_steps):
        metrics = train_one_step(step)
        swanlab.log(
            {
                "train/loss": metrics["loss"],
                "train/acc": metrics["accuracy"],
            },
            step=step,
        )

    run.config["best_metric"] = best_metric
```

Notes:

- A context manager calls `finish()` automatically.
- Nested metric dictionaries are also acceptable: `swanlab.log({"train": {"loss": loss}})` becomes `train/loss`.
- The code above intentionally does not include API keys, hosts, or sync commands.

## 3. Add logging to an existing training loop

Minimal diff pattern:

```python
import swanlab

run = swanlab.init(mode="offline", project="my-project", config=vars(args))
try:
    for epoch in range(args.epochs):
        train_stats = train_epoch(...)
        valid_stats = evaluate(...)

        swanlab.log(
            {
                "epoch": epoch,
                "train/loss": train_stats.loss,
                "valid/loss": valid_stats.loss,
                "valid/accuracy": valid_stats.accuracy,
            },
            step=epoch,
        )
finally:
    if swanlab.has_run():
        swanlab.finish()
```

Use a `finally` block when not using the context manager, especially in scripts that may raise during training.

## 4. Guarded helper functions

When a utility may be reused inside and outside SwanLab runs, do not call `swanlab.log` unconditionally:

```python
import swanlab


def log_eval_metrics(metrics, step):
    if not swanlab.has_run():
        return
    swanlab.log(
        {
            "eval/loss": metrics["loss"],
            "eval/accuracy": metrics["accuracy"],
        },
        step=step,
    )
```

Use `swanlab.get_run()` instead when absence of a run should be treated as a programming error:

```python
run = swanlab.get_run()  # raises RuntimeError when no run is active
run.config["eval_dataset"] = dataset_name
```

## 5. Reinitialize intentionally

SwanLab rejects two simultaneous active runs in one process. For sequential runs in one script:

```python
import swanlab

for seed in [1, 2, 3]:
    run = swanlab.init(
        mode="disabled",
        project="seed-sweep",
        name=f"seed-{seed}",
        config={"seed": seed},
        reinit=True,
    )
    try:
        swanlab.log({"score": run_experiment(seed)}, step=0)
    finally:
        swanlab.finish()
```

`reinit=True` finishes the previous run before starting the next one. If you need overlapping concurrent runs, run them in separate processes and initialize SwanLab separately inside each process.

## 6. Config dictionaries and config files

Dictionary config:

```python
run = swanlab.init(
    mode="offline",
    project="config-demo",
    config={"optimizer": "adamw", "lr": 1e-4},
)
```

JSON/YAML config file:

```python
run = swanlab.init(
    mode="offline",
    project="config-demo",
    config="config.yaml",
)
```

Post-init config:

```python
run.config["effective_batch_size"] = batch_size * grad_accum
swanlab.config.update({"dataset_hash": dataset_hash})
```

Keep config values simple and serializable. If a file path is passed to `config`, it must exist and parse as JSON or YAML.

## 7. Scalar metric naming

Recommended patterns:

```python
swanlab.log({
    "train/loss": float(loss),
    "train/lr": float(lr),
    "valid/accuracy": float(acc),
}, step=global_step)
```

or:

```python
swanlab.log({
    "train": {"loss": float(loss), "lr": float(lr)},
    "valid": {"accuracy": float(acc)},
}, step=global_step)
```

Avoid:

- Empty keys, only slashes/dots/spaces, or control characters.
- Negative or non-integer steps.
- Large tensors/arrays as scalar values. Convert to `.item()`, `float(...)`, or a supported media object.
- Non-numeric strings as scalar values.

## 8. Optional `define_scalar`

This version exposes `define_scalar` but does not implement it yet. If a user asks to predefine scalar display names/charts, keep it optional:

```python
try:
    swanlab.define_scalar(key="train/loss", name="Training loss")
except NotImplementedError:
    # Current SwanLab versions may not support this yet.
    pass
```

Do not present `define_scalar` as required for normal logging; ordinary `swanlab.log` works without it.

## 9. Save checkpoints or artifacts

For local/offline runs:

```python
from pathlib import Path
import swanlab

with swanlab.init(mode="offline", project="checkpoint-demo") as run:
    ckpt_dir = Path("checkpoints")
    ckpt_dir.mkdir(exist_ok=True)
    (ckpt_dir / "model.pt").write_bytes(b"placeholder weights")

    matched = run.save("*.pt", base_path=ckpt_dir, policy="end")
    assert matched == ["model.pt"]
```

Guidance:

- Use an explicit `base_path` so stored relative names are predictable.
- Use `policy="end"` when the file is finalized before finish.
- Use `policy="now"` for immediate handling.
- Use `policy="live"` only when watching/updating files during a longer run is desired.
- If `save` returns `[]`, check the glob, base path, file existence, and policy spelling.

## 10. Asynchronous metric computation

Threading mode for lightweight or I/O-bound work:

```python
import swanlab


def compute_metrics(batch_id):
    return {"async/score": float(batch_id)}

with swanlab.init(mode="disabled", project="async-demo"):
    future = swanlab.async_log(compute_metrics, 3, step=3, mode="threading")
    # finish waits for the future and logs its returned dictionary
```

Asyncio mode when already inside an event loop:

```python
async def compute_async():
    return {"async/acc": 0.95}

future = swanlab.async_log(compute_async, step=1, mode="asyncio")
```

Spawn mode for pickle-safe CPU-bound work:

```python
def compute_loss(seed):
    return {"spawn/loss": float(seed) / 10}

future = swanlab.async_log(compute_loss, 7, step=7, mode="spawn")
```

Avoid `mode="fork"`; it is reserved and currently not implemented. In spawned processes, do not access the parent active run. Return a plain dictionary and let the parent log it.

## 11. Disabled-mode smoke recipe

Use disabled mode for unit tests and installation checks:

```python
import swanlab

run = swanlab.init(mode="disabled", project="smoke", config={"lr": 0.001})
assert swanlab.run is run
swanlab.log({"loss": 0.1, "acc": 0.9}, step=0)
swanlab.finish()
assert swanlab.run is None
```

The bundled script expands this into an executable check: [../scripts/check_disabled_tracking.py](../scripts/check_disabled_tracking.py).
