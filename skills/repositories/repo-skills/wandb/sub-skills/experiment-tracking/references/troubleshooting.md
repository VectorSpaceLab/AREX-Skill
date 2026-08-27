# Experiment Tracking Troubleshooting

## `wandb.init()` fails immediately

Checklist:

1. Validate `id`: run IDs cannot contain `/`, `\`, `#`, `?`, `%`, or `:`.
2. Check `dir` or `settings.root_dir`: the process must be able to create a local W&B run directory there.
3. Increase `settings=wandb.Settings(init_timeout=...)` for slow filesystems or overloaded hosts.
4. Use `mode="offline"` to distinguish network/authentication problems from local SDK problems.
5. Use `mode="disabled"` only when tracking should be bypassed entirely.

Minimal local diagnostic:

```python
with wandb.init(project="debug", mode="offline") as run:
    run.log({"debug/ok": 1})
```

## Unwritable run directory

Symptoms include permission errors, failure to create a `wandb` directory, or init timeouts while local files are being prepared. Fix by passing a writable `dir`:

```python
with tempfile.TemporaryDirectory() as tmp:
    with wandb.init(project="debug", mode="offline", dir=tmp) as run:
        run.log({"ok": 1})
```

If the training process runs inside a container, ensure the mounted work directory is writable by the container user. Do not direct W&B to a read-only source tree in CI.

## Offline versus online confusion

- Offline mode records locally and does not upload during the run.
- Online mode attempts live syncing and may require credentials and network access.
- Disabled mode bypasses normal tracking behavior and is not a substitute for offline capture.
- Syncing offline runs later is a CLI/local workflow; use `../../cli-and-local-workflows/SKILL.md`.

A common safe pattern is to expose a CLI flag or environment-controlled mode:

```python
mode = "offline" if args.offline else None
with wandb.init(project=args.project, mode=mode, config=config) as run:
    ...
```

## Missing API key or authentication prompts

Do not embed keys in source code. For scripts that must run without secrets, use `mode="offline"`. For online runs, let users authenticate with the CLI or set environment credentials outside the code. If `force=True` is set, missing login can stop the script instead of falling back.

## Forgotten `finish()`

If a script exits normally, W&B attempts cleanup, but agents should still add explicit lifecycle management:

```python
run = wandb.init(project="train", config=config)
try:
    train(run)
finally:
    run.finish()
```

Prefer the context manager form when possible. In notebooks, explicit `run.finish()` prevents hidden active runs from affecting later cells.

## Unexpected `reinit` behavior

When `wandb.init()` is called while a run is active:

- It may return the previous active run.
- It may finish previous runs when `reinit=True` or `reinit="finish_previous"`.
- It may create another live run with `reinit="create_new"`.
- In notebooks, default handling is more convenient and can finish previous runs.

Make intent explicit in multi-run scripts:

```python
run1 = wandb.init(project="compare", name="first")
run1.finish()
run2 = wandb.init(project="compare", name="second", reinit="finish_previous")
```

Use `reinit="create_new"` only when multiple concurrent live runs in the same process are deliberate.

## Step and commit misuse

Problems:

- Logging an explicit `step` lower than a previously logged step drops or rejects history.
- Calling `run.log()` for separate metrics without `commit=False` creates separate steps.
- Treating W&B's internal step as the training step makes eval/train loops hard to compare.

Fixes:

```python
run.define_metric("epoch")
run.define_metric("train/*", step_metric="epoch")
run.log({"epoch": epoch, "train/loss": loss})

run.log({"loss": loss}, step=epoch, commit=False)
run.log({"accuracy": acc}, step=epoch, commit=True)
```

## Unsupported logged objects

`Run.log()` expects a dictionary with string keys and serializable values or W&B data types. Convert custom objects before logging:

- Dataclasses: `dataclasses.asdict(obj)`.
- NumPy scalars: `float(value)` or `int(value)`.
- Large arrays: log summary scalars, histograms, media, or bounded tables.
- Model checkpoints and datasets: route to `../../artifacts-and-registries/SKILL.md` instead of stuffing files into metrics.

## Table or media dependency gaps

`wandb.Table` works with plain row data and can often replace richer optional media when dependencies are missing. Rich media may require packages such as NumPy, pandas, Pillow, Plotly, framework tensor libraries, or audio/video codecs.

Graceful fallback:

```python
try:
    run.log({"sample/image": wandb.Image(image_array)})
except Exception as exc:
    run.log({"sample/image_skipped": str(exc)})
    run.log({"sample/pixels_mean": float(image_array.mean())})
```

## Offline smoke helper fails

Run the bundled helper with `--help` first. If execution fails:

1. Confirm the active Python environment imports `wandb`.
2. Pass `--dir` to a writable temporary or project output directory.
3. Reduce `--steps` to isolate initialization from logging loops.
4. Inspect the emitted JSON; it should include `run_id`, `mode`, `summary`, and `run_dir`.
