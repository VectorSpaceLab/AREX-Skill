# Tracking workflows

This guide shows practical Aim SDK instrumentation patterns for local repositories. The examples avoid CLI/server workflows and optional framework callbacks; route those requests to the sibling sub-skills.

## Initialize or open a local repository from Python

Use an explicit repository directory in scripts and tests:

```python
from pathlib import Path
from aim import Repo

repo_dir = Path("./aim-repo").resolve()
repo_dir.mkdir(parents=True, exist_ok=True)
repo = Repo.from_path(str(repo_dir), init=True)
try:
    ...
finally:
    repo.close()
```

Notes:

- `init=True` creates the Aim repository if missing.
- Do not pass `read_only=True` to `Repo` in this Aim version; use read-only `Run` objects instead.
- In short validation scripts, create a persistent temporary directory with `tempfile.mkdtemp()`, not a `TemporaryDirectory` context that can be removed while Aim cleanup finalizers are still flushing.

## Create a run with deterministic tracking knobs

```python
from aim import Run

run = Run(
    repo=repo,
    experiment="baseline",
    system_tracking_interval=None,
    log_system_params=False,
    capture_terminal_logs=False,
)
try:
    run.name = "baseline-seed-0"
    run.description = "Tiny validation run"
    run.add_tag("smoke")
    run["hparams"] = {
        "optimizer": {"name": "adam", "lr": 1e-3},
        "batch_size": 32,
        "seed": 0,
    }
finally:
    run.close()
```

Use default `system_tracking_interval=10`, `log_system_params=True`, or `capture_terminal_logs=True` only when the user needs those records. For unit tests and smoke checks, disable them for less background activity.

## Add Aim to a train/validation loop

This pattern tracks nested hyperparameters, metrics in separate contexts, and media samples. The same metric names can be reused for train and validation because `context` is part of the sequence identity.

```python
from aim import Distribution, Image, Repo, Run, Text
import numpy as np

repo = Repo.from_path("./aim-repo", init=True)
run = Run(repo=repo, experiment="classifier", system_tracking_interval=None, capture_terminal_logs=False)
try:
    run.name = "classifier-tiny"
    run["hparams"] = {
        "model": {"hidden_dim": 16, "dropout": 0.1},
        "optimizer": {"name": "adam", "lr": 1e-3},
        "data": {"train_size": 128, "val_size": 32},
    }

    for epoch in range(2):
        for step in range(4):
            global_step = epoch * 4 + step
            train_loss = 1.0 / (global_step + 1)
            val_loss = 0.8 / (global_step + 1)
            val_accuracy = 0.70 + 0.02 * global_step

            run.track({"loss": train_loss}, step=global_step, epoch=epoch, context={"subset": "train"})
            run.track(
                {"loss": val_loss, "accuracy": val_accuracy},
                step=global_step,
                epoch=epoch,
                context={"subset": "val"},
            )

        # Track occasional rich objects, not every batch.
        image_array = np.zeros((8, 8, 3), dtype=np.uint8)
        image_array[:, :, 1] = 64 + 20 * epoch
        run.track(Image(image_array, caption=f"validation sample epoch {epoch}"), name="samples", step=epoch, context={"subset": "val"})
        run.track(Text(f"epoch {epoch} validation summary"), name="notes", step=epoch, context={"subset": "val"})
        run.track(Distribution.from_samples([train_loss, val_loss, val_accuracy], bin_count=3), name="score_distribution", step=epoch)
finally:
    run.close()
    repo.close()
```

## Track scalars and dictionaries

Single value:

```python
run.track(0.25, name="loss", step=12, epoch=1, context={"subset": "train"})
```

Multiple values in one context:

```python
run.track({"loss": 0.22, "accuracy": 0.91}, step=12, epoch=1, context={"subset": "val"})
```

Rules:

- When `value` is a dict, do not pass `name`.
- When `value` is not a dict, always pass `name`.
- The dictionary keys are stringified and become sequence names.
- Keep each `(run, name, context)` sequence type stable.

