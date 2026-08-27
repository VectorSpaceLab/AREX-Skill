# CLI and prediction contracts

Run commands from a PointCNN working copy containing the legacy scripts and the
selected `pointcnn_seg` model/settings modules. Supply your own data,
checkpoint, and output paths. These recipes are foreground commands and
intentionally omit historical background jobs and launcher argument defects.
Before any graph command, run the FPS preflight and the read-only HDF5
validator. A preflight is not proof that a CUDA FPS kernel executed.

## Required HDF5 and file-list inputs

A flat segmentation file list is UTF-8 text with one HDF5 path per line and
no blank lines, comments, or inline annotations; paths are resolved relative
to the list file by `data_utils.load_seg`. Training may instead receive a
parent list whose entries are child HDF5 lists; validate each child list
directly. Every HDF5 file used for training,
validation, or general inference must contain:

- `data`: floating rank 3, shape `[items, padded_points, data_dim]`, with
  `items > 0`, `padded_points > 0`, `data_dim >= 3`, and finite values;
- `data_num`: integer rank 1, shape `[items]`, each value in
  `1..padded_points`;
- `label`: integer rank 1 `[items]` or rank 2 `[items, 1]`, one object/category
  placeholder per item;
- `label_seg`: integer rank 2 `[items, padded_points]`; only
  `label_seg[i, :data_num[i]]` is active.

For S3DIS, ScanNet, and Semantic3D block workflows, optional
`indices_split_to_full` must be integer rank 2 `[items, padded_points]` or rank
3 `[items, padded_points, 2]`. It maps only active block points back to a source
space: S3DIS and Semantic3D use one point index, while ScanNet uses
`(room_id, in_room_point_id)`. Its source upper bound is dataset metadata and
must be checked before merge. The validator checks non-negativity and can check
exclusive bounds with `--full-point-count` and, for rank-3 maps,
`--index-group-count`.

Run the validator without writing any file:

```bash
python3 scripts/validate_segmentation_h5.py \
  --filelist DATA/train_files.txt --data-dim 3 --num-class 50

# Or check an explicit file without constructing a list.
python3 scripts/validate_segmentation_h5.py --h5 DATA/one_block.h5 \
  --data-dim 7 --num-class 8 --full-point-count 123456
```

It also enforces one padded point/data width and one optional index-rank
contract across all files in a checked flat list. It returns nonzero on missing
keys, bad ranks/dtypes, nonfinite data, invalid counts, active label errors, or
invalid mappings. It never repairs or rewrites inputs.

## FPS preflight boundary

The shipped settings use GPU-only custom operators from `sampling/`. Inspect
both source/build layout and the TensorFlow runtime without compiling or
executing a kernel:

```bash
python3 scripts/check_fps_prerequisites.py \
  --sampling-dir sampling --source-dir sampling \
  --load-library --require-gpu --json
```

`--load-library` only calls TensorFlow's shared-library loader; it does not
create a session or execute `FarthestPointSample`/`GatherPoint`.
`PARTIAL_REQUIRED_BACKEND` is still unexecuted and is not a pass;
`BLOCKED_REQUIRED_BACKEND` is the required stop status for a missing/failed
backend. Preserve the current observed block when GPU/custom-op execution
cannot complete.

## Training and validation

`train_val_seg.py` has these exact arguments:

- required: `--filelist/-t`, `--filelist_val/-v`, `--save_folder/-s`,
  `--model/-m`, `--setting/-x`;
- optional: `--load_ckpt/-l`, `--epochs`, `--batch_size`, `--log FILE`,
  `--no_timestamp_folder`, `--no_code_backup`.

Use `--log -` to keep logs on stdout:

```bash
CUDA_VISIBLE_DEVICES=0 python3 train_val_seg.py \
  --filelist DATA/train_files.txt --filelist_val DATA/val_files.txt \
  --save_folder OUTPUT/seg --model pointcnn_seg \
  --setting shapenet_x8_2048_fps --epochs 1 --batch_size 1 \
  --no_code_backup --log -
```

The output root is `SAVE_FOLDER/MODEL_SETTING_TIMESTAMP_PID/` unless
`--no_timestamp_folder` makes it exactly `SAVE_FOLDER/`. The trainer creates
`ckpts/` with checkpoint prefixes such as `iter-STEP`, `summary/` with
TensorBoard events, and a log file when `--log` is not `-`. `--load_ckpt` is
restored explicitly; without it, the latest checkpoint in the selected
`ckpts/` directory is used if present. Do not reuse a root for a setting with a
different graph.

Dataset routing examples (paths are placeholders):

