# Datasets and sampling troubleshooting

## Common symptoms and fixes

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| `The given path does not exist. You should probably initialize the dataset with download=True.` | The dataset root is missing and download is disabled | Create the root or set `download=True` the first time. |
| `Supported splits are: ...` | The split name is not one of the dataset's known splits | Use one of the documented splits. |
| A download takes a very long time | The benchmark dataset is large | Treat the download as optional, and use a smaller or already-cached dataset when smoke-testing. |
| `batch_size` / `m` assertions from `MPerClassSampler` | The batch constraints do not line up | Make `batch_size` a multiple of `m`, and make the batch large enough for the number of labels. |
| `HierarchicalSampler` assertions | The labels are not 2D or the batch geometry is inconsistent | Provide hierarchical labels and a compatible `batch_sampler` configuration. |
| `TuplesToWeightsSampler` runs out of memory | The subset is too large for offline mining | Reduce `subset_size` or choose a smaller evaluation subset. |
| Batch elements are not grouped the way the loss expects | The sampler is not aligned with the chosen loss/miner | Pick a sampler that produces the label structure the loss needs. |

## Recovery checklist

1. Confirm the dataset root and split before blaming the transform or DataLoader.
2. Start with `EmbeddingDataset` or a small toy dataset before downloading a benchmark.
3. Make sure the sampler matches the later loss/miner requirements.
4. If you need hierarchical batches, check that the label tensor shape is really 2D.
5. If you are sampling from mined tuples, keep the mining subset small enough to be safe.

## When to read the script

Run `scripts/smoke_data.py` to confirm the batch-composition rules on toy labels before you move to a full dataset download.
