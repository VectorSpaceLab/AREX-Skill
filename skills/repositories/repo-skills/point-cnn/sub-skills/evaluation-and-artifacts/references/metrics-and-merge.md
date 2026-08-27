# Metrics and merge rules

This reference is the operating contract for the legacy PointCNN evaluation
outputs. It describes what to check and what the reported numbers mean. It
does not acquire data, run inference, or write a repaired artifact.

## Shared HDF5 prediction contract

A prediction HDF5 produced by general segmentation testing must contain:

- `data_num`: integer vector `[B]`; only `0:data_num[b]` is valid for item `b`;
- `label_seg`: integer matrix `[B, M]`, zero-based predicted labels;
- `confidence`: finite floating matrix `[B, M]`, the selected class probability;
- `indices_split_to_full`: required for reconstruction merges, either `[B, M]`
  for a single full-scene index or `[B, M, 2]` for a `[room, point]` index.

`label_seg`, `confidence`, and indices must agree in their first two dimensions.
For every item, `0 <= data_num[b] <= M`. Padded values are not metric input.
Confidence should be in `[0, 1]`; a non-finite or out-of-range valid value is an
artifact error, not a reason to clip it. Valid indices must be non-negative and
within the selected full-scene or room bounds. See the bundled validator for a
read-only check.

The inference repeat count controls stochastic point coverage. It is not an
ensemble count and must be recorded separately from checkpoint identity.

## ShapeNet Parts

### Files and alignment

The evaluator consumes two parallel directory trees:

```text
<ground-truth>/<category>/<object>.seg
<prediction>/<category>/<object>.seg
```

The category directories and filenames must match exactly. If point data is
requested for optional error visualization, the corresponding path is built as
`<data>/<category>/<object>.pts` (the evaluator replaces the label-file suffix
with `pts`). A `.pts` file must have the same number of coordinate rows and
three numeric columns.

The built-in numeric category map is:

```text
2691156 Airplane       2773838 Bag          2954340 Cap
2958343 Car            3001627 Chair        3261776 Earphone
3467517 Guitar        3624134 Knife        3636649 Lamp
3642806 Laptop        3790512 Motorbike    3797390 Mug
3948459 Pistol        4099429 Rocket       4225987 Skateboard
4379243 Table
```

An unknown numeric category can fail category-name reporting. Preserve the
category names used by the data rather than guessing a remap.

### Label offset and score

The evaluator finds one global `label_min` across every ground-truth text file,
then evaluates `label_gt - label_min`. Predictions are already zero-based and
are used as read. Do not independently subtract one from prediction labels or
apply a category-local ground-truth offset.

With `part_avg` enabled, for each object and each part index from zero through
the maximum ground-truth part:

```text
IoU_part = (intersection + eps) / (union + eps)
IoU_object = mean(IoU_part over max_part + 1 parts)
```

The aggregate is an object-weighted mean of `IoU_object`. Category values are
printed as the mean of objects in that category, but the final value weights
categories by their object counts. Empty-part handling follows the evaluator's
epsilon convention.

Without `part_avg`, the value printed with the label `IoU` is instead the
per-object point accuracy:

```text
mean(label_gt == label_pred)
```

Do not call that number mean part IoU. Record the flag and the exact evaluator
output.

## S3DIS

### Room layout and required inputs

A merge root contains room directories, either directly or below area-like
folders. Every evaluated room must have:

```text
<room>/label.npy                 # one integer label per full-room point
<room>/*_pred*.h5                # one or more block predictions
```

Prediction HDF5 files must include `indices_split_to_full` with rank `[B, M]`.
The index is a full-room point index. For each valid prefix, require
`0 <= index < len(label.npy)`. A room with no prediction HDF5 is incomplete.
The post-merge artifact is `<room>/pred.npy`; despite its suffix, the evaluator
loads it as whitespace-delimited text. Its length must equal `label.npy`.

The merge implementation classifies a filename containing `zero` into the
zero branch. Other matching prediction filenames go to the half branch. For
an item, only `data_num[b]` entries are written. Within a branch, duplicate
indices are last-write-wins in directory iteration order; this is not a stable
confidence policy, so duplicate-index evidence should be reported.

### Two-branch confidence merge

For each full-room point, maintain label and confidence arrays for `zero` and
`half`. The final selection is:

```text
zero_confidence >= half_confidence  -> zero label
zero_confidence <  half_confidence  -> half label
```

Thus zero wins equal-confidence ties. A missing branch has its initial zero
confidence; an absent point can remain label 0, which is indistinguishable from
a real class-0 prediction without coverage evidence.

### 13-class IoU

The evaluator uses classes `0..12` and accumulates, for every room:

```text
gt_classes[c]       = count(gt == c)
positive_classes[c] = count(pred == c)
true_positive[c]     = count(gt == c and pred == c)
IoU[c] = true_positive[c] /
        (gt_classes[c] + positive_classes[c] - true_positive[c])
```

