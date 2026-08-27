# Point-cloud troubleshooting

## Parser and entrypoint problems

**`unrecognized arguments: --train_path` or `--test_path`**

The sparse README and shell snippets are stale relative to the current sparse
config. Use `--data_dir` for both train and test. The current sparse source
uses area 5 internally. Dense uses `--data_dir` and exposes `--area` (default
5).

**Test mode creates a strange result path or crashes before loading.**

Pass a non-empty `--pretrained_model` path in test mode. The task configs derive
result/log directories from that path. Also pass the same model-shape flags
used at training time; do not rely on a checkpoint filename alone.

**A model import fails when launched from another directory.**

The task examples use a local `__init__.py` to insert a repository-relative
path and import sibling modules by bare names. That is an example-source
convention, not a portable package API. Run an approved entrypoint with its
working-directory expectations satisfied, or package/adapt the model in a
separate environment. The bundled smoke intentionally has no such import and
works from arbitrary CWD. Do not solve this by making a runtime skill open the
original checkout.

**`--conv`, `--block`, or boolean values behave unexpectedly.**

Dense layers accept `edge|mr`; sparse `GraphConv` has additional underlying
choices (`gat`, `gcn`, `gin`, `sage`, `rsage`), but individual parser help text
is narrower and should be treated as the interface for that task. PartNet's
dense architecture only implements `res` and `plain` blocks in its own
constructor. Several configs use `type=bool`, so `--bias False` may parse as a
truthy string; use documented switch flags and verify the printed arguments.
Plain blocks intentionally disable stochastic/dilated behavior in the model
construction.

## Data layout and labels

**HDF5 files are not found for ModelNet40.**

Check the exact extracted directory name `modelnet40_ply_hdf5_2048` and the
`ply_data_train*.h5`/`ply_data_test*.h5` patterns. Confirm keys `data` and
`label`, dtype/shape, and that `--num_points` is no larger than stored points.
Do not enable the source's automatic `wget` fallback in a controlled run.

**S3DIS produces a shape or class-count error.**

Confirm `data.pos` and `data.x` have the same point axis, and that
`pos + x` supplies nine channels for the default model. Dense expects
`B x 9 x N x 1` and targets `B x N`; sparse expects flattened `[N,9]`, targets
`[N]`, and a `[N]` `batch`. Ensure `--no_clutter` is consistent with label ids
and the checkpoint's output width.

**A sparse batch mixes clouds or KNN indexes cross a graph boundary.**

Check that `batch` is a contiguous zero-based vector and that every graph has
an expected point count. The source matrix-KNN implementation reshapes by an
inferred graph count, so variable-sized graphs are not automatically safe.
Test the actual selected backend with a tiny unequal-size fixture before a
real run; otherwise use compatible fixed-size batching.

**PartNet says the raw marker is missing or processed files are empty.**

For `sem_seg_h5`, verify `<data_dir>/raw/sem_seg_h5` exists and the desired
category-level folder uses the exact spelling `<Category>-<level>`, for example
`Bed-3`, with `train-*.h5`, `test-*.h5`, and `val-*.h5`. Verify HDF5 keys
`data` and `label_seg`. Then check the matching processed folder under
`processed/sem_seg_h5/level_<level>/<Category>-<level>/`. The source's
application-only download path is intentionally not a bundled recovery path.

**PartNet output classes or labels do not match.**

Check numeric category mapping, level, processed dataset, and checkpoint. The
model is category-specific; do not apply a Bed checkpoint to Chair or a level-3
checkpoint to another level. Treat labels above the expected class range as a
preparation error rather than relying on legacy label clamping.

## Checkpoints and device

**`state_dict` keys do not load.**

These utilities expect a checkpoint dictionary containing `state_dict`; some
training paths also save optimizer/scheduler state. Compare the model's
`module.` prefix (single GPU versus `DataParallel`) and exact architecture
width/depth. A mismatch in `in_channels`, `n_filters`, `n_blocks`, `k`, or
class count is not fixed by changing the map location.

**CPU evaluation fails while loading an optimizer.**

The source optimizer loader moves optimizer tensors with `.cuda()`. Do not
resume optimizer state in a CPU-only troubleshooting pass; load model weights
only with an explicitly device-aware adapter, or use a verified CUDA
environment. This is a source limitation, not evidence that the model forward
requires a GPU.

**CUDA or PyG extension import errors.**

Check the tuple of Python, PyTorch, PyG, `torch_scatter`, and `torch_cluster`
versions and whether the wheel was built for the active CUDA runtime. Dense
matrix KNN still imports/uses `torch_cluster` through the library surface in
some environments; sparse additionally uses PyG message passing and scatter.
Fix the environment before changing model flags. Route generic layer ABI and
KNN diagnosis to `graph-layers` when the issue is not task-specific.

## Memory and runtime

**Out of memory during a dense forward.**

Dense pairwise KNN is quadratic in points per cloud and deep feature tensors
scale with `B`, `N`, channels, and blocks. For test, try batch size 1. For a
bounded diagnosis, reduce `--batch_size`, `--num_points`, `--k`, or
`--n_blocks`, in that order as appropriate, and record the change. Do not
claim published accuracy from a reduced configuration. Sparse layout reduces
feature duplication but KNN and edge/message tensors can still dominate.

**Multi-GPU run hangs or gives a device/backend error.**

First run one device without `--multi_gpus`. Dense uses `torch.nn.DataParallel`;
sparse uses PyG `DataListLoader`/`DataParallel`. Confirm CUDA visibility,
per-device memory, and matching extension builds before re-enabling the flag.
Long distributed training is outside the safe skill actions.

**Metrics contain NaN or differ between dense and sparse.**

The source replaces undefined per-class IoU divisions with one in S3DIS,
whereas PartNet averages only classes with nonzero union per shape and excludes
class 0 from aggregate part IoU. Confirm task, split, clutter policy, class
count, and averaging rule before comparing numbers. A pure shape smoke cannot
validate metrics.

## Visualization boundary

**VTK cannot import or a window cannot open.**

This is optional PartNet visualization, not core inference. Do not install
packages or launch a GUI from the skill. Inspect generated OBJ rows and label
ranges non-interactively, or hand the prepared result to an environment with
VTK and a display. Keep the visualization folder/category/object naming
contract from [partnet.md](partnet.md).