```bash
# ShapeNet Parts
... --filelist DATA/shapenet/train_val_files.txt \
    --filelist_val DATA/shapenet/test_files.txt \
    --setting shapenet_x8_2048_fps

# S3DIS held-out Area N
... --filelist DATA/s3dis/train_files_for_val_on_Area_N.txt \
    --filelist_val DATA/s3dis/val_files_Area_N.txt \
    --setting s3dis_x8_2048_fps

# ScanNet
... --filelist DATA/scannet/seg/train_files.txt \
    --filelist_val DATA/scannet/seg/test_files.txt \
    --setting scannet_x8_2048_fps

# Semantic3D
... --filelist DATA/semantic3d/train_data_files.txt \
    --filelist_val DATA/semantic3d/val_data_files.txt \
    --setting semantic3d_x4_2048_fps
```

These are routing examples, not performance recipes. Confirm the required FPS
backend and choose a bounded run appropriate to the available data.

## General segmentation inference

Use `test_general_seg.py` for S3DIS, ScanNet, and Semantic3D. Its exact
arguments are required `--filelist/-t`, `--load_ckpt/-l`, `--model/-m`, and
`--setting/-x`; optional `--max_point_num/-p`, `--repeat_num/-r`, and
`--save_ply/-s`:

```bash
CUDA_VISIBLE_DEVICES=0 python3 test_general_seg.py \
  --filelist DATA/scannet/seg/test_files.txt \
  --load_ckpt OUTPUT/seg/ckpts/iter-STEP \
  --model pointcnn_seg --setting scannet_x8_2048_fps \
  --max_point_num 8192 --repeat_num 1 --save_ply
```

`max_point_num` defaults to `8192`, fixes the graph placeholder width, and
must equal the HDF5 `data.shape[1]`; every `data_num` must be no larger. The
runtime batch size is `repeat_num * ceil(max_point_num / setting.sample_num)`.
For each input `name.h5`, output is `name_pred.h5` in the same directory:

| Dataset | Shape / meaning |
|---|---|
| `data_num` | copied active point counts `[items]` |
| `label_seg` | predicted labels `[items, max_point_num]`; padding stays `-1` |
| `confidence` | retained maximum softmax probabilities `[items, max_point_num]`; padding is `0` |
| `indices_split_to_full` | copied only when present; required for block merge |

The tester samples repeatedly and keeps, for each point, the sampled class with
the largest maximum class probability. It does not average probabilities or
vote. With `--save_ply`, the source naming expression produces
`name_predply_label_0000.ply`, `name_predply_label_0001.ply`, and so on. These
are colored visualization files, not merge or metric inputs.

The mapping/output boundary is dataset-specific:

- S3DIS rank-2 mappings go to the sibling S3DIS merge route, which writes
  per-room/dataset `pred.npy` only after its source `label.npy` tree is present.
- ScanNet rank-3 `(room, point)` mappings go to the sibling
  `eval_scannet.py --datafolder PREDICTIONS --picklefile TEST_PICKLE` route.
- Semantic3D rank-2 mappings go to the sibling
  `semantic3d_merge.py --datafolder PREDICTIONS --version reduced|full` route,
  which writes `results/*.labels` for the selected fixed cloud table.

Do not perform these merges in this sub-skill.

## ShapeNet Parts inference

Use `test_shapenet_seg.py`, whose exact required arguments are
`--filelist/-f`, `--category/-c`, `--data_folder/-d`, `--load_ckpt/-l`,
`--model/-m`, and `--setting/-x`; optional arguments are `--repeat_num/-r`,
`--sample_num`, and `--save_ply/-s`:

```bash
CUDA_VISIBLE_DEVICES=0 python3 test_shapenet_seg.py \
  --filelist DATA/shapenet/test_files.txt \
  --category DATA/shapenet/categories.txt \
  --data_folder DATA/shapenet/test_data \
  --load_ckpt OUTPUT/seg/ckpts/iter-STEP \
  --model pointcnn_seg --setting shapenet_x8_2048_fps \
  --repeat_num 1 --save_ply
```

The implementation uses `setting.sample_num` even if `--sample_num` is parsed.
The category file contains `category part_count` rows; row order is the HDF5
object-label order. For each sorted category/file item under `data_folder`,
the tester writes one category-local integer per original coordinate at:

```text
DATA/shapenet/test_data_pred_nips_REPEAT/CATEGORY/BASENAME.seg
```

The matching `.pts` file must have exactly `data_num[i]` coordinate rows and
must be in the same sorted order as the HDF5 items. With `--save_ply`, the
sibling path is:

```text
DATA/shapenet/test_data_pred_nips_REPEAT_ply/CATEGORY/BASENAME.ply
```

The tester creates output directories through the PLY writer. Route `.seg`
length/category checks and IoU to the sibling evaluation skill; do not treat
PLY as the metric source.

## Repeat and confidence semantics

Both testers tile enough sampled graph examples to cover the active point set;
a point can occur more than once. The retained class is the occurrence with
the largest maximum softmax probability, with that probability written to
`confidence` for general inference. `repeat_num` changes stochastic coverage
and fixed inference batch size, not checkpoint count. It can sharply increase
memory use and does not justify a benchmark claim. Validate counts, label
ranges, padding, and index mappings before sending artifacts to merge/eval.
