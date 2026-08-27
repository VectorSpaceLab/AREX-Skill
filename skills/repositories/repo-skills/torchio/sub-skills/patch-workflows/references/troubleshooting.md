# Patch Workflow Troubleshooting

## `patch_size` or Spatial Shape Problems

Symptoms:

- Patches have unexpected shapes.
- Aggregated output has seams or missing regions.
- Random sampling repeatedly returns border-heavy patches.

Checks and fixes:

- Pass either an `int` or exactly three spatial integers: `patch_size=(I, J, K)`.
- Remember that images are `(C, I, J, K)`; do not include the channel dimension in `patch_size`.
- Keep `patch_size` no larger than the spatial shape when possible. If a grid patch is larger than an axis, the sampler clamps the start index but the resulting sliced patch cannot exceed the available volume extent.
- For dense inference, choose `patch_size` and `patch_overlap` together so `patch_size - patch_overlap` is the intended stride.
- If using `PatchAggregator(output_shape=...)`, ensure each model output patch spatial shape matches the scaled `PatchLocation.size`.

## Overlap and Aggregation Errors

Symptoms:

- `ValueError` mentioning `overlap_mode`.
- Output seams, cropped borders, or assignment shape mismatches.
- `RuntimeError` from tensor slice assignment inside aggregation.

Checks and fixes:

- Valid overlap modes are only `"crop"`, `"average"`, and `"hann"`.
- For `"crop"`, pass the same `patch_overlap` to `PatchAggregator` that was used by `GridSampler`.
- Use `"average"` for logits/probabilities and `"hann"` for smooth continuous outputs.
- `PatchAggregator.add_batch()` expects output tensors shaped `(B, C, I, J, K)`, not `(C, I, J, K)`; add a batch dimension for single patches.
- The number of locations must equal `B`. If you drop or reorder predictions, also drop or reorder `batch.metadata["patch_location"]`.
- If padding was enabled in `GridSampler`, aggregate over `sampler.subject.spatial_shape` unless you explicitly crop the final padded output afterward.

## Missing `patch_location`

Symptoms:

- `AttributeError: SubjectsBatch has no attribute 'patch_location'`.
- `KeyError: 'patch_location'` when aggregating.
- `PatchAggregator.add_batch()` receives locations that are tensors, tuples, or missing.

Checks and fixes:

- Individual sampled patch subjects expose `patch.patch_location`.
- Batched patches from `SubjectsLoader` store locations in `batch.metadata["patch_location"]`.
- Use `locations = batch.metadata["patch_location"]`, not `batch.patch_location`.
- Ensure the dataset passed to `SubjectsLoader` actually yields patches from a TorchIO sampler. Whole-subject datasets do not automatically have patch locations.
- Do not convert `SubjectsBatch` metadata to tensors before aggregation; `PatchAggregator` expects `PatchLocation` objects.

## Probability Map and Label Sampling Failures

Symptoms:

- `KeyError` for the probability map or label name.
- `RuntimeError` saying the probability map is all zeros.
- Sampler never returns foreground-looking patches.

Checks and fixes:

- `WeightedSampler(probability_map="name")` requires `subject.images["name"]` to exist.
- Probability maps should be single-channel or at least have useful weights in channel 0; TorchIO reads `prob_image.data[0]`.
- Values should be nonnegative and have a positive sum after invalid borders are masked.
- Labels near borders can be masked out if a patch centered there would exceed the image bounds; reduce `patch_size` or enlarge the valid labeled region.
- For `LabelSampler`, `label_probabilities=None` samples all nonzero labels. Provide `{label_value: weight}` to bias classes; labels not listed receive zero weight.

## Queue Worker and Performance Pitfalls

Symptoms:

- Training stalls before yielding a batch.
- RAM grows unexpectedly.
- Distributed training repeats or skips subject subsets.

Checks and fixes:

- `Queue.num_workers` controls background threads inside the queue, not PyTorch `DataLoader` worker processes. Start with queue `num_workers=0` for debugging.
- `max_length` is a patch-buffer capacity; increasing it improves shuffle diversity but increases RAM.
- `patches_per_volume` controls epoch length and subject balance. `queue.patches_per_epoch` is `queue.num_subjects * queue.patches_per_volume`.
- Avoid combining a large `max_length`, large 3D patches, many channels, and high loader worker counts without checking `queue.max_memory_pretty`.
- When using `subject_sampler`, set `shuffle_subjects=False`; TorchIO raises a `ValueError` otherwise.
- Apply transforms through `Queue(transform=...)` when transforms should happen before patch extraction.

## Batch Object Access

Symptoms:

- `TypeError` or `AttributeError` while reading a batch.
- A model receives 4D data when it expects 5D, or vice versa.

Checks and fixes:

- `SubjectsLoader` returns `SubjectsBatch`; access images as `batch.t1.data` or `batch["t1"].data`.
- `ImagesLoader` returns `ImagesBatch`; access tensor data as `batch.data`.
- `SubjectsBatch.metadata` stores lists of per-subject metadata values.
- `batch.batch_size` is the number of subjects/patches in the batch.
- `batch.to(device)` moves image tensors and affines; metadata objects such as `PatchLocation` remain Python objects.

## Memory and Large-Volume Limits

Symptoms:

- Whole-volume inference runs out of GPU memory.
- CPU RAM spikes during patch training.
- Patch inference is too slow on compressed images.

Checks and fixes:

- Reduce inference `batch_size` first; keep `patch_size` large enough for model context.
- Reduce `Queue.max_length` or `patches_per_volume` if CPU RAM is the bottleneck.
- Use lazy image slicing and patch workflows instead of materializing `image.data` for huge volumes before sampling.
- Prefer storage formats with efficient random access for repeated patch reads, such as uncompressed local NIfTI or chunked Zarr when available.
- Keep dense inference inside `torch.no_grad()` and move only patch batches through the model.
