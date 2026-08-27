# Augmentation and sampling API reference

`Transform` operates on `X` and optionally `y`; it should preserve the batch,
channel, time, label, dtype, and device contract unless the transform explicitly
documents otherwise. Set `probability` in `[0, 1]` and use a reproducible
`random_state` when comparing experiments. `Compose` applies transforms in
order.

`AugmentedDataLoader(dataset, transforms=..., batch_size=..., device=..., 
 n_augmentation=0, ...)` applies transforms to batches. With positive
`n_augmentation`, the first block is the clean batch and later blocks are
augmented copies; labels are tiled across all blocks. A negative value is
invalid.

Sampler APIs under `braindecode.samplers` include `SequenceSampler`,
`RelativePositioningSampler`, and self-supervised samplers. Their required
trial/window metadata and index semantics differ; inspect the sampler's
signature and enumerate a tiny output before training.