## Track media and objects safely

```python
from aim import Audio, Distribution, Figure, Image, Text
import io
import numpy as np

run.track(Image(np.zeros((8, 8, 3), dtype=np.uint8), caption="blank"), name="images", step=0)
run.track(Text("qualitative note"), name="notes", step=0)
run.track(Distribution.from_samples([0.1, 0.2, 0.3], bin_count=3), name="weights", step=0)
run.track(Audio(b"RIFF....WAVEfmt ", format="wav", caption="placeholder"), name="audio", step=0)
```

For figures:

```python
# If Plotly is installed:
import plotly.graph_objects as go
from aim import Figure
fig = go.Figure(data=[go.Bar(x=["a", "b"], y=[1, 2])])
run.track(Figure(fig), name="figures", step=0)
```

If Plotly or matplotlib conversion is not available, use `Image(fig)` for a static rendering when possible, or skip figure tracking in the smoke script and record the missing optional dependency.

## Log artifacts

Artifacts require a base URI:

```python
from pathlib import Path

artifact_dir = Path("./artifact-store").resolve()
artifact_dir.mkdir(parents=True, exist_ok=True)
run.set_artifacts_uri(artifact_dir.as_uri())

checkpoint = Path("model.txt")
checkpoint.write_text("tiny checkpoint\n", encoding="utf-8")
run.log_artifact(str(checkpoint), name="model.txt", block=True)
```

For remote or cloud artifact URI policy, confirm credentials and storage backend separately. Keep local smoke checks on `file://` URIs.

## Log messages

```python
run.log_info("training started", epoch=0)
run.log_warning("validation metric plateaued", patience=2)
# run.log_error("fatal condition", batch=17)
```

These records are stored as Aim log record sequences. For minimal tests, prefer explicit `run.log_*` calls over terminal capture.

## Resume or inspect an existing run

Resume for additional writes:

```python
run = Run(run_hash=existing_hash, repo=repo, system_tracking_interval=None, force_resume=True)
try:
    run.track(0.19, name="loss", step=20, context={"subset": "train"})
finally:
    run.close()
```

Read without writes:

```python
from aim.storage.context import Context

read_run = Run(run_hash=existing_hash, repo=repo, read_only=True)
try:
    print(read_run["hparams"])
    metric = read_run.get_metric("loss", context=Context({"subset": "val"}))
finally:
    read_run.close()
```

or:

```python
read_run = repo.get_run(existing_hash)
if read_run is not None:
    try:
        ...
    finally:
        read_run.close()
```

## Close-order template for temporary validation

```python
import gc
import shutil
import tempfile
import time
from pathlib import Path

repo_dir = Path(tempfile.mkdtemp(prefix="aim-sdk-"))
repo = None
run = None
try:
    repo = Repo.from_path(str(repo_dir), init=True)
    run = Run(repo=repo, system_tracking_interval=None, capture_terminal_logs=False)
    run.track(1.0, name="ok")
finally:
    if run is not None:
        run.close()
    if repo is not None:
        repo.close()
    gc.collect()
    time.sleep(0.1)
    try:
        from aim.ext.cleanup import AutoClean
        AutoClean.cleanup()
    except Exception:
        pass
    gc.collect()
    time.sleep(0.1)
    shutil.rmtree(repo_dir, ignore_errors=True)
```

This pattern keeps the directory alive until explicit close calls and Aim cleanup finalizers have had a chance to release RocksDB-backed files.

## Validation workflow

For a new instrumentation patch:

1. Run the user's training/evaluation code with Aim writes pointed at an explicit repo path.
2. Ensure every created `Run` is closed.
3. Reopen the repo and query with `QueryReportMode.DISABLED`.
4. Assert the expected run count, metric names, contexts, last values, and at least one dataframe conversion if pandas is installed.
5. If media is tracked, query the media sequence type (`query_images`, `query_texts`, `query_distributions`, etc.) and verify sequence names/contexts.
6. Run `scripts/aim_sdk_smoke.py` when the environment or cleanup behavior is uncertain.
