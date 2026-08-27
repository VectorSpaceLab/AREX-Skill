# Segmentation configurations

Use these exact module names with `--model pointcnn_seg --setting MODULE`.
Every shipped module uses `sampling = 'fps'`, `sample_num = 2048`, X-Conv/X-DeConv
layers, and `with_X_transformation = True`. The four settings are not
interchangeable: a checkpoint must be restored with the same class count,
feature width, sampling mode, and architecture arrays.

| Dataset | Setting | Classes | `data_dim` | Features | Default batch | Active mapping |
|---|---|---:|---:|---|---:|---|
| ShapeNet Parts | `shapenet_x8_2048_fps` | 50 global logits; category-local output | 3 | XYZ only | 16 | no `indices_split_to_full`; object/category labels |
| S3DIS | `s3dis_x8_2048_fps` | 13 | 6 | XYZ + 3 RGB features | 16 | rank-2 `[block, point]` index |
| ScanNet | `scannet_x8_2048_fps` | 21 | 3 | XYZ only | 16 | rank-3 `[block, point, 2]` `(room_id, point_id)` |
| Semantic3D | `semantic3d_x4_2048_fps` | 8 | 7 | XYZ + RGB + intensity | 12 | rank-2 `[block, point]` full-cloud index |

In every row, `data` is `[items, padded_points, data_dim]`; only
`data[i, :data_num[i], :]` is active. If `data_dim > 3`, the first three
channels are XYZ and the remainder are features. The validator accepts the
floating dtypes emitted by the source converters and checks finite values; the
legacy loader casts data to `float32` before feeding TensorFlow.

## ShapeNet Parts

- **Input:** a flat list such as `DATA/shapenet/test_files.txt`, category rows
  `category part_count` in `DATA/shapenet/categories.txt`, and sorted category
  directories of `.pts` files under `DATA/shapenet/test_data`.
- **Graph:** `shapenet_x8_2048_fps`, `num_class=50`, `data_dim=3`, default batch
  16. The HDF5 `label` is an object category row index, not a segmentation
  class id. Active `label_seg` values are global part ids in prepared training
  files; the tester restricts logits to the category's cumulative range and
  writes category-local labels.
- **Training lists:** a direct HDF5 list may be used for `--filelist_val`; a
  training `--filelist` may be a parent list of child lists, as accepted by the
  legacy trainer. Validate each child list directly.
- **Outputs:** `test_shapenet_seg.py` writes
  `<data_folder>_pred_nips_<repeat_num>/<category>/<basename>.seg`, exactly one
  integer per `.pts` coordinate. `--save_ply` writes the sibling
  `<data_folder>_pred_nips_<repeat_num>_ply/<category>/<basename>.ply`.
- **Boundary:** send `.seg` length/category checks and IoU to
  [evaluation-and-artifacts](../../evaluation-and-artifacts/SKILL.md). Do not
  treat a PLY as the metric input.

## S3DIS

- **Graph:** `s3dis_x8_2048_fps`, `num_class=13`, `data_dim=6`, default batch 16.
  The six channels are XYZ plus RGB normalized by the preparation workflow.
- **Lists:** the preparation workflow produces
  `DATA/s3dis/train_files_for_val_on_Area_N.txt`, child lists under
  `DATA/s3dis/filelists/`, and `DATA/s3dis/val_files_Area_N.txt`. Use the
  Area-N validation list for a held-out area and the generated parent training
  list for training. Do not hand-edit the duplicated historical launcher.
- **Inference:** run `test_general_seg.py --filelist DATA/s3dis/val_files_Area_N.txt`
  with `--max_point_num` equal to the HDF5 padded width. Each `*_pred.h5`
  contains `data_num`, predicted `label_seg`, `confidence`, and copied rank-2
  `indices_split_to_full` for block-to-dataset mapping.
- **Boundary:** send `*_pred.h5` structural checks and merging to
  [evaluation-and-artifacts](../../evaluation-and-artifacts/SKILL.md). Its
  S3DIS merge consumes a prediction tree with per-category `label.npy` and
  writes `pred.npy`; evaluation then reads the S3DIS root. This sub-skill does
  not perform either operation.

## ScanNet

- **Graph:** `scannet_x8_2048_fps`, `num_class=21`, `data_dim=3`, default batch
  16. Class 0 is ignored by the shipped label weights; do not silently remap
  it during input validation.
- **Lists:** the preparation workflow produces
  `DATA/scannet/seg/train_files.txt`, child lists under
  `DATA/scannet/seg/filelists/`, and `DATA/scannet/seg/test_files.txt`.
  Test HDF5 files are block-based and carry rank-3
  `indices_split_to_full[..., 0:2] = (room_id, in_room_point_id)`.
- **Inference:** run `test_general_seg.py --filelist DATA/scannet/seg/test_files.txt`
  with `--max_point_num` equal to the block HDF5 padded width. The prediction
  HDF5 copies the pair mapping unchanged.
- **Boundary:** send predictions plus `scannet_test.pickle` to the sibling
  evaluation route. Its ScanNet merge/evaluation entry point is
  `eval_scannet.py --datafolder PREDICTIONS --picklefile TEST_PICKLE`; this
  sub-skill does not merge room points or report accuracy.

## Semantic3D

- **Graph:** `semantic3d_x4_2048_fps`, `num_class=8`, `data_dim=7`, default batch
  12. The seven channels are XYZ, RGB, and intensity after preparation.
- **Lists:** the preparation workflow produces
  `DATA/semantic3d/train_data_files.txt`, `val_data_files.txt`, and
  `test_files.txt`, with optional child lists under `DATA/semantic3d/filelists/`.
  Test HDF5 blocks use rank-2 `indices_split_to_full` into the selected cloud.
- **Inference:** run `test_general_seg.py --filelist DATA/semantic3d/test_files.txt`
  (or the prepared test-list path for a local layout). Each `*_pred.h5`
  preserves `data_num`, confidence, labels, and full-cloud point indices.
- **Boundary:** send predictions to the sibling merge route, choosing exactly
  one version: `semantic3d_merge.py --datafolder PREDICTIONS --version reduced`
  or `--version full`. It writes `results/*.labels` using the version's fixed
  cloud-length table. This sub-skill does not acquire the roughly large source
  dataset, merge blocks, or score labels.

## Architecture and sample semantics

The architecture arrays are part of the checkpoint contract. `xconv_params`
use `(K, D, P, C, links)` and `xdconv_params` use
`(K, D, pts_layer_idx, qrs_layer_idx)`; changing them changes variable shapes
or names. `sample_num` is the graph sample width. Training applies bounded
random variation around it, while both testers use the setting's value even
when ShapeNet parses `--sample_num`. General inference uses
`repeat_num * ceil(max_point_num / sample_num)` sampled graph examples per
item. Repeated coverage is stochastic; it is not an ensemble or vote.
