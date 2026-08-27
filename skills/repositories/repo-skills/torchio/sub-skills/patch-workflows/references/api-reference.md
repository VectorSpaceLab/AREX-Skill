# Patch Workflow API Reference

## Objects and Responsibilities

| API | Use for | Key constructor arguments | Output or access pattern |
| --- | --- | --- | --- |
| `tio.GridSampler(subject, patch_size, patch_overlap=0, padding_mode=None, fill=0)` | Exhaustive, deterministic grid patches for dense inference | `subject`, 3D `patch_size`, even `patch_overlap`; optional padding by half-overlap | Map-style dataset; `len(sampler)` is number of patches; `sampler[i]` returns a patch `Subject` with `patch.patch_location` |
| `tio.UniformSampler(subject, patch_size, num_patches=None)` | Random spatially uniform training patches | `subject`, `patch_size`, optional finite `num_patches` | Iterable dataset; yields patch `Subject` instances |
| `tio.WeightedSampler(subject, patch_size, probability_map, num_patches=None)` | Random patches biased by a per-voxel weight image | `probability_map` is the subject image name containing weights | Iterable dataset; samples centers using nonzero weights after invalid borders are masked |
| `tio.LabelSampler(subject, patch_size, label_name, label_probabilities=None, num_patches=None)` | Random patches centered on labels, useful for class imbalance | `label_name` is the label image name; optional `{label_value: weight}` | Iterable dataset; defaults to all nonzero labels if probabilities are omitted |
| `tio.Queue(subjects, patch_sampler, max_length=300, patches_per_volume=10, num_workers=0, ...)` | Buffered patch training over many subjects | `subjects`, sampler, buffer size, patches per subject, worker threads, optional transform | Iterable dataset that yields individual patch `Subject` instances |
| `tio.SubjectsLoader(dataset, batch_size=...)` | Batch subjects or patches into `SubjectsBatch` | Any dataset yielding `Subject` instances | `batch.t1.data` is `(B, C, I, J, K)`; metadata lists are in `batch.metadata` |
| `tio.ImagesLoader(dataset, batch_size=...)` | Batch bare images into `ImagesBatch` | Dataset yielding `Image` instances | `batch.data` is `(B, C, I, J, K)` |
| `tio.PatchLocation(index, size, subject_index=None)` | Store a patch corner and spatial size | `index=(i, j, k)`, `size=(si, sj, sk)` | `index_ini`, `index_fin`, `to_slices()`, and `scaled(factor)` |
| `tio.PatchAggregator(spatial_shape, overlap_mode='crop', patch_overlap=0, output_shape=None)` | Reassemble patch outputs into a dense volume | Full output `spatial_shape`, overlap mode, optional output shape for downsampled predictions | `add_batch(outputs, locations)` then `get_output()` or `get_output(key)` |

## Tensor and Batch Shapes

- Image data is always channel-first 4D: `(C, I, J, K)`.
- A `SubjectsLoader` batch wraps named `ImagesBatch` objects with 5D tensors: `(B, C, I, J, K)`.
- Patch models should usually accept `batch.image_name.data` and return `(B, C_out, I_out, J_out, K_out)`.
- `PatchAggregator.get_output()` returns a 4D tensor `(C_out, I, J, K)`.
- If model outputs are spatially downsampled, set `output_shape` on `PatchAggregator`; patch locations are scaled automatically.

## Accessing Patch Locations

Individual patch subjects expose locations directly:

```python
patch = sampler[0]
location = patch.patch_location
```

Batched patches expose locations as metadata lists:

```python
for batch in tio.SubjectsLoader(sampler, batch_size=4):
    locations = batch.metadata["patch_location"]
    assert len(locations) == batch.batch_size
```

Use `locations` directly with `PatchAggregator.add_batch(outputs, locations)`. Avoid assuming a `batch.patch_location` attribute on `SubjectsBatch`; named images are attributes, metadata is not.

## Sampler Selection

- Choose `GridSampler` for complete volume coverage and deterministic dense inference.
- Choose `UniformSampler` when every valid patch location should be equally likely.
- Choose `WeightedSampler` when a subject contains a scalar probability/importance map such as `sampling_weights`.
- Choose `LabelSampler` when labels define regions of interest; use `label_probabilities` to oversample rare classes or suppress background.
- Put random samplers behind `Queue` when reading many subjects, applying transforms before sampling, or needing a shuffled patch buffer.

## Queue Knobs

- `max_length` caps the number of queued patches and controls memory use/diversity.
- `patches_per_volume` controls the maximum patches extracted from each subject per epoch pass.
- `num_workers` uses background threads to load and transform subjects before patch extraction.
- `shuffle_subjects=True` randomizes subject order unless `subject_sampler` is provided.
- `shuffle_patches=True` randomizes each drained buffer.
- `transform` is applied to each loaded subject before patches are sampled.
- `subject_sampler` supports distributed or custom subject partitioning; set `shuffle_subjects=False` when using it.
- `patches_per_epoch` is `num_subjects * patches_per_volume`.
- `max_memory_pretty` estimates patch-buffer memory from channel count, patch size, and `max_length`.

## Aggregator Overlap Modes

| `overlap_mode` | Best for | Notes |
| --- | --- | --- |
| `"crop"` | Discrete segmentation or argmax-style outputs | Crops overlapping margins and writes patch centers; pass the same `patch_overlap` used by `GridSampler` |
| `"average"` | Probability maps and logits | Sums overlaps and divides by counts |
| `"hann"` | Smooth continuous outputs | Uses Hann-window weighting to reduce seams |

`add_batch()` accepts either a single tensor or a dict of tensors:

```python
aggregator.add_batch(logits, locations)
aggregator.add_batch({"seg": seg_logits, "emb": embeddings}, locations)
seg = aggregator.get_output("seg")
emb = aggregator.get_output("emb")
```

## Valid In-Memory Synthetic Construction

Use direct tensor construction for tests and examples:

```python
image = tio.ScalarImage(torch.rand(1, 32, 32, 32))
label = tio.LabelMap(torch.zeros(1, 32, 32, 32, dtype=torch.long))
subject = tio.Subject(t1=image, seg=label)
```

Do not use `source=tensor`; the current API accepts the tensor as the first positional argument.
