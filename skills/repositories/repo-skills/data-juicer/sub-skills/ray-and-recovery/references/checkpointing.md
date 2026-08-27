# Checkpointing and recovery

## Key settings
- `work_dir`: the root directory for the run state.
- `checkpoint_dir`: where checkpoint files are written.
- `event_log_dir`: where Ray / job events are stored if enabled.
- `job_id`: stable identity for the run.
- `resume`: tells the executor to continue from prior state when possible.
- `partition.*`: partition size and partition mode controls.

## Recovery rules
- Reuse the same work directory when you expect recovery to find prior state.
- Do not change the partition layout unless you are intentionally starting a new run.
- If resume fails, check whether the new config is compatible with the saved checkpoint.
- Keep checkpoint storage on a path that all workers can see.

## What to verify
- The checkpoint path exists and is writable.
- The event log path matches the expected run.
- The resume token or job ID refers to the same logical job.
- The partition count still matches the dataset and executor shape.

## When recovery is not safe
Start a new run instead of resuming if:
- the dataset changed materially
- the process list changed in a way that invalidates prior state
- the partition strategy changed
- the saved state is missing or partially corrupted
