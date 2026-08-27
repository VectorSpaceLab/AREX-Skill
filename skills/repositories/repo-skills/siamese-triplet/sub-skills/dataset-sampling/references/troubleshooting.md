# Dataset-Sampling Troubleshooting

## Missing legacy attributes

The repository wrappers expect `train_data`, `train_labels`, `test_data`, and `test_labels`. Modern torchvision datasets usually expose `data` and `targets` instead. If you see `AttributeError`, provide a thin compatibility wrapper.

## PIL conversion fails

`Image.fromarray(..., mode='L')` expects a 2D grayscale array or tensor. If your fixture uses floats, RGB images, or a different shape, convert it to `uint8` grayscale first.

## `BalancedBatchSampler` yields too few indices

The sampler needs enough samples per class to satisfy `n_classes × n_samples`. Reduce the batch shape or rebalance the fixture.

## Deterministic test pairs and triplets look odd

That is expected. Test mode intentionally builds fixed pairs and triplets so evaluation can be repeatable.
