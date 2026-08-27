# Sync and conversion reference

This reference covers SwanLab local/offline run upload and conversion from TensorBoard, Weights & Biases, and MLflow records. It is intentionally self-contained: use it without reading a repository checkout.

## Decision matrix

| User intent | Best surface | Required input | Network? | Notes |
|---|---|---|---|---|
| Upload an existing SwanLab local/offline run | `swanlab.sync(run_dir, settings=...)` or `swanlab sync RUN_DIR` | SwanLab run directory containing its local run record file | Yes, during upload | Requires an existing login client or an API key in settings/CLI. |
| Validate a SwanLab run path before sync | `scripts/check_sync_guards.py --check-run-dir RUN_DIR` | Candidate directory | No | Confirms basic existence/directory/readability before a real upload. |
| Mirror W&B calls while a script runs | `swanlab.sync_wandb(...)` | Existing training script using `wandb.init/log/finish` | Depends on selected SwanLab/W&B modes | Call before `wandb.init`. Can force W&B itself offline with `wandb_run=False`. |
| Mirror TensorBoard writer calls while a script runs | `swanlab.sync_tensorboardX(...)` or `swanlab.sync_tensorboard_torch(...)` | Training script using TensorBoard writer APIs | Depends on SwanLab mode | Call before creating the writer instance. |
| Mirror MLflow calls while a script runs | `swanlab.sync_mlflow(...)` | Training script using `mlflow` APIs | Depends on SwanLab mode | Call before MLflow experiment/run/logging calls. |
| Convert saved TensorBoard event files | `TFBConverter(...).run(convert_dir=...)` or `swanlab convert --type tensorboard` | Directory tree containing `tfevents` files | Usually yes because converter creates SwanLab runs | Python default converts scalar/image/audio/text; CLI default is scalar only unless `--tb-types` is set. |
| Convert W&B cloud runs | `WandbConverter(...).run(...)` or `swanlab convert --type wandb` | W&B project and entity, optional run id | Yes | Requires W&B package and W&B access, plus SwanLab credentials for created runs. |
| Convert local W&B files | `WandbLocalConverter(...).run(...)` or `swanlab convert --type wandb-local` | W&B root such as `wandb/`, optional run directory | Usually yes because converter creates SwanLab runs | Searches `run-*` and `offline-run-*` directories and reads `.wandb` files. |
| Convert MLflow runs | `MLFlowConverter(...).run(...)` or `swanlab convert --type mlflow` | Tracking URI and experiment id/name, optional run id | Yes to MLflow server and usually SwanLab | Converts params/tags/config and metric histories. |

## `swanlab.sync` local run upload

Programmatic shape:

```python
import swanlab
from swanlab import Settings

swanlab.sync(
    "runs/offline-run-123",
    settings=Settings(
        api_key="...",  # omit only when already logged in
        api_host="https://api.example.invalid",
        project=Settings.Project(workspace="team", name="project"),
        run=Settings.Run(id="target-run-id"),
    ),
)
```

CLI shape:

```bash
swanlab sync RUN_DIR [RUN_DIR ...] \
  --api-key API_KEY \
  --host https://api.example.invalid \
  --workspace WORKSPACE \
  --project PROJECT \
  --id TARGET_RUN_ID
```

Important behavior:

- `run_dir` must already exist, must be a directory, and must be readable. Programmatic sync resolves it to an absolute path after validation; the CLI also rejects non-existing or unreadable non-directories before calling sync.
- The run directory should be the SwanLab run directory that contains the local SwanLab run record file. Do not pass a TensorBoard log directory, a W&B root, an MLflow tracking URI, or a parent directory containing many unrelated runs unless each child is explicitly passed as its own run directory.
- If no SwanLab client/login exists, sync requires `settings.api_key` or CLI `--api-key`. Without either, it raises an authentication error telling the user to log in first or call `swanlab.login()`.
- `--host` / `Settings(api_host=...)` targets the API host used for authentication and upload. Login and long-term credential setup belong to the settings-and-modes sub-skill.
- `--workspace`, `--project`, and `--id` override the uploaded run's target workspace, project, and run id. If no run id is supplied, sync generates one.
- Multiple CLI paths are processed sequentially with the same settings.

### Record lifecycle and integrity behavior

