---
name: patch-workflows
description: "Design TorchIO patch-based training queues and dense patch
  inference loops with samplers, SubjectsLoader batches, PatchLocation metadata,
  and PatchAggregator."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Patch Workflows

Use this sub-skill when an agent needs to train or infer on large 3D images by sampling patches instead of processing whole volumes. It covers `GridSampler`, `UniformSampler`, `WeightedSampler`, `LabelSampler`, `Queue`, `SubjectsLoader`, `ImagesLoader`, `PatchLocation`, and `PatchAggregator`.

## Route by Goal

- Need dense whole-volume inference: use `GridSampler` plus `PatchAggregator`; see [dense inference](references/workflows.md#dense-inference-with-grid-sampler-and-patchaggregator).
- Need stochastic training patches: use `UniformSampler`, `WeightedSampler`, or `LabelSampler`, optionally buffered by `Queue`; see [training queues](references/workflows.md#training-with-queue-and-random-samplers).
- Need to choose sampler or batch access patterns: see [API reference](references/api-reference.md).
- Hit shape, overlap, probability map, or metadata errors: see [troubleshooting](references/troubleshooting.md).
- Want a runnable synthetic sanity check: run `python scripts/patch_workflow_smoke.py --help`, then `python scripts/patch_workflow_smoke.py` from this sub-skill directory.

## Current API Reminders

- Construct in-memory images as `tio.ScalarImage(tensor)` and labels as `tio.LabelMap(tensor)`; do not use `source=tensor`.
- Image tensors are 4D `(C, I, J, K)` and loader batches are 5D `(B, C, I, J, K)`.
- `SubjectsLoader` returns a `SubjectsBatch`: named images are accessed as `batch.t1.data` or `batch["t1"].data`.
- Patch locations are stored on individual patch subjects as `patch.patch_location`; after batching, use `batch.metadata["patch_location"]`.
- `PatchAggregator.add_batch()` expects model outputs shaped `(B, C, I, J, K)` and a list of one `PatchLocation` per batch item.

## Minimal Dense Inference Pattern

```python
sampler = tio.GridSampler(subject, patch_size=(64, 64, 64), patch_overlap=16)
loader = tio.SubjectsLoader(sampler, batch_size=4)
aggregator = tio.PatchAggregator(
    spatial_shape=subject.spatial_shape,
    overlap_mode="hann",
    patch_overlap=16,
)

for batch in loader:
    logits = model(batch.t1.data)
    locations = batch.metadata["patch_location"]
    aggregator.add_batch(logits, locations)

volume_logits = aggregator.get_output()
```

## Minimal Training Queue Pattern

```python
sampler = tio.UniformSampler(subjects[0], patch_size=(64, 64, 64))
queue = tio.Queue(
    subjects,
    patch_sampler=sampler,
    max_length=300,
    patches_per_volume=10,
    num_workers=4,
    transform=train_transform,
)
loader = tio.SubjectsLoader(queue, batch_size=16)

for batch in loader:
    inputs = batch.t1.data
    targets = batch.seg.data
    loss = criterion(model(inputs), targets)
    loss.backward()
```

## Boundaries

- For creating `Subject`, `ScalarImage`, and `LabelMap` objects, use the parent data-model guidance.
- For choosing augmentations or preprocessing transforms, use the transforms sub-skill.
- For command-line operations, use the CLI and I/O sub-skill.
