---
name: segmentation-workflows
description: "Route legacy PointCNN TensorFlow 1.x graph-mode segmentation
  training and inference for ShapeNet Parts, S3DIS, ScanNet, and Semantic3D,
  including FPS prerequisites and prediction artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Segmentation workflows

Use this sub-skill when a Researcher needs to train, validate, or test the
PointCNN segmentation graph for ShapeNet Parts, S3DIS, ScanNet, or Semantic3D.
This is legacy TensorFlow 1.x graph-mode code. A successful Python import or
CPU-side HDF5 check is not evidence that a segmentation graph can execute.

## Hard prerequisite: GPU FPS custom operators

All four shipped segmentation settings select `sampling = 'fps'`. During graph
construction, `pointcnn.py` imports `sampling/tf_sampling.py`, which loads
`tf_sampling_so.so`. The registered `FarthestPointSample`, `GatherPoint`, and
gradient operators are `DEVICE_GPU` kernels only. Segmentation therefore needs
a shared library built for the target TensorFlow/Python/CUDA ABI and a usable
CUDA GPU; there is no supported CPU fallback for these settings.

Run the read-only preflight before graph construction:

```bash
python3 scripts/check_fps_prerequisites.py \
  --sampling-dir sampling \
  --source-dir sampling \
  --load-library --require-gpu --json
```

The preflight does not compile, download, create a session, or execute an FPS
kernel. `PARTIAL_REQUIRED_BACKEND` means the files/runtime are only inspected;
it is never a pass. `BLOCKED_REQUIRED_BACKEND` means a required component is
missing or failed. Current runtime evidence is TensorFlow 1.15 import and GPU
discovery passed, while a bounded GPU/custom-op session timed out. Preserve
`BLOCKED_REQUIRED_BACKEND` for FPS and do not claim that GPU custom operators
ran until a bounded target-GPU custom-op smoke actually completes.

## Route the workflow

1. Send dataset acquisition, conversion, block construction, and file-list
   generation to [data-preparation](../data-preparation/SKILL.md). Do not
   download, decompress, or convert large datasets from this sub-skill.
2. Choose the exact dataset setting in
   [configurations](references/configurations.md), including its class count,
   feature width, and block/index convention.
3. Validate every flat HDF5 file list, or an explicit HDF5 path, before opening
   a TensorFlow graph:

   ```bash
   python3 scripts/validate_segmentation_h5.py \
     --filelist DATA/train_files.txt --data-dim 3 --num-class 50
   ```

   The validator is read-only. It checks required datasets, ranks, compatible
   dtypes, finite data, active point counts, active label ranges, optional
   `indices_split_to_full` rank/shape/non-negativity, and optional source-index
   bounds. A trainer parent list of child lists must be validated one child
   HDF5 list at a time; it is not a flat input list.
4. Run a foreground command from
   [CLI and prediction contracts](references/cli-and-prediction-contract.md)
   with explicit data, checkpoint, and output paths. Do not copy the historical
   backgrounding launchers; several contain duplicated or unsupported flags.
5. Send prediction validation, block merging, and metrics to
   [evaluation-and-artifacts](../evaluation-and-artifacts/SKILL.md). This skill
   ends at model outputs and does not merge or score them.

The model argument is normally `pointcnn_seg`; the setting argument is the
module name under `pointcnn_seg/`, such as `shapenet_x8_2048_fps`. The setting
and checkpoint must describe the same graph: `num_class`, `data_dim`, feature
flags, layer arrays, and `sampling` must match.

## Train and validate

`train_val_seg.py` requires these exact arguments:

- `--filelist/-t` and `--filelist_val/-v`: training and validation HDF5 lists;
- `--save_folder/-s`: output parent;
- `--model/-m`: normally `pointcnn_seg`;
- `--setting/-x`: a module under `pointcnn_seg/`.

Optional exact arguments are `--load_ckpt/-l`, `--epochs`, `--batch_size`,
`--log FILE` (use `--log -` for stdout), `--no_timestamp_folder`, and
`--no_code_backup`. Example:

```bash
CUDA_VISIBLE_DEVICES=0 python3 train_val_seg.py \
  --filelist DATA/train_files.txt --filelist_val DATA/val_files.txt \
  --save_folder OUTPUT/seg --model pointcnn_seg \
  --setting shapenet_x8_2048_fps --epochs 1 --batch_size 1 \
  --no_code_backup --log -
```

