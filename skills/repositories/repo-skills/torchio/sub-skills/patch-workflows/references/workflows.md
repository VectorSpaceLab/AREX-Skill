# Patch Workflow Recipes

## Training with Queue and Random Samplers

Use `Queue` when training from many subjects, especially if loading, transforms, or random patch extraction are expensive.

```python
import torchio as tio

subjects = [
    tio.Subject(
        t1=tio.ScalarImage(t1_tensor),
        seg=tio.LabelMap(seg_tensor),
    )
    for t1_tensor, seg_tensor in training_tensors
]

sampler = tio.LabelSampler(
    subjects[0],
    patch_size=(64, 64, 64),
    label_name="seg",
    label_probabilities={0: 0.1, 1: 1.0},
)
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
    logits = model(inputs)
    loss = criterion(logits, targets)
    loss.backward()
```

Checklist:

- The sampler object needs an example subject at construction, but `Queue` calls it on each queued subject.
- Keep `patch_size` smaller than or equal to the usable spatial shape on all axes.
- Size `max_length` as a RAM budget: roughly `4 bytes * channels * patch_voxels * max_length` for float32 image data.
- Use `patches_per_epoch` to set progress bars or training-step expectations.
- Use `subject_sampler` with `shuffle_subjects=False` for distributed or custom subject partitioning.

## Direct Random Patch Loader

For small experiments or single subjects, random samplers can be used directly with `SubjectsLoader`.

```python
sampler = tio.UniformSampler(subject, patch_size=(48, 48, 48), num_patches=200)
loader = tio.SubjectsLoader(sampler, batch_size=8)

for batch in loader:
    assert batch.t1.data.ndim == 5
    logits = model(batch.t1.data)
```

This avoids a queue but does not buffer across subjects. Use `WeightedSampler` or `LabelSampler` instead of `UniformSampler` when a probability map or labels should bias patch centers.

## Dense Inference with GridSampler and PatchAggregator

Use `GridSampler` when every voxel in a volume must receive an output.

```python
import torch
import torchio as tio

patch_size = (64, 64, 64)
patch_overlap = (16, 16, 16)

sampler = tio.GridSampler(
    subject,
    patch_size=patch_size,
    patch_overlap=patch_overlap,
    padding_mode="constant",
)
loader = tio.SubjectsLoader(sampler, batch_size=4)
aggregator = tio.PatchAggregator(
    spatial_shape=sampler.subject.spatial_shape,
    overlap_mode="hann",
    patch_overlap=patch_overlap,
)

model.eval()
with torch.no_grad():
    for batch in loader:
        inputs = batch.t1.data
        outputs = model(inputs)
        locations = batch.metadata["patch_location"]
        aggregator.add_batch(outputs, locations)

prediction = aggregator.get_output()
```

Notes:

- `padding_mode` pads by half of `patch_overlap`; if you pass padding to `GridSampler`, use `sampler.subject.spatial_shape` for aggregation over the padded sampling domain.
- For non-padded inference, `subject.spatial_shape` and `sampler.subject.spatial_shape` are the same.
- `PatchAggregator.add_batch()` moves tensors to CPU internally, so keep GPU memory bounded by sending only patch batches through the model.
- `prediction` is 4D `(C_out, I, J, K)`.

## PatchLocation Handling

`PatchLocation` stores the corner index and size in the input volume coordinate frame.

```python
location = batch.metadata["patch_location"][0]
start = location.index_ini
stop = location.index_fin
spatial_slices = location.to_slices()
```

When manually aggregating, pass exactly one `PatchLocation` per batch item. If a model filters or reorders a batch, filter or reorder `locations` the same way.

## Dense Inference with Multiple Outputs

Use dictionary aggregation when a model returns multiple dense tensors.

```python
aggregator = tio.PatchAggregator(
    spatial_shape=subject.spatial_shape,
    overlap_mode="average",
)

for batch in loader:
    outputs = model(batch.t1.data)
    aggregator.add_batch(
        {
            "segmentation": outputs["segmentation"],
            "embedding": outputs["embedding"],
        },
        batch.metadata["patch_location"],
    )

segmentation = aggregator.get_output("segmentation")
embedding = aggregator.get_output("embedding")
```

Each tensor must be 5D and share the same batch dimension as the locations list. Channel counts may differ per key.

## Downsampled Model Outputs

If the model output has a smaller spatial grid than the input image, tell the aggregator the full output shape.

```python
aggregator = tio.PatchAggregator(
    spatial_shape=subject.spatial_shape,
    output_shape=(128, 128, 88),
    overlap_mode="average",
)
```

The aggregator scales `PatchLocation` indices and sizes to the output grid. This is appropriate for strided encoders or feature maps. The per-patch output spatial shape should match the scaled patch size.

## Choosing Probability Maps

For `WeightedSampler`, add a scalar image to the subject and pass its name:

```python
weights = torch.zeros(1, *subject.spatial_shape)
weights[:, 20:80, 20:80, 20:80] = 1
subject = tio.Subject(
    t1=subject.t1,
    sampling_weights=tio.ScalarImage(weights),
)
sampler = tio.WeightedSampler(
    subject,
    patch_size=(32, 32, 32),
    probability_map="sampling_weights",
    num_patches=100,
)
```

For labels, prefer `LabelSampler`:

```python
sampler = tio.LabelSampler(
    subject,
    patch_size=(32, 32, 32),
    label_name="seg",
    label_probabilities={1: 1.0, 2: 3.0},
    num_patches=100,
)
```

Borders where a patch center cannot produce a valid patch are masked internally. If all remaining probabilities are zero, sampling raises a runtime error.
