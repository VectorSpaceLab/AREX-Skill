# Troubleshooting evaluation artifacts

Classify the failure first. Keep the original files unchanged, preserve the
validator output, and repair the upstream producer or approved copy rather than
padding, clipping, relabeling, or merging in place.

## First-response checklist

1. Confirm the dataset and exact evaluation version.
2. Record model, setting, checkpoint prefix, input list, class map, repeat
   number, output root, and whether the run was produced with the same
   preprocessing as the ground truth.
3. Run the read-only validator for the appropriate artifact family.
4. Check that every HDF5 valid prefix has the expected labels, confidence, and
   indices. Compare counts with the target labels before interpreting output.
5. Check `ckpts/` companions and non-empty `summary/` event files, but do not
   use either as a substitute for predictions.
6. Keep TensorFlow/FPS execution status separate from file inspection:
   TensorFlow 1.15 import and device discovery passed, but the GPU/custom-op
   session timed out. FPS remains `BLOCKED_REQUIRED_BACKEND`.

## HDF5 errors

### Missing `data_num`, `label_seg`, or `confidence`

**Meaning:** The file is not a general segmentation prediction, is incomplete,
or was written under a different schema.

**Action:** Stop the merge. Check that the upstream test writer finished and that
the file is the intended `*_pred.h5`. Re-run inference to a new output path
only after the segmentation workflow's checkpoint/setting and backend gates
pass. Do not synthesize a missing confidence dataset.

### Missing `indices_split_to_full`

**Meaning:** The file can describe block-local predictions but cannot be mapped
back to a full S3DIS room, ScanNet room/point, or Semantic3D scene.

**Action:** Confirm whether the input HDF5 had the index dataset. If it did,
inspect the writer/output copy process. If it did not, route back to data
preparation and regenerate inputs with the correct mapping. Never derive indices
from block order or filenames.

### Shape or valid-count mismatch

**Meaning:** `data_num` does not match the number of prediction rows, or a valid
count exceeds the padded width. This commonly indicates mixed input files,
partial writes, or an incorrect `max_point_num`/sample contract.

**Action:** Treat as a hard error. Identify the exact source HDF5 and rerun the
producer with the matching setting. Do not truncate to the shortest array,
pad with class 0, or score only a convenient prefix.

### Label outside the expected range

**Meaning:** The class/part setting and checkpoint may not match, or a label
offset was applied at the wrong stage.

**Action:** For general predictions, labels are zero-based. For ShapeNet, only
the evaluator shifts ground truth by its single global minimum; it does not
shift predictions. For Semantic3D submission output, the final text is
one-based only after merging. Verify the selected setting's class count and
category/part range upstream.

### Confidence is non-finite or outside `[0, 1]`

**Meaning:** The artifact is corrupt, contains logits instead of softmax
probabilities, or has invalid padded/valid data.

**Action:** Stop. Do not replace NaN with zero or clip values. Check the model
output operation and whether the HDF5 write completed. Recreate the prediction
with the expected softmax confidence contract.

### Index is negative or out of range

**Meaning:** The index map and target scene/room do not belong together, or a
source point count changed.

**Action:** Compare the index range with `label.npy`, the ScanNet pickle room
lengths, or the exact Semantic3D version table. Check valid prefixes only, but
never hide an out-of-range valid index. Rebuild the input mapping upstream.

## ShapeNet failures

### Category or filename missing on one side

**Meaning:** The evaluator will attempt a same-category/same-filename load and
the result is incomplete or misaligned.

**Action:** Produce a complete matching GT/pred tree or explicitly narrow the
approved evaluation set and record that it is not a full benchmark. Do not
rename files just to satisfy alignment without checking object identity.

### One label file has a different length

**Meaning:** Prediction points and ground-truth points are not aligned.

**Action:** Stop. Check the `.pts` row count, `data_num`, object ordering, and
conversion. Do not truncate, repeat, or pad labels.

### Part IoU is unexpectedly high or low

**Meaning:** Common causes are applying a second prediction offset, using a
category-local GT offset, choosing `--part_avg` unexpectedly, or interpreting
the non-part-avg object accuracy as IoU.

**Action:** Recompute the manifest: global GT minimum, prediction zero-based
range, category map, part-avg flag, object count, and per-category values. Keep
optional error PLY separate from the metric source.

### Numeric category lookup fails

**Meaning:** A numeric folder is not in the built-in 16-category map.

**Action:** Verify the category list and dataset version. Do not guess a name
or silently omit the category.

## S3DIS failures

### Room is skipped or `pred.npy` is absent

