# Diagnostics and performance

## Read this when

You need to debug a slow, hanging, or memory-hungry imgaug background augmentation workflow.

## Fast diagnosis order

1. Confirm the package imports from the intended environment with the root environment check.
2. Run the tiny multicore smoke helper with a tiny batch list.
3. Reduce `processes`, `queue_size`, and `chunksize`.
4. Replace lambdas and closures with top-level functions if pickling fails.
5. Only then scale batch counts or worker counts.

## Performance knobs

| Knob | Effect |
| --- | --- |
| `processes` | Number of worker processes; negative values reserve cores. |
| `maxtasksperchild` | Restart workers after a number of tasks to reduce long-run drift. |
| `chunksize` | More tasks per worker call can improve throughput. |
| `queue_size` | Larger queues can increase memory use. |
| `seed` | Stabilizes random behavior across workers. |

## Common platform caveats

- macOS and some Linux setups may require a different multiprocessing start method.
- NixOS and other unusual environments can show hangs that disappear when start methods change.
- GUI calls inside workers can cause blocking or process crashes.

## Safe smoke target

The bundled smoke script should prove that a tiny batch survives background augmentation and returns data without opening a GUI or looping for a long time.

## What not to do

- Do not use the full long-running source checks as a runtime dependency.
- Do not tune performance with a single giant batch when the issue may be pickling, queueing, or process startup overhead.
