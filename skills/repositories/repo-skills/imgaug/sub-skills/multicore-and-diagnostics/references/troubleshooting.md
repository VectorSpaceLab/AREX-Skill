# Multicore troubleshooting

## Background generator hangs

**Symptoms:** loop over `augment_batches(..., background=True)` stops producing batches.

**Likely causes:** worker exception, unconsumed generator cleanup, GUI call, non-picklable custom augmenter, or queue deadlock.

**Recovery:** run the tiny smoke helper, reduce to one worker/batch, remove GUI calls, and make custom functions importable top-level functions.

## Pool creation assertion

**Symptom:** error says a pool is being created inside another pool or `_WORKER_AUGSEQ` is already set.

**Recovery:** do not instantiate `imgaug.multicore.Pool` from inside an existing imgaug worker process.

## Process count surprises

**Symptom:** too many or too few workers start.

**Recovery:** remember that `processes=None` uses all available logical cores, while negative values reserve cores when CPU count is available. Use explicit small positive values during debugging.

## Pickling failures

**Symptom:** multiprocessing errors mention that a function, lambda, or object cannot be pickled.

**Recovery:** move custom image/keypoint/heatmap functions to module top level, avoid closures over large objects, and test with a simple built-in augmenter first.

## Memory blowup

**Symptom:** process memory rises quickly or the OS kills workers.

**Recovery:** shrink batch size, queue size, and `chunksize`; avoid preloading too many images; carry only IDs/metadata in `Batch.data`.

## Platform-specific hangs or process-loader seed errors

**Symptom:** behavior differs across Linux/macOS/Windows or a specific container, or process-backed `BatchLoader` fails before loading any batches with a seed-related `TypeError` from Python's `random.seed`.

**Recovery:** reproduce with the tiny smoke, then change process count/start-method context outside imgaug if needed. Prefer explicit `Pool` or threaded `BatchLoader` first; only use process-backed loading after a dedicated tiny check passes. If the smoke passes, scale one dimension at a time.
