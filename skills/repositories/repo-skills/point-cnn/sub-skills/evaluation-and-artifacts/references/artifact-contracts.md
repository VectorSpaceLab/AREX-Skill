# Artifact contracts

Use these contracts to decide whether a file is metric-ready. They are
read-only inspection rules; they do not authorize merging, rewriting, or
repairing an artifact.

## Prediction HDF5

General segmentation inference writes a sibling file whose name ends in
`_pred.h5`. The metric-facing datasets are:

| Dataset | Required shape/type | Contract |
|---|---|---|
| `data_num` | `[B]`, integer | Valid point count for each item; only the prefix `:data_num[b]` is input to a merge or metric. |
| `label_seg` | `[B, M]`, integer | Zero-based predicted class id. Its first two dimensions match `data_num`/`confidence`. |
| `confidence` | `[B, M]`, floating | Selected class probability for each point. Valid values are finite and expected in `[0, 1]`; padded values are normally zero. |
| `indices_split_to_full` | `[B, M]` or `[B, M, 2]`, integer | Optional for a block-local metric; required for S3DIS/Semantic3D merges and required as `[room, point]` for ScanNet. |

`M` is padded storage width, not necessarily the valid point count. Require
`0 <= data_num[b] <= M`. Do not compare padded labels or confidences. An index
map must have the same first two dimensions as `label_seg`; rank 2 means one
full-scene index per point and rank 3 means a final width of two. Valid indices
must be non-negative. Compare their upper bounds with the target scene/room
length whenever that length is known.

The inference writer may copy `indices_split_to_full` from the input HDF5. If
it did not, a block-only score is possible only when the ground-truth order is
known to be identical. Never invent an index map from a filename or row order.
The test writer initializes unused general labels to `-1`, but a valid
`data_num` prefix must contain actual labels in the selected class range.

The bundled `validate_prediction_artifacts.py` checks this contract and never
opens a file in write mode.

## ShapeNet Parts text tree

ShapeNet uses a text label tree, not prediction HDF5:

```text
GT_ROOT/<category>/<filename>.seg
PRED_ROOT/<category>/<filename>.seg
```

The two roots must contain the same category directories and filenames. Every
label file must parse as a finite, one-dimensional integer sequence after
normalizing a one-value file to length one. Ground-truth and prediction lengths
must match. Prediction labels are zero-based. Ground-truth labels are shifted
by one global minimum across the entire GT tree by the evaluator; preserve this
behavior and do not shift predictions.

Numeric category names are resolved through the 16-category built-in map. An
unknown numeric category is a hard compatibility error. Non-numeric names are
reported as their names. If point data is supplied for visualization, the
matching `.pts` path is under the same category and must contain the same number
of rows with three numeric coordinates. PLY error output is optional and is not
the metric source.

The `--part_avg` choice changes meaning. With it, the evaluator reports an
object mean over part IoUs; without it, its printed `IoU` is object point
accuracy. Record this flag in the result manifest.

## S3DIS room artifacts

A S3DIS merge root may be organized as `<area>/<room>` or as direct room
folders. A room is identified by `label.npy`:

```text
<room>/label.npy
<room>/*_pred*.h5
<room>/pred.npy       # generated merge output, text despite suffix
```

`label.npy` must be a one-dimensional integer sequence with labels in `0..12`.
Its length is the full-room point count. Each prediction file must contain the
shared HDF5 datasets and a rank-2 `indices_split_to_full`; all valid indices
must be less than the label length. `pred.npy`, when present, must parse as
text, have exactly the label length, and contain class ids in `0..12`.

Before merge, absent `pred.npy` is a pending-output warning; use a strict
review decision or a `--require-merged` validator option when a score is being
prepared. A room with no prediction HDF5 is incomplete. A partial tree can be
silently skipped by the legacy metric evaluator, so the expected room inventory
must be recorded separately.

