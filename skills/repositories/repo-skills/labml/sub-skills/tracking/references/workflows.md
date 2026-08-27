# Tracking Workflows

## Purpose

Read this for end-to-end recipes that combine the client APIs, hardware
monitoring, and app publishing patterns.

## 1) Record and watch a training loop

Use this pattern when you want to track loss, accuracy, or custom tensors while
printing readable progress.

1. Create a `.labml.yaml` file at the project root or configure LabML
   programmatically with `lab.configure`.
2. Start the run with `experiment.create(...)` or `experiment.record(...)`.
3. Use `tracker.add(...)` during each step and `tracker.save(...)` to flush.
4. Wrap training and validation loops in `monit.loop(...)` or `monit.section(...)`
   to get timing information.
5. Use `logger.log(...)` for human-readable milestones and summaries.

Typical shape:

```python
from labml import experiment, tracker, monit, logger

with experiment.record(name="demo", writers={"screen", "file"}):
    for step in monit.loop(3):
        tracker.add(loss=1 / (step + 1))
        tracker.save()
        logger.log(f"step={step}")
```

## 2) Configure runs and dynamic parameters

The config system is useful when a training loop needs swapable options or
computed values.

- Subclass `labml.configs.BaseConfigs`.
- Register computed values with `@option(...)` or `calculate(...)`.
- Mark hyperparameters with `hyperparams(...)`.
- Call `experiment.configs(conf)` or `experiment.record(..., exp_conf=...)`.
- Use `lab.configure(...)` when the settings belong to the project rather than a
  single experiment.

This is the same pattern used by the config-heavy sample scripts and by the
`.labml.yaml` defaults.

## 3) Monitor hardware locally

`labml monitor` is for read-only hardware reporting. The useful support path is:

1. Install `psutil` for CPU, memory, disk, and process counters.
2. Install `py3nvml` when you also want NVIDIA GPU metrics.
3. Run `labml monitor` to start the monitor.
4. Run `labml service` only when you want a user-level systemd service.

The client can still run without `py3nvml`; it will just report fewer GPU
metrics.

## 4) Publish to the app backend

The client can send run data to a monitoring backend through `AppAPI` or through
a configured app URL.

1. Make sure the backend URL is valid and reachable.
2. Use `experiment.record(..., app_url=...)` or set `app_url` in the project
   configuration.
3. Use `AppAPI` for direct inspection of runs, analyses, logs, metrics, and data
   stores.
4. If you see network or version errors, compare the client version with the
   server API version before debugging deeper.

## 5) Framework integration patterns

### PyTorch

- Record with `experiment.create` or `experiment.record`.
- Use `tracker.add`/`tracker.save` inside the training loop.
- Use `monit.loop` for epoch or batch progress.
- Optionally checkpoint a model with LabML-managed writers.

### Lightning, Keras, and FastAI

- Keep the framework-specific training step untouched when possible.
- Add tracking calls around step, validation, and logging boundaries.
- Use the same `experiment` and `tracker` API from the client package.
- Treat framework packages as optional extras, not as core LabML dependencies.

### Custom analytics and richer plots

- Use the app-backed run metadata and data-store APIs for custom views.
- Keep the recorded names stable so the UI can group indicators predictably.
- Prefer a small number of clearly named scalars and tensors over opaque blobs.

## 6) Git metadata and dirty-repo checks

`labml` can store git metadata and can optionally abort if the repo is dirty.

- If you see a dirty-repo warning, either commit or disable the check in your
  project config.
- If git information is missing, check that `gitpython` is installed and that the
  project root is a Git repository.

## 7) When to use the smoke script

Use `scripts/tracking_smoke.py` when you want a local, low-risk sanity check for
logging, tracking, and experiment output paths without opening the original
repository examples.
