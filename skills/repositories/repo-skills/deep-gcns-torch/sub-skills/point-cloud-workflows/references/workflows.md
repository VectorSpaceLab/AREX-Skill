# Point-cloud workflow reference

This reference is distilled from task documentation, parsers, data loaders,
and architectures. Commands below are **non-executable command shapes** for an
independently staged implementation. Run them only after data and any
checkpoint have been provisioned by an approved, network-free preparation
process; replace the neutral entrypoint and resource placeholders. Do not open
or run files from an original source checkout. The bundled smoke in the parent
skill is the only direct executable.

## ModelNet40 classification

### Inputs and preparation

The loader expects a directory containing the extracted HDF5 collection
`modelnet40_ply_hdf5_2048`, with files matching `ply_data_train*.h5` and
`ply_data_test*.h5`. Each file has `data` (float32 point coordinates) and
`label` (int64 class ids). The default loader takes the first
`--num_points 1024` points. Training applies an independent per-coordinate
scale sampled from `[2/3, 3/2]`, a shift sampled from `[-0.2, 0.2]`, and a point
shuffle; test data is not augmented.

The source loader contains a `wget`/`unzip` fallback. Do not use it here:
pre-stage and validate the HDF5 tree instead. The 40-class count should come
from the training labels, and must agree with a checkpoint if one is used.

### Reference commands

Train shape (default ResGCN-28):

```bash
<modelnet-entrypoint> --phase train --n_blocks 28 --block res \
  --data_dir <prepared-modelnet-root>
```

Test shape:

```bash
<modelnet-entrypoint> --phase test --n_blocks 28 --block res \
  --pretrained_model <modelnet-checkpoint> \
  --data_dir <prepared-modelnet-root>
```

Important parser flags:

| Flag | Default / accepted values | Operational meaning |
|---|---|---|
| `--phase` | `train` or `test` | Selects experiment or evaluation setup. |
| `--data_dir` | `<prepared-modelnet-root>` placeholder | Prepared HDF5 root; no download. |
| `--num_points` | `1024` | Points retained from each cloud. |
| `--batch_size`, `--test_batch_size` | `32`, `50` | Train/test loader sizes; lower for memory. |
| `--pretrained_model` | empty | Required for a meaningful test run. |
| `--k` | `9` | KNN width. |
| `--block` | `res`, `plain`, `dense` | Backbone skip style. |
| `--conv` | `edge`, `mr` | Dense EdgeConv or max-relative convolution. |
| `--act` | `relu`, `prelu`, `leakyrelu` | Activation. |
| `--norm` | `batch`, `instance` | Normalization. |
| `--n_blocks`, `--n_filters` | `28`, `64` | Depth and feature width. |
| `--emb_dims` | `1024` | Global embedding width. |
| `--dropout`, `--lr`, `--epochs` | `.5`, `.001`, `400` | Head dropout and training controls. |
| `--use_cpu` | switch | Select CPU when CUDA is unavailable or intentionally avoided. |
| `--no_dilation` | switch | Sets `use_dilation=False`. |
| `--epsilon` | `.2` | Stochastic dilation probability parameter. |
| `--no_stochastic` | switch | Sets `use_stochastic=False`. |
| `--multi_gpus` | switch | Uses `DataParallel`; requires a tested CUDA/PyTorch setup. |

The parser uses `type=bool` for some values and has `--augment` enabled by
default with no complementary disable switch. Prefer the named switches above
rather than passing strings such as `--bias False` and expecting normal CLI
boolean parsing.

### Tensor path and output

The dataset yields `B x N x 3`. The training/evaluation path permutes it to
`B x 3 x N x 1`; the dense dynamic graph model returns `B x 40` logits. The
head and every dynamic block use the first three channels for KNN coordinates.
Global max and average pooling happen only at the classification head.

## S3DIS semantic segmentation

### Dense versus sparse choice

Prefer the **dense** path for the standard S3DIS experiment when a fixed-size
batch fits memory: the task README explicitly calls it more efficient. Choose
**sparse** when point counts or memory make dense `B x C x N x 1` tensors and
matrix KNN too expensive, or when an existing PyG pipeline already requires
node-level `batch` semantics. Do not silently change layout: the model,
loader, checkpoint, and test script must all agree.

Both paths use area 5 for the usual held-out evaluation. They apply PyG
`S3DIS` with `NormalizeScale`; the prepared dataset must be available at
`--data_dir`.

### Dense S3DIS

Reference train shape:

```bash
<s3dis-entrypoint> --multi_gpus --phase train \
  --data_dir <prepared-s3dis-root>
```

Reference alternate architecture and shallow run:

