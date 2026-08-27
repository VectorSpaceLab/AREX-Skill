# Point-cloud data and tensor contracts

## Common point-cloud conventions

- A point row is ordered as `x, y, z` in the first three channels.
- Labels are integer class ids. Classification labels are one id per cloud;
  segmentation labels are one id per point.
- KNN is computed from coordinates, not from arbitrary feature channels. Keep
  coordinate channels in positions 0--2 when adding color, normals, or other
  features.
- All model tensors should be float32 unless a specific loss or index requires
  another dtype. Targets and `batch` are integer tensors.
- For every KNN call, require `1 <= k <= N` and, with dilation `d`,
  `k*d <= N`. The dense `topk` path otherwise fails before the model runs.

## Dense contract

Dense point-cloud layers operate on:

```text
features:  [B, C, N, 1]  float32
positions: first three channels of features, [B, 3, N, 1]
edge_index: [2, B, N, k] long
```

The dense KNN helper transposes/squeezes the last singleton dimension, computes
pairwise distances for each batch item, and returns neighbor and center indices.
`DenseDilatedKnnGraph(k, dilation, ...)` first requests `k*dilation` neighbors,
then takes every `dilation`-th neighbor, or a stochastic subset during
training when stochastic dilation is enabled. Dense `EdgeConv2d` and `MRConv2d`
return `[B, C_out, N, 1]` and preserve the point axis.

### S3DIS dense assembly

The PyG S3DIS item is assembled as:

```text
pos: [B, N, 3]
x:   [B, N, 6]
y:   [B, N]
inputs = cat(pos.transpose(2, 1).unsqueeze(3),
             x.transpose(2, 1).unsqueeze(3), dim=1)
inputs: [B, 9, N, 1]
out:    [B, n_classes, N]
```

`DenseDataLoader` must produce compatible point counts for a batch. If a
loader pads or batches a different shape, verify the resulting tensor before
calling a dense model; do not reshape labels independently of the point axis.
`data.y` stays aligned with the same `N` points.

### ModelNet dense assembly

The HDF5 loader returns NumPy `data [B,N,3]` after collation and `label [B]`.
The task path converts it to:

```text
[B, N, 3] -> permute -> [B, 3, N] -> unsqueeze(-1) -> [B, 3, N, 1]
```

The classification head pools over `N` and returns `[B, 40]`. Do not use this
pooled output as a segmentation output.

### PartNet dense assembly

The semantic PartNet path loads `Data(pos=[N,3], y=[N])` and
`DenseDataLoader` batches it as `pos [B,N,3]`, `y [B,N]`. The architecture
uses only positions:

```text
pos.transpose(2, 1).unsqueeze(3): [B, 3, N, 1]
out:                              [B, n_classes, N]
```

The model returns `log_softmax` scores and the training path uses `NLLLoss`.
Use `argmax(dim=1)` for predicted point labels.

## Sparse contract

Sparse point-cloud layers operate on one flattened node axis:

```text
x:          [N, C] float32
pos:        [N, 3] float32
batch:      [N] long, contiguous graph ids 0..B-1
edge_index: [2, N*k] long
out:        [N, C_out]
```

The source `DilatedKnnGraph` uses the batch vector to keep KNN neighborhoods
inside each cloud. Sparse residual/plain blocks return `(features, batch)`;
dense blocks concatenate channels and return `(features, batch)`. The S3DIS
model explicitly unpacks the block result and keeps the same `batch` vector
through the network.

A global feature uses scatter max over `batch`, producing `[B, C]`, then repeats
one global row for each node before concatenating it back to node features.
Therefore a sparse segmentation head must preserve the exact node order and
batch length; any filtering or sorting must apply to `pos`, `x`, `y`, and
`batch` together.

The source matrix-KNN helper infers `B` from `batch[-1] + 1` and reshapes the
flattened features into equal-length graphs. This is a stronger constraint
than the abstract `batch` contract: test variable-size clouds with the actual
chosen KNN/backend before relying on them. Never let a batch id skip a value.

## Dataset-specific records

### ModelNet40 HDF5

```text
<root>/modelnet40_ply_hdf5_2048/ply_data_train*.h5
<root>/modelnet40_ply_hdf5_2048/ply_data_test*.h5
HDF5 data:  float32 [objects, 2048, 3] (source collection)
HDF5 label: int64   [objects, 1] or collatable label shape
```

The task defaults to the first 1024 points. Validate that all files are
present, the requested point count does not exceed the stored count, and labels
are in `[0,39]` before invoking a training or test command.

### S3DIS

The task delegates storage and preprocessing to the PyG `S3DIS` dataset. Use
`--data_dir` as the dataset root and `--area 5` for dense; the sparse source
constructs area 5 directly. Apply the same `NormalizeScale` policy used by the
workflow. Do not mix a dense checkpoint with a sparse `Data` object or vice
versa.

### PartNet semantic HDF5

For the documented `sem_seg_h5` path, processing searches a category/level
folder under the raw dataset and reads split files named like:

```text
<root>/raw/sem_seg_h5/Bed-3/train-*.h5
<root>/raw/sem_seg_h5/Bed-3/test-*.h5
<root>/raw/sem_seg_h5/Bed-3/val-*.h5
```

Each file is expected to contain `data` (converted to float32, first three
columns used as `pos`) and `label_seg` (converted to long point labels).
Processed tensors are written under the matching `processed/sem_seg_h5/level_3/<Category>-3/`
folder as `train.pt`, `test.pt`, and `val.pt`. Verify these paths and split
names before blaming a model for a missing-data error.

PartNet's optional `ins_seg_h5` branch has a different raw layout and extra
point attributes (`nor`, `opacity`, `rgb`); it is not the default semantic
workflow and is not interchangeable with `sem_seg_h5` checkpoints.

## Shape checks before a run

1. Print or assert `features.ndim`, channel count, point count, and dtype.
2. For dense data, assert `features.shape == (B,C,N,1)` and labels align to
   `B,N` (or `B` for classification).
3. For sparse data, assert `x.shape[0] == pos.shape[0] == y.shape[0] == batch.shape[0]`.
4. Assert `batch.min()==0`, `batch.max()==B-1`, and no graph id is missing.
5. Assert `k*dilation <=` the smallest graph's point count.
6. Run `scripts/pointcloud_model_smoke.py --mode all` separately; it confirms
   the generic layouts but cannot validate a dataset's on-disk schema.
