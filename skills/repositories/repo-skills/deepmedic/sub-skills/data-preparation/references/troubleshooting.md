# Data preparation troubleshooting

Use this as a diagnosis tree before changing model, training, or inference
settings. Keep the original data immutable while isolating a failure.

## Manifest and path failures

### “Required channels” or no channel files

1. Confirm the number of entries in the configuration's `channelsTraining`,
   `channelsValidation`, or `channels` list equals the intended number of
   modalities and the model's input-channel count.
2. Open each referenced list file. It must have one nonempty data path (or an
   intentional `-` channel placeholder) per subject.
3. Remember that a relative path inside a list is relative to that list file,
   while a relative list-file path in a Python configuration is relative to
   the configuration file. Do not resolve either relative to the shell's
   current directory by intuition.
4. Run `scripts/validate_nifti_manifest.py --help`, then pass one
   `--channel-list` for each modality. The error names the missing manifest or
   input file.

A line containing `-` is a special zero-filled **channel** entry. It is not a
portable “missing file” marker for labels or ROIs. If every channel for a
subject is `-`, there is no shape from which DeepMedic can construct the
subject and the bundled validator rejects it.

### Different case counts or cases paired incorrectly

Every channel list, labels list, and ROI list is positional. Case 7 in every
list must be the same subject; filenames are not used to join rows. Count the
non-comment, nonblank lines. Do not sort one list independently after creating
it. If a channel count error appears during parsing, inspect for blank lines,
comment formatting, accidental headers, and a path split across lines.

For CSV input, one row is one subject. Check that all `channel_` columns are
present on every row and remember that the parser sorts channel column names
alphabetically. `channel_10` sorts before `channel_2`; use zero-padded names or
an explicit naming convention. `ground_truth` is required for training and
validation but can be omitted for testing. `roi_mask` and
`prediction_filename` are optional.

## NIFTI load and dimensional failures

### NIFTI cannot be loaded

Check that the path points to a NIFTI file rather than a sidecar (`.json`,
`.bval`, `.index`, or another output), that compressed files can be read, and
that the file is not a partially copied archive. Run the validator with
`--read-data` to force the image payload to be read, not just the header.
Inspect the reported file before replacing it. Do not “fix” the manifest by
renaming a non-NIFTI file.

DeepMedic accepts a 2-D image by adding a singleton z-axis. It accepts a 4-D
image only when the fourth dimension is 1 and removes that dimension. A true
multi-volume 4-D image is not a single channel for this interface; split or
convert it deliberately before listing it.

### Shape mismatch within a subject

A mismatch between two modalities, a label, or an ROI means their voxel grids
cannot be indexed together. Confirm that all files were generated from the
same crop, orientation, and resampling operation. Compare NIFTI shape,
affine, orientation, and voxel sizes. Re-register/resample the complete
subject set using a label-safe method, then regenerate the manifest. Do not
silence this by disabling input checks.

A mismatch between subjects is not automatically an error for array shape;
subjects may have different matrix dimensions. Every subject's own modalities,
labels, masks, and weight maps must agree. The configured network and sampling
plan must still fit each subject after any padding policy.

### Voxel size mismatch

DeepMedic's documentation requires one voxel size across the database so a
kernel corresponds to the same physical structure for every subject. Header
shape equality is not enough. Compare the first three NIFTI zooms (after any
intentional resampling), including units. Fix the data preprocessing and
revalidate rather than relying on a tolerance that hides a real spacing
change. A voxel-size mismatch within a subject or against the first case is a
hard error in the bundled validator. Its default tolerance is `1e-5` header
units; adjust it only for a known, documented floating-point header
discrepancy.

### Same shape but not co-registered

The current loading/sampling path indexes arrays by voxel coordinate; it does
not perform registration. Equal shapes can still have different orientation,
origin, handedness, or field-of-view. Use an external medical-image QA step to
compare affines and visual overlays. The bundled validator's `--check-affine`
flag is a useful strict screen, but affine equality is evidence, not a full
clinical registration assessment. If intentional transforms differ, document
and apply them consistently before using the files.

## Label and ROI failures

### Invalid labels or class count errors

Labels must use background `0` and consecutive integer class ids. For a model
with `N` output classes, all labels must satisfy `0 <= label < N`; background
is included in `N`. A runtime error saying a label exceeds the configured
class count means either the labels contain an unexpected value or the model
configuration does not describe the task. Inspect the unique values across
all label volumes. Values such as `0, 10, 20` are not accepted class ids.

The sampling loader rounds non-integer labels to `int16`, but this warning can
hide an export error. The bundled validator treats non-integer labels as an
error so the correction is explicit. An individual subject may not contain
every class; require contiguous ids across the dataset, not within each case.
Use `--num-classes N --require-contiguous-labels` for this gate.

Negative labels, NaN/Inf labels, an empty label file, or a label shape/grid
mismatch should be corrected at the source. Do not cast them blindly.

### Empty or wrong ROI

A positive ROI voxel is inside the mask; absent ROI means whole-volume
processing. A provided ROI with no positive voxel can leave no valid sampling
locations and can make ROI-based normalization undefined. Confirm its unique
values, shape, voxel size, affine, and anatomical extent. Make sure a binary
mask was not accidentally exported as a probability map with unexpected
scaling. If whole-volume behavior is intended, remove the ROI parameter/list
instead of supplying an empty mask.

The sampling loader also rounds non-integer ROI values to `int16` and later
uses `roi_mask > 0`. Treat that conversion as a warning, not as a data-cleaning
strategy.

## Normalization failures

### Z-score produces NaN/Inf or implausible intensity

`normalize_zscore_subj` computes statistics from positive ROI voxels, or from
the full volume when `roi_mask is None`. Percentile and standard-deviation
cutoffs further reduce the voxels used for statistics. An empty ROI, an ROI
that excludes all voxels after cutoffs, or a constant selected region can make
the standard deviation zero. Check the selected ROI and cutoff ranges on a
small fixture before processing the full dataset.

Use exactly one mode: set `apply_to_all_channels=True` with
`apply_per_channel=None`, or set `apply_to_all_channels=False` and supply a
boolean list whose length equals the number of channels. A configuration that
sets both modes is rejected. `verbose_lvl=1` logs per-subject timing and
applied normalizers; `verbose_lvl=2` also logs channel statistics.

The function mutates `channels` by default (`in_place=True`). If a later
comparison needs the original array, call it with `in_place=False` and retain
the returned array. Normalization changes all voxel values, including outside
the ROI; the ROI controls statistic estimation, not the write mask.

### Data was already normalized

The example data names indicate pre-normalized channels, while the runtime
normalizer is optional and disabled unless configured. Applying z-score a
second time can change the intended distribution, especially with cutoffs.
Record whether normalization occurred during export and whether the
configuration applies it at load time. Compare ROI mean/std before and after
on representative subjects.

## Validator outcomes and limits

A successful validator run means list lengths, path existence, NIFTI header
loading, accepted dimensionality, per-case shape, and per-case voxel-size
agreement passed. With label options it also means the requested label checks
passed. It does not prove clinical registration, intensity quality, sampling
weight-map shape/non-negativity, CSV parser behavior, or that a model's
receptive field fits every volume. Those remain explicit preflight checks.

The validator never writes, resamples, casts, deletes, or normalizes input
files. If it fails, preserve the error and repair the manifest or source data;
do not disable checks merely to start a session.
