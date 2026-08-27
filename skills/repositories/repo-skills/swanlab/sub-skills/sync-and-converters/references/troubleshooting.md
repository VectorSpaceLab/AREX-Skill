# Sync and converter troubleshooting

Use this when a sync or conversion task fails or the user is unsure which path to pass to SwanLab.

## First triage questions

1. Is the user trying to upload an existing SwanLab run directory, convert logs from another tool, or mirror another tool while training is still running?
2. What kind of source artifact do they have?
   - SwanLab local run record file in a run directory.
   - TensorBoard `tfevents` files.
   - W&B cloud project/entity/run id.
   - Local W&B `run-*` or `offline-run-*` directory containing a `.wandb` file.
   - MLflow tracking URI plus experiment id/name.
3. Do they expect network access now? If not, prefer validation, disabled/offline examples, or converter planning rather than `swanlab sync` upload.
4. Are credentials and host settings already configured? If the question is about setup or persistent storage of credentials, route to settings-and-modes.

## Common failures

| Symptom | Likely cause | Fix |
|---|---|---|
| Authentication error saying to login first or call `swanlab.login()` | No active SwanLab client and no API key was supplied to sync | Use `swanlab login`, pass `Settings(api_key=...)`, or use CLI `--api-key`. Confirm host/workspace/project separately. |
| CLI rejects `RUN_DIR` before sync starts | Path does not exist, is a file, is unreadable, or is not a directory | Pass the actual SwanLab run directory; check permissions; run `scripts/check_sync_guards.py --check-run-dir RUN_DIR` before upload. |
| Programmatic sync raises a validation error for `run_dir` | `run_dir` is missing or not a directory | Use the directory containing the SwanLab run record file, not the record file itself. |
| Programmatic sync raises a permission error | Directory exists but is not readable by the process | Fix filesystem permissions or copy the run directory to a readable location. |
| Sync fails because the first record is missing or not a start record | The file is not a valid SwanLab run record file, or it is severely truncated/corrupted | Do not hand-edit the file; recover from a backup or rerun the experiment. If the source is TensorBoard/W&B/MLflow, use a converter instead of `swanlab sync`. |
| Sync uploads only records before a corrupt point | Record checksum/payload corruption caused the reader to stop at the last valid record | Treat the upload as partial. Preserve the directory, inspect whether the training process or storage layer corrupted the file, and retry only after restoring a valid copy. |
| Remote synced run is marked crashed with an error log about no finish record | Training was killed or interrupted before SwanLab wrote a finish record | This is expected crash-tolerant behavior. Metrics before the interruption can still sync, but the final state is `crashed`. |
| Sync fails with an invalid run version message | The local run file was created by an incompatible SwanLab SDK record format | Use a SwanLab SDK version compatible with that run file to sync it. Do not rewrite the binary record header manually. |
| Duplicate or old metric steps appear to be skipped | Sync is resuming against an existing remote run summary or the local file has repeated/older steps | This is expected de-duplication. Use a new run id if the intent is to upload every record as a fresh run. |
| Start/finish records do not appear as uploaded metrics | Lifecycle records are used internally to prepare/finish the remote run | Not a bug; check the remote run state and uploaded metric/log records instead. |
| Start or flush stage raises a runtime error | Backend rejected run preparation, credentials/host/workspace/project are wrong, or server/network failed | Verify API host and credentials; retry after network/server recovery. Keep the local run directory intact. |
| Confirm/finish stage reports failure after upload | Upload finished but final stop/finish report failed | Check the cloud run and retry if final state is wrong. The local directory remains the source of truth for a repeat attempt. |

## Optional dependency failures

SwanLab core can be installed without every converter source dependency. Missing converter packages usually appear only when the selected converter or monkey-patch touches that dependency.

| Selected path | Common missing package | Typical fix |
|---|---|---|
| `sync_wandb`, `WandbConverter`, `WandbLocalConverter` | `wandb` | Install W&B in the same Python environment. |
| W&B image/table/media conversion | `numpy`, Pillow/media support, pyecharts | Install SwanLab media dependencies and media/table dependencies needed by the data being converted. |
| `sync_tensorboardX` | `tensorboardX` | Install `tensorboardX`. |
| `sync_tensorboard_torch` | `torch` and TensorBoard support | Install PyTorch with TensorBoard support for the target environment. |
| `TFBConverter` | `tensorboard`, media dependencies for image/audio/text extraction | Install TensorBoard and any rich media dependencies required by the TFEvent contents. |
| `sync_mlflow`, `MLFlowConverter` | `mlflow` | Install MLflow and ensure the tracking URI is reachable. |

