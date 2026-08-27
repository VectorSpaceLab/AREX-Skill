# Datasets and samplers

This reference covers the packaged benchmark datasets, the custom dataset extension pattern, and the bundled samplers that control batch composition.

## BaseDataset

```python
BaseDataset(
    root,
    split="train+test",
    transform=None,
    target_transform=None,
    download=False,
)
```

### Behavior

- `root` points to the dataset directory on disk.
- `download=True` creates the root directory when needed and downloads the dataset.
- `download=False` expects the root to exist already.
- `split` must be one of the supported split names.
- `transform` applies to the image or input.
- `target_transform` applies to the label.

### Required subclass methods

Custom datasets must implement:

- `download_and_remove()`
- `generate_split()`

The distilled extension pattern from `docs/extend/datasets.md` is:

1. subclass `BaseDataset`,
2. fetch or stage the raw files,
3. populate `self.paths` and `self.labels`,
4. let `__getitem__` return `(image, label)`.

### Supported splits

The built-in base class defaults to:

- `train`
- `test`
- `train+test`

## Packaged benchmark datasets

| Dataset | Typical split counts from the docs | Notes |
| --- | --- | --- |
| `CUB` | train 5864, test 5924, train+test 11788 | Fine-grained birds benchmark |
| `Cars196` | train 8054, test 8131, train+test 16185 | Fine-grained cars benchmark |
| `INaturalist2018` | train 325846, test 136093, train+test 461939 | Very large species dataset |
| `StanfordOnlineProducts` | train 59551, test 60502, train+test 120053 | Retrieval benchmark with large download |

### Common usage pattern

```python
from pytorch_metric_learning.datasets import CUB
train = CUB(root="data", split="train", download=True)
test = CUB(root="data", split="test", download=False)
```

## Samplers

### `MPerClassSampler`

```python
MPerClassSampler(labels, m, batch_size=None, length_before_new_iter=100000)
```

Use this when you want every batch to contain `m` examples per class.

Important constraints:

- `batch_size` must be a multiple of `m` when you pass it.
- `length_before_new_iter` must be at least `batch_size`.
- `m * (number of unique labels)` must be large enough for the batch size.

### `HierarchicalSampler`

```python
HierarchicalSampler(
    labels,
    batch_size,
    samples_per_class,
    batches_per_super_tuple=4,
    super_classes_per_batch=2,
    inner_label=0,
    outer_label=1,
)
```

Use this when labels have a hierarchy and you want batches built from grouped super-classes.

Important constraints:

- `labels` should be 2D.
- `batch_size` must be a multiple of both `super_classes_per_batch` and `samples_per_class`.
- It is a `BatchSampler`, so pass it through `batch_sampler` in the DataLoader.

### `TuplesToWeightsSampler`

```python
TuplesToWeightsSampler(model, miner, dataset, subset_size=None, **tester_kwargs)
```

Use this for offline mining-based sampling.

Workflow:

1. compute embeddings for a subset of the dataset,
2. mine hard tuples,
3. derive sampling weights from the mined tuples,
4. sample from the dataset using those weights.

`subset_size` should be chosen carefully so the mining step stays memory-safe.

### `FixedSetOfTriplets`

```python
FixedSetOfTriplets(labels, num_triplets)
```

Use this when the supervision is already triplet-shaped or when you want a fixed triplet sequence for evaluation.

## Tiny in-memory helper

`EmbeddingDataset` is handy when you already have embeddings and labels in memory and only need a PyTorch dataset wrapper for a smoke test or evaluation example.

## Practical selection checklist

- Want a downloadable benchmark dataset? Start with `BaseDataset` and the packaged dataset class.
- Want balanced class structure in each batch? Use `MPerClassSampler`.
- Want hierarchical batches? Use `HierarchicalSampler`.
- Want offline mining to drive sampling? Use `TuplesToWeightsSampler`.
- Want an already-fixed triplet stream? Use `FixedSetOfTriplets`.

## Cross-check against the tests

Useful native references for this layer include:

- `tests/datasets/test_cub.py`
- `tests/datasets/test_cars196.py`
- `tests/datasets/test_inaturalist2018.py`
- `tests/datasets/test_sop.py`
- `tests/samplers/test_m_per_class_sampler.py`
- `tests/samplers/test_fixed_set_of_triplets.py`
- `tests/samplers/test_hierarchical_sampler.py`
- `tests/samplers/test_tuples_to_weights_sampler.py`