SwanLab sync reads the local run record file and uploads metric/media/log/save records while using lifecycle records to determine the remote run state.

- A valid sync file begins with a start record. If the first record is missing or not a start record, sync fails before upload because the file is not a valid SwanLab run file.
- Start and finish lifecycle records are not uploaded as ordinary metric records. They are used to prepare and stop the remote run.
- Duplicate or too-old scalar/log steps can be skipped when the target remote run already has those entries or the local file repeats an older step.
- If a record checksum or payload is corrupted after some valid records, the reader stops at the last valid record. Earlier valid records can still upload, but do not claim the upload is complete unless the run file is known to be intact.
- If the run file has no finish record, sync synthesizes a crashed finish state, adds an error log explaining that the process was interrupted before writing a finish record, and reports the remote run as crashed. This is expected for killed or crashed training jobs.
- If the run file header version is older/incompatible, sync fails with a version message. Use a SwanLab SDK version compatible with the file to perform the upload instead of editing the record file by hand.
- Network or server failures can appear at start, flush, progress, confirm, or finish-report phases. Preserve the local run directory and retry after fixing credentials/host/connectivity; do not delete partial local logs.

## Live monkey-patch sync helpers

These helpers forward logging calls from another library into SwanLab while the source script is running. They are not the same as `swanlab.sync`, which uploads a completed local SwanLab run directory.

### W&B live sync

```python
import swanlab

swanlab.sync_wandb(
    mode="offline",      # online | local | offline | disabled
    wandb_run=False,     # force W&B itself offline while mirroring into SwanLab
    workspace="team",
    log_dir="swanlab-logs",
)

import wandb
wandb.init(project="demo", config={"lr": 0.01})
wandb.log({"loss": 0.5}, step=1)
wandb.finish()
```

Behavior to remember:

- Call before `wandb.init`.
- `wandb.init` initializes SwanLab if no run exists, otherwise it updates the active SwanLab config.
- `wandb.config.update` forwards dictionary and keyword updates into `swanlab.config.update`.
- `wandb.log` forwards scalar/bool/string values and W&B images or lists of W&B images that can be converted to `swanlab.Image`.
- `wandb.finish` calls `swanlab.finish` before the original W&B finish.

### TensorBoard live sync

```python
import swanlab

swanlab.sync_tensorboardX(types=["scalar", "scalars", "text"])
# or: swanlab.sync_tensorboard_torch(types=["scalar", "image"])

from tensorboardX import SummaryWriter
writer = SummaryWriter(log_dir="runs/tb")
writer.add_scalar("loss", 0.5, 1)
writer.close()
```

Behavior to remember:

- Call before creating the `SummaryWriter` instance.
- `sync_tensorboardX` patches `tensorboardX.SummaryWriter`; `sync_tensorboard_torch` patches `torch.utils.tensorboard.SummaryWriter`.
- Supported live-sync type filters are `scalar`, `scalars`, `image`, and `text`. `None` syncs all patched types.
- Writer initialization stores the TensorBoard log directory in SwanLab config as `tensorboard_logdir`.
- Writer close calls `swanlab.finish` after closing the original writer.

### MLflow live sync

```python
import swanlab

swanlab.sync_mlflow(mode="offline")

import mlflow
mlflow.set_experiment("demo")
with mlflow.start_run(run_name="trial-1"):
    mlflow.log_param("lr", 0.01)
    mlflow.log_metric("loss", 0.5, step=1)
mlflow.end_run()
```

Behavior to remember:

- Call before MLflow experiment, start-run, and logging calls.
- `set_experiment(experiment_name=...)` stores the SwanLab project name for the next run. Passing only an experiment id does not provide a project name.
- `start_run(run_name=...)` initializes SwanLab if no run exists, using the project name saved by `set_experiment` and the MLflow run name.
- `log_param` / `log_params` update SwanLab config. `log_metric` / `log_metrics` forward metrics to `swanlab.log` with the MLflow step.
- `end_run` calls `swanlab.finish`.

## Batch converters

Batch converters read existing logs from another tracking system and create SwanLab runs from them. The converter classes accept common SwanLab run controls such as `project`, `workspace`, `mode`, `log_dir`, deprecated `logdir`, optional `tags`, and `resume` where applicable.

### TensorBoard file converter