**Meaning:** The legacy evaluator skips rooms without both `label.npy` and
`pred.npy`, so a reported score can be partial.

**Action:** Inventory every expected area/room. Require a successful merge output
for each approved room before scoring. The validator treats absent post-merge
outputs as pending unless strict review requires them; it must never be treated
as proof of an all-room score.

### Merged output length differs from `label.npy`

**Meaning:** A block index range, target room, or merge input is wrong.

**Action:** Stop and identify the offending HDF5 and valid prefix. Recreate the
prediction/index contract. Never resize `pred.npy` or use a different room's
label array.

### Coverage appears as class 0

**Meaning:** Untouched indices and real class-0 labels share a value. A zero
confidence branch can also win a tie at an untouched point.

**Action:** Report branch coverage and index inventory. Review filenames for the
`zero` branch marker and duplicate indices. Do not change class 0 to an ignore
label after the merge.

### IoU division is invalid

**Meaning:** A class has an empty union. The legacy 13-class mean does not
provide a safe policy for this case.

**Action:** Report the empty class/union and stop acceptance unless the evaluator
and reviewer define an explicit policy. Do not drop the class silently.

## ScanNet failures

### Pickle cannot be loaded or has one object instead of two

**Meaning:** The file is not the expected two-object Python-3-compatible test
pickle, or it is not trusted for deserialization.

**Action:** First use the validator without pickle inspection to check HDF5
shape only. If the file is trusted, explicitly add
`--allow-pickle-inspection`; then confirm `xyz_all`/`labels_all` list lengths and
per-room point counts. Do not deserialize an untrusted pickle merely to obtain a
range check.

### Index rank is not `[B, M, 2]`

**Meaning:** The file cannot identify a ScanNet room and point. A rank-2 S3DIS
index map is not interchangeable.

**Action:** Route back to input construction and regenerate the mapping. Do not
interpret the two dimensions as room and point unless the schema says so.

### Point and voxel accuracy disagree unexpectedly

**Meaning:** Voxelization is not point averaging. The fixed voxel size is
`0.0484`; ground truth uses the first point in each voxel and predictions use
majority voting. Label-0 denominators are excluded while correct label-0
numerators remain in the legacy implementation.

**Action:** Reproduce those exact rules and record room-level denominators. Do
not replace them with a standard confusion-matrix implementation while calling
it the same score.

## Semantic3D failures

### Version or scene key is wrong

**Meaning:** The merge has two exact version tables. A typo can otherwise fall
through to the reduced behavior.

**Action:** Use only `full` or `reduced` and compare scene keys, fixed lengths,
and output stems with the artifact reference. Do not infer lengths from the
prediction files.

### No matching scene prediction

**Meaning:** The merge can create an all-default result for a scene with no
matching `_pred` file.

**Action:** Treat it as an incomplete result and stop submission generation.
Check filename key matching and the complete scene inventory.

### Output labels are all or mostly `1`

**Meaning:** Semantic3D output adds one to merged zero-based labels, and
uncovered points also become one. This pattern is not evidence of class-1
performance.

**Action:** Inspect valid index coverage and confidence winners before reading
the submission file. Preserve the zero-based prediction HDF5s as provenance.

### Merge runs out of memory

**Meaning:** Full-scene arrays and HDF5 buffers can require several GB, with the
largest scenes much larger.

**Action:** Stop, check memory and disk, process one scene/result set at a time,
and use an approved destination. Do not reduce arrays by changing scene length
or run the complete dataset as a smoke test.

## Checkpoint, log, and summary confusion

### A checkpoint directory exists but restore fails

**Meaning:** The prefix or its `.index`/data companions are missing, or the
checkpoint belongs to another model/setting.

**Action:** Inspect exact prefix companions and the saved model/setting
provenance. Re-select a matching checkpoint; do not infer compatibility from a
nearby iteration number.

### TensorBoard shows accuracy but evaluator has no score

**Meaning:** Summary scalars describe training or validation graph feeds, not
full benchmark artifacts.

**Action:** Keep summary evidence in the run manifest, then validate predictions
and run the dataset-specific evaluator separately. A TensorBoard event file
cannot replace a merge or submission label set.

## Recovery boundary

If the only blocker is a required TensorFlow/CUDA FPS custom op, route to
segmentation workflows and report `BLOCKED_REQUIRED_BACKEND`. Do not switch to
CPU and claim equivalent segmentation. If all files are structurally valid but
a metric is still questionable, preserve the unverified status and list the
missing dataset/version/checkpoint/coverage evidence for the next run.
