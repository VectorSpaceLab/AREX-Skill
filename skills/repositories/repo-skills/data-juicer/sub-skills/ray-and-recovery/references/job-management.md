# Job management

## Use the helpers
- snapshot: inspect saved run state
- monitor: follow progress and completion
- stopper: stop a running job cleanly

## Practical loop
1. Start the Ray job.
2. Check the snapshot or monitor output.
3. Stop the job if the state is clearly wrong.
4. Re-run with the same identity only after you understand the failure.

## Useful questions to answer
- Is the job still running, finished, or stalled?
- Which partition or worker failed first?
- Is the issue in the data, the executor, or the storage path?

## Operational tips
- Prefer explicit work directories.
- Keep the job ID stable across a recovery attempt.
- Use the monitor before trying to infer state from logs alone.
