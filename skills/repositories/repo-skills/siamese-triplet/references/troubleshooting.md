# Troubleshooting

## `AttributeError: train_data` or `train_labels`

The wrappers were written for an older torchvision API. If your dataset only exposes `data` and `targets`, add a compatibility object with the legacy attributes or adapt the dataset before wrapping it.

## `Image.fromarray` or transform errors

`SiameseMNIST` and `TripletMNIST` convert their tensors to grayscale PIL images. If your fake fixture is not `uint8` or not 2D, image conversion can fail. Use a `torch.uint8` tensor shaped like `(N, 28, 28)` for the bundled smokes.

## Balanced batch sampler yields short batches

`BalancedBatchSampler` expects enough examples per class for the chosen `n_classes × n_samples` configuration. If your labels are too sparse, reduce the batch shape or rebalance the dataset.

## Pair or triplet selectors return empty results

The online mining losses need multiple samples per class inside the mini-batch. If a batch contains only singletons, the selectors can return no useful pairs or triplets.

## `OnlineTripletLoss` metric mismatch

`OnlineTripletLoss` returns `(loss, num_triplets)`. The `AverageNonzeroTripletsMetric` reads the second tuple element. If you swap in a custom online loss, keep that return shape or update the metric.

## Scheduler warning in modern PyTorch

The repo's `fit` function calls `scheduler.step()` before the epoch's optimizer steps, which triggers a warning in modern PyTorch releases. The bundled smoke accepts that warning because it does not affect the verification goal here.

## Dataset downloads are slow or unavailable

The notebooks download MNIST and FashionMNIST. The generated skill's smoke scripts avoid network access by using tiny synthetic fixtures instead.

## GPU is visible but not needed

The skill is CPU-first and uses CUDA only for an optional smoke check. A visible GPU does not imply the notebooks must be run on GPU.
