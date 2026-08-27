# TensorBoard conversion and sync

Use this reference when the user has TensorBoard event logs, uses a TensorBoard callback, or wants old TensorBoard logs visible in Aim without rerunning training.

## Choose the right workflow

| User situation | Recommended Aim workflow | Why |
| --- | --- | --- |
| Existing TensorBoard log directory from a completed run | Offline conversion with `aim convert --repo <aim-repo> tensorboard --logdir <logdir>` | Reads event files once and creates Aim runs; no training rerun. |
| Existing logs were converted before and new event data was appended | Offline conversion again, using the default cache, or `--no-cache` only if reprocessing is intended | Conversion stores a cache in the Aim repo to avoid duplicate processing. |
| A training job is currently writing TensorBoard event files and the user wants live Aim updates | `aim.ext.tensorboard_tracker.Run(sync_tensorboard_log_dir=...)` in the same Python process | Starts a watcher resource that follows TensorBoard event folders. |
| User only wants future metrics and can edit training code | Framework callback or direct `Run.track` | Avoids TensorBoard parsing dependencies and event-file layout issues. |

## Offline conversion command

Use the group-level `--repo` option before the `tensorboard` subcommand:

```bash
aim convert --repo path/to/aim-repo tensorboard --logdir path/to/tensorboard-logdir
```

Optional flags:

```bash
# Flatten nested run grouping when converting event directory trees.
aim convert --repo path/to/aim-repo tensorboard --logdir path/to/tensorboard-logdir --flat

# Ignore the previous TensorBoard conversion cache and reprocess event files.
aim convert --repo path/to/aim-repo tensorboard --logdir path/to/tensorboard-logdir --no-cache
```

The converter scans for files whose names contain TensorBoard event-file markers, groups candidate run directories, creates or resumes Aim runs, stores `tensorboard_logdir` on the run, and tracks supported event values. Scalars and images are the primary supported plugin types; unsupported plugin types are skipped with a warning.

## Live sync template

Use live sync only when a process should watch a TensorBoard log directory as it changes. This starts a background tracker resource attached to an Aim run.

```python
from aim.ext.tensorboard_tracker import Run as AimTensorBoardRun

run = AimTensorBoardRun(
    sync_tensorboard_log_dir="path/to/tensorboard-logdir",
    repo="path/to/aim-repo",
    experiment="tensorboard_live_sync",
)
try:
    # Keep this process alive while the TensorBoard writer is producing events.
    # Put the user's existing training call here if they intentionally want live sync.
    pass
finally:
    run.close()
```

Do not add synthetic training just to use live sync. For completed logs, prefer offline conversion.

## Safe migration checklist

1. Confirm the log directory exists, is readable, and contains event files.
2. Confirm the target Aim repository path explicitly; do not rely on an arbitrary current working directory.
3. Check optional dependencies. Offline conversion requires TensorFlow import support and TensorBoard event utilities.
4. Decide whether to preserve conversion cache behavior. Use `--no-cache` only when the user wants reprocessing.
5. Run the conversion command, then use normal Aim UI/SDK workflows to inspect the imported runs.
6. If unsupported plugin warnings appear, list what was skipped and offer direct `Run.track` or a custom converter for those values.

## Bundled helper script

Print a safe command without executing it:

```bash
python scripts/tensorboard_sync_template.py --logdir path/to/tensorboard-logdir --repo path/to/aim-repo
```

Run dependency and logdir checks:

```bash
python scripts/tensorboard_sync_template.py --check-deps --logdir path/to/tensorboard-logdir --repo path/to/aim-repo
```

Execute conversion only when explicitly requested:

```bash
python scripts/tensorboard_sync_template.py --logdir path/to/tensorboard-logdir --repo path/to/aim-repo --execute
```

Print a live-sync Python template:

```bash
python scripts/tensorboard_sync_template.py --sync-template --logdir path/to/tensorboard-logdir --repo path/to/aim-repo
```

The helper validates paths and builds commands with explicit arguments so behavior does not depend on where it is launched.

## Troubleshooting conversion output

- `Could not process TensorBoard logs - failed to import tensorflow module.` means the converter could not import TensorFlow. Install/check TensorFlow in the environment used to run the conversion, or use a direct/custom importer.
- Warnings about unorganized event files mean the directory tree contains event files at levels the converter will ignore. Point `--logdir` at the parent that groups runs cleanly, or try `--flat` if the desired grouping is nested.
- Unsupported plugin warnings mean conversion skipped plugin types outside the converter's supported set. Preserve the original TensorBoard logs if a custom conversion is needed later.
- If re-running conversion does not import newly appended data, inspect cache behavior and consider `--no-cache` only after confirming duplicates are acceptable or the previous cache is stale.