Overall accuracy is implemented as total true positives divided by total
predicted positives (which normally equals the number of evaluated points).
Average IoU is the unweighted mean of all 13 class IoUs. Missing rooms are
skipped by the evaluator, so a partial directory must never be accepted as a
complete score. Empty unions can make a class division invalid; report the
class and do not silently drop it.

## ScanNet

### Pickle and HDF5 alignment

The test pickle contains two sequential objects, loaded with Python 3
`encoding='latin1'`:

1. `xyz_all`: list of room point arrays;
2. `labels_all`: list of matching room label arrays.

A prediction directory contains matching HDF5 files with the shared datasets
and `indices_split_to_full` of shape `[B, M, 2]`. The first index is a room
position in `xyz_all`; the second is a point position in that room. Both must be
in range for every valid prefix. The validator does not inspect an untrusted
pickle unless the operator explicitly supplies `--allow-pickle-inspection`.

Filename classification is the same two-branch rule: names containing `zero`
feed the zero arrays; other matching `pred` files feed half. Duplicate
room/point indices are last-write-wins within a branch. The final selection uses
zero on ties and half only when its confidence is strictly greater. Uncovered
points remain zero-filled and must be counted as ambiguous coverage, not
assumed correct class 0.

### Point and voxel accuracy

Point accuracy is accumulated over rooms as:

```text
correct_points = count(pred == label)
denominator      = number_of_points - count(label == 0)
```

The implementation still counts correctly predicted label-0 points in the
numerator while excluding label-0 points from the denominator. Preserve this
quirk when reproducing its result and report invalid zero denominators.

Voxelization uses fixed resolution `0.0484`. Coordinates are offset by the room
minimum, divided by that resolution, and assigned to the implementation's
integer voxel id. The first point selected for each unique voxel supplies the
voxel ground-truth label. Voxel prediction is the majority label among points
in that voxel, with `argmax` tie behavior. Voxel accuracy applies the same
label-0 denominator rule and the same numerator quirk. Do not substitute a
more conventional voxel policy and call it the project score.

## Semantic3D

### Version gate and scene table

The version must be exactly `full` or `reduced`. The legacy implementation
otherwise falls back to the reduced table, so reject spelling or case errors
before invoking it.

Reduced scenes, exact point lengths, and output stems are:

```text
MarketplaceFeldkirch  10538633  marketsquarefeldkirch4-reduced
StGallenCathedral     14608690  stgallencathedral6-reduced
sg27                  28931322  sg27_10-reduced
sg28                  24620684  sg28_2-reduced
```

Full scenes are:

```text
stgallencathedral_station1   31179769  stgallencathedral1
stgallencathedral_station3   31643853  stgallencathedral3
stgallencathedral_station6   32486227  stgallencathedral6
marketplacefeldkirch_station1 26884140 marketsquarefeldkirch1
marketplacefeldkirch_station4 23137668 marketsquarefeldkirch4
marketplacefeldkirch_station7 23419114 marketsquarefeldkirch7
birdfountain_station1        40133912  birdfountain1
castleblatten_station1       31806225  castleblatten1
castleblatten_station5       49152311  castleblatten5
sg27_station3               422445052  sg27_3
sg27_station6               226790878  sg27_6
sg27_station8               429615314  sg27_8
sg27_station10              285579196  sg27_10
sg28_station2               170158281  sg28_2
sg28_station5               267520082  sg28_5
```

The merge selects HDF5 filenames containing the scene key whose stem ends in
`_pred`. Each selected file must have rank-2 full-point indices in
`[0, scene_length)`. It uses only valid `data_num` prefixes.

For each point, the candidate with the larger confidence replaces the current
candidate. Equal confidence keeps the earlier label. The merge creates
`results/<output-stem>.labels` and writes `merged_label + 1`, so these
submission labels are one-based while HDF5 predictions are zero-based. An
uncovered point is emitted as label `1`; coverage must therefore be recorded
separately.

Full-scene arrays are large: process one approved result set at a time and
check memory/disk before any merge. Never use a complete Semantic3D merge as a
smoke test.

## Invocation and evidence record

If the legacy evaluator executables are available in the approved runtime, the
observable command contracts are:

```text
ShapeNet:   eval_shapenet_seg.py --folder_gt GT --folder_pred PRED [--folder_data PTS] [--part_avg]
S3DIS merge: s3dis_merge.py --datafolder ROOT
S3DIS score: eval_s3dis.py --data ROOT
ScanNet:    eval_scannet.py --datafolder PRED_DIR --picklefile TEST_PICKLE
Semantic3D: semantic3d_merge.py --datafolder PRED_DIR --version full|reduced
```

Run only after the bundled read-only validator succeeds. Preserve stdout,
stderr, command arguments, input version, checkpoint prefix, and all warnings.
The merge commands write outputs; use an approved disposable copy rather than
assuming they are read-only.
