# Distributed Classical Training

AgileRL includes distributed training demos and Accelerate config examples. Treat distributed mode as an execution concern layered on top of validated single-process training.

## Before Launching Distributed Runs

- Prove the same algorithm/env/config works in a tiny single-process smoke run.
- Verify `accelerate` is installed and the config matches the host hardware.
- Keep environment creation inside a guarded entry point: `if __name__ == "__main__":`.
- Confirm W&B/logging behavior for multi-process jobs.
- Avoid benchmark-scale settings until process count, device assignment, and checkpoint paths are correct.

## Common Failure Modes

| Symptom | Recovery |
| --- | --- |
| Multiple processes each start full training unexpectedly | Check launch command, rank handling, and guarded main function. |
| CUDA device mismatch | Confirm visible devices and Accelerate config. Start with CPU or one GPU smoke runs. |
| W&B duplicate runs | Configure per-rank logging or log only from the main process. |
| Pickle/multiprocessing errors | Move env factories and training entry point to import-safe top-level functions. |

Use distributed scripts as templates, not as default validation commands.