Without `--no_timestamp_folder`, the run root is
`SAVE_FOLDER/MODEL_SETTING_TIMESTAMP_PID/`; with it, the root is exactly
`SAVE_FOLDER/`. The trainer creates `ckpts/` (checkpoints such as
`ckpts/iter-STEP`) and `summary/` (TensorBoard event files), and writes a log
unless `--log -` is used. A checkpoint is restored from `--load_ckpt` or the
latest checkpoint in that root when available. A one-epoch/tiny run is only a
bounded graph/data smoke, not a benchmark.

The trainer loads `data`, `data_num`, `label`, and `label_seg` through
`data_utils.load_seg`; it samples `sample_num` points, with bounded random
variation during training. Validation reports loss, point accuracy, and mean
per-class accuracy. Keep `data_num` accurate: only `0:data_num[i]` is active;
padded `label_seg` values do not become valid labels automatically.

## Inference and prediction artifacts

For S3DIS, ScanNet, and Semantic3D, `test_general_seg.py` accepts exactly
`--filelist/-t`, `--load_ckpt/-l`, `--model/-m`, and `--setting/-x`, plus optional
`--max_point_num/-p`, `--repeat_num/-r`, and `--save_ply/-s`:

```bash
CUDA_VISIBLE_DEVICES=0 python3 test_general_seg.py \
  --filelist DATA/scannet/seg/test_files.txt \
  --load_ckpt OUTPUT/seg/ckpts/iter-STEP \
  --model pointcnn_seg --setting scannet_x8_2048_fps \
  --max_point_num 8192 --repeat_num 1 --save_ply
```

`--max_point_num` defaults to `8192`, is the fixed graph placeholder width,
and must equal the input HDF5 `data.shape[1]` (and be at least every
`data_num[i]`). `repeat_num` defaults to `1` and changes random coverage and
inference batch size; it is not an ensemble count. For each input `name.h5`,
the tester writes `name_pred.h5` beside it with:

- `data_num`: copied active point counts;
- `label_seg`: `[items, max_point_num]` predicted labels, with `-1` in unused
  padding;
- `confidence`: `[items, max_point_num]` retained maximum softmax probability,
  with zero in padding;
- `indices_split_to_full`: copied unchanged when present.

For each point, the tester keeps the class from the sampled occurrence with the
largest maximum softmax probability; it does not average probabilities or
vote. With `--save_ply`, `data_utils.save_ply_property_batch` writes colored
files named `name_predply_label_0000.ply`, `name_predply_label_0001.ply`, and so
on beside the prediction HDF5. PLY is visualization only.

For ShapeNet Parts, `test_shapenet_seg.py` accepts exactly
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

The script uses `setting.sample_num` even though it parses `--sample_num`. It
creates `DATA/shapenet/test_data_pred_nips_1/CATEGORY/` and writes one
category-local integer label per original point to `BASENAME.seg`. The
coordinate tree must contain one `.pts` file per HDF5 item in the same sorted
category/file order; a point-count mismatch asserts. With `--save_ply`, it
also writes `DATA/shapenet/test_data_pred_nips_1_ply/CATEGORY/BASENAME.ply`.
The category list is `category part_count` per row; row order must match the
HDF5 object label, and cumulative part offsets are used only to restrict logits
before category-local labels are written.

Do not merge or score these artifacts here. Use the evaluation sibling for the
ShapeNet `.seg` tree, general prediction HDF5, PLY inspection, and all
block-to-full mappings.

## Failure gates

- Stop before training/testing if FPS cannot be loaded or executed on the
  target GPU. Diagnose rather than silently switching to CPU.
- Stop on HDF5 rank, dtype, finite-value, point-count, label-range, or index
  inconsistencies; repair the data contract upstream.
- Stop on checkpoint/setting mismatch; select or rebuild the matching setting.
- Stop if general inference uses a `max_point_num` different from the HDF5
  padded width.
- Avoid dataset downloads, decompression, full conversion, and long benchmark
  runs in a smoke check.

Read the linked references for the exact schemas, configuration matrix,
output names, merge boundaries, and recovery actions.