```bash
<s3dis-entrypoint> --conv mr --multi_gpus --phase train \
  --data_dir <prepared-s3dis-root> --n_blocks 7
```

Reference evaluation shape:

```bash
<s3dis-entrypoint> --pretrained_model <s3dis-dense-checkpoint> \
  --batch_size 32 --data_dir <prepared-s3dis-root>
```

Source-verified dense flags include:

- Data/device: `--phase train|test`, `--use_cpu`, `--data_dir`, `--area 5`,
  `--in_channels 9`, `--batch_size`, `--pretrained_model`, `--no_clutter`.
- Model: `--k 16`, `--block plain|res|dense`, `--conv edge|mr`,
  `--act relu|prelu|leakyrelu`, `--norm batch|instance`, `--n_filters 64`,
  `--n_blocks 28`, `--dropout .3`, `--epsilon .2`, and `--stochastic`.
- Train/resume: `--total_epochs 100`, `--lr .001`, `--lr_adjust_freq 20`,
  `--lr_decay_rate .5`, `--eval_freq 1`, `--multi_gpus`, and `--seed`.

The dense loader forms `data.pos.transpose(2, 1).unsqueeze(3)` and the same
for `data.x`, then concatenates channels. The expected input is therefore
`B x 9 x N x 1`, with targets `B x N`; model output is `B x n_classes x N`.
`--no_clutter` decreases the evaluation class count by one and must match the
checkpoint's label convention.

### Sparse S3DIS

Reference train and test shapes using the current parser are:

```bash
<s3dis-entrypoint> --phase train --data_dir <prepared-s3dis-root>
<s3dis-entrypoint> --pretrained_model <s3dis-sparse-checkpoint> \
  --batch_size 1 --data_dir <prepared-s3dis-root>
```

The sparse config accepts `--data_dir`; the older README and shell snippets
mention `--train_path` and `--test_path`, which are not current parser flags.
Passing those stale names fails with an unrecognized-argument error. The
current source also hard-codes area 5 in its `S3DIS` construction.

Sparse flags include `--phase train|test`, `--use_cpu`, `--data_dir`,
`--batch_size`, `--in_channels 9`, `--pretrained_model`, `--k 16`,
`--block plain|res|dense`, `--conv edge|mr` (the underlying sparse layer also
has `gat`, `gcn`, `gin`, `sage`, and `rsage` implementations), `--n_filters 64`,
`--n_blocks 28`, `--dropout .3`, `--epsilon .2`, `--stochastic`,
`--multi_gpus`, `--no_clutter`, and the training scheduler flags
`--total_epochs`, `--lr`, `--lr_adjust_freq`, `--lr_decay_rate`, `--print_freq`,
`--postname`, and `--seed`.

A PyG sparse batch carries `pos [N,3]`, `x [N,6]`, `y [N]`, and `batch [N]`.
The model concatenates position and features to `[N,9]`, runs dynamic KNN per
batch, and returns `[N,n_classes]` logits. With `--multi_gpus`, the loader
uses `DataListLoader` and PyG `DataParallel`; targets are concatenated across
list elements.

### Metrics and safe verification

Dense and sparse test paths accumulate per-class intersection and union and
report mean IoU, replacing undefined class divisions with one. A CPU smoke
only checks layouts and tiny forwards; it does not verify S3DIS mIoU, the
published Area-5 number, or a full CUDA memory profile. Lower test batch size
when a real evaluation hits out-of-memory; changing evaluation batch size does
not change predictions when model state and preprocessing are unchanged.

## Backend and memory decisions

- Dense matrix KNN materializes pairwise distances, approximately quadratic in
  `N` per cloud. First lower `batch_size`, then `num_points`, `k`, or depth;
  do not compensate by changing labels or silently dropping coordinates.
- Sparse storage avoids the dense feature layout but still constructs `k`
  neighbors and uses PyG scatter/message-passing extensions. It is not a
  guarantee of low memory for very large `N`.
- The dense implementation's `GraphConv2d` is limited to `edge` and `mr`.
  Generic layer customization belongs to `graph-layers`; do not infer that a
  sparse convolution choice is valid for dense checkpoints.
- `batch` ids must be contiguous and aligned with node rows. The source matrix
  KNN helper reshapes by inferred batch size, so equal point counts per graph
  are the safe contract for that implementation. Preserve this invariant or
  choose a verified variable-size KNN path before running a sparse batch.
- CPU execution is useful for parser/data/shape checks, but native PyG,
  `torch_scatter`, and `torch_cluster` wheels must still match the installed
  PyTorch version. A successful pure-torch smoke is not backend verification.
