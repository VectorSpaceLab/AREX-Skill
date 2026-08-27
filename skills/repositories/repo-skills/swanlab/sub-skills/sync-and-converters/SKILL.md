---
name: sync-and-converters
description: "Guide SwanLab local sync, offline run validation, crash-tolerant
  upload behavior, and TensorBoard/W&B/MLflow conversion."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# SwanLab sync and converters

Use this sub-skill when the task is about uploading an existing SwanLab local/offline run, validating a run directory before upload, interpreting incomplete or legacy local records, or converting/synchronizing logs from TensorBoard, Weights & Biases, or MLflow into SwanLab.

## Route here for

- `swanlab.sync(...)` or the `swanlab sync` CLI.
- Checking whether a local/offline run directory is readable and structurally plausible before cloud sync.
- Explaining corrupted-record, missing-finish, crash-marked, duplicate-step, or old run-file-version behavior during sync.
- Choosing among `sync_wandb`, `sync_tensorboardX`, `sync_tensorboard_torch`, `sync_mlflow`, `WandbConverter`, `WandbLocalConverter`, `TFBConverter`, `MLFlowConverter`, and the `swanlab convert` CLI.
- Troubleshooting converter optional dependencies, monkey-patch ordering, source path confusion, or upload failures.

## Route elsewhere

- Creating the original SwanLab training run, logging scalars/config, or using `finish`: use the experiment-tracking sub-skill.
- Login, API-key storage, default mode selection, and host configuration: use the settings-and-modes sub-skill.
- Fetching/exporting cloud metadata with `swanlab.Api` or `swanlab api`: use the open-api-and-cli sub-skill.
- Media object constructors and rich chart object details: use the media-and-custom-charts sub-skill.

## Operating references

1. Read [references/sync-and-conversion.md](references/sync-and-conversion.md) for the sync/converter decision matrix, API and CLI shapes, local run expectations, and conversion path checklist.
2. Read [references/troubleshooting.md](references/troubleshooting.md) when a user reports authentication, run-directory, record-integrity, old-version, optional-dependency, path-selection, or network upload failures.
3. Use [scripts/check_sync_guards.py](scripts/check_sync_guards.py) for no-network parser and path-guard assertions before trusting advice that depends on local sync/converter surfaces.

## Safety defaults

- Do not start a network upload unless the user explicitly asks to sync and has provided or confirmed credentials/host context.
- Validate the directory first; for sync, the target is the run directory containing the SwanLab run record file, not a TensorBoard log root, W&B root, or MLflow tracking URI.
- Treat missing finish records as a crash-tolerant sync case, not as proof that all metrics are complete.
- Treat converter dependencies as optional until the selected converter path requires them.