When optional imports fail, explain the selected converter path first; do not ask users to install all optional frameworks if they only need one converter.

## Path confusion fixes

- **SwanLab run directory vs record file**: `swanlab sync` takes the directory, not the `run-*.swanlab` file path.
- **SwanLab run directory vs parent log root**: if a log root contains many run directories, pass each run directory explicitly. The CLI can accept multiple directories.
- **TensorBoard vs SwanLab**: TensorBoard conversion needs a directory containing `tfevents` files. A SwanLab run directory should use `swanlab sync` instead.
- **W&B cloud vs W&B local**: W&B cloud conversion needs `--wb-project` and `--wb-entity`; W&B local conversion needs `--wb-dir` and optionally `--wb-run-dir`.
- **W&B local root vs child run**: `--wb-dir` should usually be the `wandb` root; `--wb-run-dir` should be only a selected child directory name if narrowing to one run.
- **MLflow path vs URI**: MLflow conversion takes a tracking URI and experiment id/name. A filesystem path is valid only if it is a valid MLflow tracking URI for that MLflow setup.
- **TensorBoard live sync vs file conversion**: `sync_tensorboardX` and `sync_tensorboard_torch` patch a running script. `TFBConverter` reads existing files after they were written.

## Monkey-patch ordering problems

| Symptom | Cause | Fix |
|---|---|---|
| W&B calls are not mirrored | `sync_wandb` was called after `wandb.init` or after methods were already captured | Call `swanlab.sync_wandb(...)` before the W&B run starts. |
| TensorBoard writer logs are not mirrored | Patch was called after a writer instance was created | Call `sync_tensorboardX` or `sync_tensorboard_torch` before creating `SummaryWriter`. |
| MLflow run has no SwanLab project name | `mlflow.set_experiment` was called with only an experiment id, or `sync_mlflow` was called too late | Call `sync_mlflow` first and provide an experiment name if you want it to become the SwanLab project. |
| `swanlab.finish` happens earlier than expected | Patched `wandb.finish`, TensorBoard writer close, or `mlflow.end_run` calls finish the SwanLab run | If the source framework closes multiple runs/writers, use explicit SwanLab run lifecycle planning in the main experiment-tracking sub-skill. |

## Converter-specific notes

### TensorBoard

- Python `TFBConverter(types=None)` converts all supported types; CLI `--tb-types` defaults to `scalar`. If images/text/audio are missing from a CLI import, rerun with `--tb-types scalar,image,text,audio`.
- Live TensorBoard sync type filters include `scalars` for grouped scalar logging; file conversion type filters do not use `scalars`.
- A `FileNotFoundError` for no TFEvent files usually means the wrong directory or too shallow a search depth.

### W&B

- Cloud W&B conversion requires both project and entity. If only project is supplied, the converter will still fail when entity is missing.
- `--resume` requires a single `--wb-runid`; otherwise the CLI rejects it.
- Local W&B conversion expects a `.wandb` file inside each selected run directory. No `.wandb` file means that selected run cannot be converted.
- Media paths are guarded against directory traversal. If W&B media/table objects are skipped, confirm the referenced files exist under the run's `files` directory and optional media dependencies are installed.
- Dictionary-valued W&B history items are skipped by the cloud converter. If the user needs rich objects, prefer local conversion when the files are available or log equivalent media through SwanLab directly.

### MLflow

- `experiment` can be an id or name. If an id lookup fails, the converter tries name lookup; if both fail, it raises a missing experiment error.
- `run_id` filters within the selected experiment. A missing run id error means the experiment was found but not that run.
- MLflow metric histories are logged per key with their original steps; params and non-MLflow-prefixed tags become SwanLab config.

## Network upload failures

For actual `swanlab.sync` or batch converters that create SwanLab runs:

1. Preserve the source directory/logs. Do not delete local/offline runs after a partial or failed upload.
2. Distinguish credentials/host failures from record-integrity failures. Credential/host failures are retriable after configuration changes; corrupt or incompatible record files require restoration or matching SDK versions.
3. If retrying against the same target run id, expect duplicate-step de-duplication. Use a new run id when the desired result is a separate fresh remote run.
4. For self-hosted or custom hosts, verify API host and web host configuration in settings-and-modes before blaming converters.
5. If the failure happens only during the final finish report, inspect the remote run: data may have uploaded even if the final state did not update.