```python
from swanlab.converter import TFBConverter

converter = TFBConverter(project="tb-import", mode="offline", types="scalar,image,text")
converter.run(convert_dir="runs/tensorboard", depth=3)
```

- Searches under `convert_dir` up to `depth` directory levels for file names containing `tfevents`.
- Supported converter types are `scalar`, `image`, `audio`, and `text`.
- If `types` is omitted in Python, all supported converter types are enabled. In the CLI, `--tb-types` defaults to `scalar`; pass a comma-separated list to include rich data.
- Each TFEvent file becomes a SwanLab run named from the relative directory and file name; the source TFEvent path is recorded in run config.
- No TFEvent file found raises a file-not-found error.

CLI examples:

```bash
swanlab convert --type tensorboard --tb-log-dir runs/tensorboard --tb-types scalar,image,text --project tb-import --mode offline
# Deprecated but still accepted: --tb-logdir; prefer --tb-log-dir.
```

### W&B cloud converter

```python
from swanlab.converter import WandbConverter

converter = WandbConverter(project="wandb-import", mode="offline")
converter.run(wb_project="source-project", wb_entity="source-team", wb_run_id=None)
```

- Requires both W&B project and W&B entity. The optional W&B run id narrows conversion to one run.
- Reads W&B run metadata, config, tags, group, job type, notes, and history rows.
- Skips W&B history keys that start with `_`, `None` values, and dictionary-valued history entries.
- If `resume=True`, pass a single `wb_run_id` so the source run id can be used as the SwanLab target id.

CLI example:

```bash
swanlab convert --type wandb --wb-project source-project --wb-entity source-team --wb-runid abc123 --resume --project wandb-import --mode offline
```

### W&B local converter

```python
from swanlab.converter import WandbLocalConverter

converter = WandbLocalConverter(project="wandb-local-import", mode="offline")
converter.run(root_wandb_dir="wandb", wandb_run_dir="offline-run-20250101_120000-abc123")
```

- `root_wandb_dir` is the W&B root directory, commonly named `wandb`.
- If `wandb_run_dir` is omitted, it searches for `run-*` and `offline-run-*` children.
- Each selected run directory must contain a `.wandb` file. Missing `.wandb` fails that run.
- Media/table file references inside W&B records are resolved relative to the run's `files` directory with a traversal guard; paths outside that directory are ignored.
- Table conversion needs pyecharts support; image and audio conversion also require the corresponding SwanLab media dependencies.

CLI example:

```bash
swanlab convert --type wandb-local --wb-dir wandb --wb-run-dir offline-run-20250101_120000-abc123 --project wandb-local-import --mode offline
```

### MLflow converter

```python
from swanlab.converter import MLFlowConverter

converter = MLFlowConverter(project="mlflow-import", mode="offline")
converter.run(tracking_uri="http://127.0.0.1:5000", experiment="demo", run_id=None)
```

- `experiment` can be an MLflow experiment id or name.
- `run_id` narrows conversion to one run inside the experiment.
- Converts MLflow params, non-MLflow-prefixed tags, run name/description, and full metric histories.
- Missing experiment or run id raises a value error.

CLI example:

```bash
swanlab convert --type mlflow --mlflow-url http://127.0.0.1:5000 --mlflow-exp demo --mlflow-runid abc123 --project mlflow-import --mode offline
```

## Path-selection checklist

Before giving a command, identify the source path type:

1. **SwanLab sync**: pass a SwanLab run directory containing the local SwanLab record file. Use `swanlab sync`, not `swanlab convert`.
2. **TensorBoard conversion**: pass the root directory that contains or recursively contains `tfevents` files. Use `--tb-log-dir` / `TFBConverter.run(convert_dir=...)`.
3. **W&B cloud conversion**: pass no local path; provide W&B entity/project and optional run id.
4. **W&B local conversion**: pass the W&B root directory to `--wb-dir` / `root_wandb_dir`, and optionally a child run directory name to `--wb-run-dir` / `wandb_run_dir`.
5. **MLflow conversion**: pass a tracking URI and experiment id/name, not a local SwanLab run directory.

If the path type is unclear, ask the user what produced the directory and whether it contains SwanLab `run-*.swanlab`, TensorBoard `tfevents`, W&B `.wandb`, or MLflow experiment metadata.