The merge uses filename branches: names containing `zero` update zero, all
other matching `pred` HDF5 files update half. It consumes only valid prefixes,
then chooses zero when confidence ties. Duplicate indices within a branch are
last-write-wins in directory iteration order. Uncovered points retain class 0;
coverage must be checked rather than inferred from the label value.

## ScanNet pickle and prediction directory

ScanNet uses a flat prediction directory and a pickle with two sequential
objects:

```text
xyz_all       # list of room coordinate arrays
labels_all    # list of matching room label arrays
```

Python 3 compatibility requires loading each object with `encoding='latin1'`.
Each coordinate array must have a point axis of length equal to its label array.
Each prediction HDF5 must have rank-3 indices `[B, M, 2]`; index `[room, point]`
must identify an existing room and point in the pickle for every valid prefix.
The filename branch rule is zero versus half as described for S3DIS. Equal
confidence selects zero. A valid class-0 prediction and uncovered zero-filled
point are observationally indistinguishable without index coverage.

Pickle is an executable serialization format. The validator refuses to inspect
it unless `--allow-pickle-inspection` is explicitly supplied. Without that flag,
it still checks HDF5 shapes but cannot prove room/point ranges; this limitation
must remain in the handoff.

The score consists of point and voxel accuracy. Voxel size is fixed at `0.0484`.
Ground-truth voxel labels use the first point in each unique voxel, and voxel
predictions use majority voting. Both denominators exclude ground-truth label
0 while correct label-0 predictions remain in the numerator in the legacy
implementation.

## Semantic3D submission artifacts

Semantic3D merge consumes a flat directory of prediction HDF5 files. The
version argument is an exact enum: `full` or `reduced`. The resulting files are
written under:

```text
<prediction-root>/results/<scene-stem>.labels
```

The source predictions use zero-based classes, while submission lines are
`merged_label + 1`. Do not read output label 1 as proof of predicted class 1;
an uncovered point also becomes 1.

The selected scene key must occur in a filename whose stem ends in `_pred`.
Each valid rank-2 point index must be within that scene's fixed length. The
validator contains the exact reduced (four scenes) and full (15 scenes) key,
length, and output-stem tables. It reports a missing scene prediction instead
of allowing a merge to create a full default array. Duplicate points use the
larger confidence; equal confidence keeps the earlier label. Full scenes may
require multiple GB of memory, so inspect and plan before merging.

## Checkpoints, logs, summaries, and TensorBoard

A run directory normally contains:

```text
<run>/ckpts/
<run>/summary/
```

A checkpoint is a prefix plus its companion TensorFlow index and data files;
`.meta` alone, a directory name, or a log line claiming "saved" is not enough.
Match it to the model module, setting module, class/part count, data dimension,
preprocessing, and input list used by inference.

`summary/` contains TensorFlow event files. They may expose graph structure,
training/validation loss, top-1 or per-class accuracy, and learning rate, but
an event scalar is not an evaluation metric. Check that expected event files
are non-empty and that step continuity is plausible; do not equate a training
accuracy tag with a ShapeNet, S3DIS, ScanNet, or Semantic3D result.

A console/file `--log` transcript is run provenance and diagnostics. It can show
argument parsing, checkpoint restore, skipped inputs, and completion, but a
printed loss or "Done" line does not prove that every prediction file exists
or that a benchmark evaluator consumed the complete split. Keep log evidence
separate from `ckpts/`, `summary/`, and metric outputs.

A result record should preserve:

1. dataset and exact version/split;
2. model, setting, checkpoint prefix, and repeat number;
3. source input list and preprocessing/class map;
4. all prediction files and required-key/index preflight output;
5. merge command arguments and output inventory;
6. evaluator stdout/stderr, warnings, skipped rooms/scenes, empty classes, and
   optional PLY status;
7. the required-backend status (`BLOCKED_REQUIRED_BACKEND` until FPS executes).
