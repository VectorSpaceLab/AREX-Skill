---
name: multicore-and-diagnostics
description: "Use when running imgaug batches in background processes or
  threads, tuning Pool/queue behavior, or diagnosing slow and hanging
  augmentation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Multicore and Diagnostics

Use this sub-skill for imgaug's CPU parallelism and diagnostic surfaces: `augment_batches(..., background=True)`, `Augmenter.pool()`, `imgaug.multicore.Pool`, `BatchLoader`, `BackgroundAugmenter`, safe smoke checks, and performance/hang triage.

## What this sub-skill covers

- Batch-oriented background augmentation.
- Process pools, `map_batches`, `imap_batches`, `chunksize`, `processes`, `seed`, and `maxtasksperchild`.
- `BatchLoader` and `BackgroundAugmenter` queue/worker configuration.
- Pickling and platform start-method caveats.
- Small, deterministic diagnostics that do not open GUI windows or run huge loops.

## What it does not cover

- Core augmenter composition belongs to [`../augmentation-pipelines/SKILL.md`](../augmentation-pipelines/SKILL.md).
- Detailed annotation object and batch data layouts belong to [`../augmentables-and-batches/SKILL.md`](../augmentables-and-batches/SKILL.md).
- RNG/distribution internals belong to [`../parameters-random-and-utilities/SKILL.md`](../parameters-random-and-utilities/SKILL.md).

## Typical triggers

- “How do I augment batches in the background?”
- “Use all CPUs except one for imgaug.”
- “Why does `BackgroundAugmenter` hang?”
- “What should `chunksize` or queue size be?”
- “Prove the multiprocessing path with a tiny fixture before scaling up.”

## Fast path

1. Read [`references/multicore-workflows.md`](references/multicore-workflows.md) for API patterns and safe defaults.
2. Read [`references/diagnostics-and-performance.md`](references/diagnostics-and-performance.md) before tuning worker counts or queues.
3. Run [`scripts/tiny_multicore_smoke.py`](scripts/tiny_multicore_smoke.py) before attempting a large workload.
4. Read [`references/troubleshooting.md`](references/troubleshooting.md) for hangs, pickling errors, platform issues, and queue exhaustion.

## Verified signatures

- `Augmenter.augment_batches(batches, hooks=None, background=False)`
- `Augmenter.pool(processes=None, maxtasksperchild=None, seed=None)`
- `imgaug.multicore.Pool(augseq, processes=None, maxtasksperchild=None, seed=None)`
- `Pool.map_batches(batches, chunksize=None)`
- `Pool.imap_batches(batches, chunksize=1, output_buffer_size=None)`
- `BatchLoader(load_batch_func, queue_size=50, nb_workers=1, threaded=True)`
- `BackgroundAugmenter(batch_loader, augseq, queue_size=50, nb_workers='auto')`
- `BackgroundAugmenter.get_batch()`

## Safe starting pattern

```python
from imgaug.augmentables.batches import UnnormalizedBatch
import imgaug.augmenters as iaa

seq = iaa.Sequential([iaa.Fliplr(0.5), iaa.GaussianBlur((0.0, 1.0))])
batches_aug = seq.augment_batches(batches, background=True)
for batch in batches_aug:
    consume(batch)
```

For explicit process control:

```python
with seq.pool(processes=-1, seed=1) as pool:
    batches_aug = pool.imap_batches(batches, chunksize=1)
    for batch in batches_aug:
        consume(batch)
```

Negative `processes` reserves that many logical cores when possible; `-1` means all but one. Start with a tiny batch list and scale only after the smoke passes.

## Diagnostic order

1. Run the root environment check.
2. Run the tiny multicore smoke with one or two batches.
3. Replace custom lambdas/callbacks with top-level picklable functions.
4. Reduce `processes`, queue sizes, and batch sizes.
5. Only then tune `chunksize`, `maxtasksperchild`, or background queue depth.
