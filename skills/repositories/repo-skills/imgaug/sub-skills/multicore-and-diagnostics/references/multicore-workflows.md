# Multicore workflows

## Read this when

You need to run imgaug augmentation in background workers or explicit pools.

## Simple background generator

```python
import imgaug.augmenters as iaa
from imgaug.augmentables.batches import UnnormalizedBatch

seq = iaa.Sequential([iaa.Fliplr(0.5), iaa.CoarseDropout(p=0.1, size_percent=0.1)])
batches = [UnnormalizedBatch(images=images)]
for batch_aug in seq.augment_batches(batches, background=True):
    use(batch_aug.images_aug)
```

Use this form when the default background configuration is enough and the caller consumes the generator to completion.

## Explicit pool

```python
with seq.pool(processes=-1, seed=1) as pool:
    for batch_aug in pool.imap_batches(batches, chunksize=1):
        use(batch_aug.images_aug)
```

`processes=None` uses available CPU cores. A negative value reserves cores, e.g. `processes=-1` uses all but one when CPU count is available.

## BatchLoader and BackgroundAugmenter

```python
import imgaug.multicore as multicore

loader = multicore.BatchLoader(load_batches, queue_size=4)
background = multicore.BackgroundAugmenter(loader, seq, queue_size=4)
while True:
    batch = background.get_batch()
    if batch is None:
        break
    use(batch.images_aug)
```

Use this only when you need explicit control over loading and augmentation queues. Keep queues small until throughput and memory use are proven.

## Verified APIs

- `Augmenter.augment_batches(batches, hooks=None, background=False)`
- `Augmenter.pool(processes=None, maxtasksperchild=None, seed=None)`
- `Pool.map_batches(batches, chunksize=None)`
- `Pool.imap_batches(batches, chunksize=1, output_buffer_size=None)`
- `BatchLoader(load_batch_func, queue_size=50, nb_workers=1, threaded=True)`
- `BackgroundAugmenter(batch_loader, augseq, queue_size=50, nb_workers='auto')`
- `BackgroundAugmenter.get_batch()`

## Safety checklist

- Use tiny synthetic batches first.
- Avoid GUI display in background workers.
- Make custom functions top-level and picklable.
- Preserve `Batch.data` IDs when output order matters.
- Consume generators fully or ensure workers are cleaned up.
- Do not nest `Pool` inside a worker process.
