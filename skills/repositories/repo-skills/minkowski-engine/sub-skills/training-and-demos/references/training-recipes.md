# Training Recipes

## Purpose

Use this file to adapt MinkowskiEngine's training examples without running long downloads or training jobs.

## Dataset Item Contract

A sparse training dataset usually returns:

```python
coords, feats, labels
```

Where:

- `coords` is an `N x D` coordinate matrix before batching.
- `feats` is an `N x C` feature matrix.
- `labels` is either per-point/per-voxel labels or a per-example class label depending on the task.

## Quantization Step

For continuous point clouds, quantize before batching:

```python
coords_q, feats_q, labels_q = ME.utils.sparse_quantize(
    coordinates=points,
    features=features,
    labels=labels,
    ignore_label=-100,
    quantization_size=voxel_size,
)
```

`quantization_size` is a real hyperparameter. It changes the number of occupied voxels and therefore affects accuracy, memory, and speed.

## Collate Function Choices

### Built-in collate object

```python
loader = DataLoader(dataset, batch_size=batch_size, collate_fn=ME.utils.SparseCollation())
```

### Function collate

```python
loader = DataLoader(dataset, batch_size=batch_size, collate_fn=ME.utils.batch_sparse_collate)
```

### Custom dictionary collate

```python
def minkowski_collate_fn(batch):
    coordinates, features, labels = ME.utils.sparse_collate(
        [item["coordinates"] for item in batch],
        [item["features"] for item in batch],
        [item["labels"] for item in batch],
    )
    return {"coordinates": coordinates, "features": features, "labels": labels}
```

## Main-Process SparseTensor Construction

When DataLoader workers are used, keep `ME.SparseTensor(...)` construction in the main process. The coordinate manager is a C++ structure and should not be built in worker processes and then reused in the parent process.

```python
for coords, feats, labels in loader:
    sinput = ME.SparseTensor(features=feats, coordinates=coords)
    logits = model(sinput)
```

## Minimal Training Loop Skeleton

```python
model.train()
for coords, feats, labels in loader:
    sinput = ME.SparseTensor(features=feats, coordinates=coords)
    output = model(sinput)
    loss = criterion(output.F, labels.long())
    optimizer.zero_grad()
    loss.backward()
    optimizer.step()
```

For segmentation-style tasks, align `output.F` rows with voxel or point labels. For classification-style tasks, apply global pooling or a model head that returns per-example rows.

## Memory Pattern

Sparse batches can vary significantly in the number of active coordinates. On CUDA builds, periodic `torch.cuda.empty_cache()` can reduce repeated allocation pressure in long training loops.

## Safe First Check

Before using a real dataset, run `scripts/training_batch_check.py`. It verifies synthetic collation, sparse tensor construction, and a tiny forward pass without downloads.
