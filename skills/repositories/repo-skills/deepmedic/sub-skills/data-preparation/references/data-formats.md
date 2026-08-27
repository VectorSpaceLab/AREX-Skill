# DeepMedic data contracts

This reference is the data-only contract for DeepMedic 0.8.4. It deliberately
omits model architecture, optimization, session execution, and checkpoint
inference. Those topics belong to
[model architecture](../../model-architecture/SKILL.md),
[training](../../training/SKILL.md), and
[inference](../../inference/SKILL.md).

## NIFTI volumes and the subject unit

DeepMedic reads NIFTI images. A subject is one aligned set of modality
channels, with an optional ground-truth label volume, optional ROI mask, and
optional sampling weight maps. A channel is a modality/sequence, not a
spatial axis. Preserve the channel order used by the model: the first item in
`channelsTraining`/`channels` is channel 0, the second is channel 1, and so on.
The number of channel list files must match the model's configured number of
input channels.

The source I/O function is:

```text
load_volume(filepath)
```

It returns a NumPy array. A 2-D NIFTI is expanded to `(x, y, 1)`. A 4-D NIFTI
is accepted only when its fourth dimension is exactly 1, and that singleton
axis is removed. A 4-D image with more than one volume is rejected. Plan on
3-D arrays after loading. NIFTI headers and affines are not resampled by
DeepMedic; prepare and register data before handing it to the application.

For every subject:

- Every real modality file, label file, and ROI file must be readable NIFTI.
- All present volumes must have the same voxel-array shape after the 2-D and
  singleton-4-D interpretation above.
- They must describe the same anatomical grid and be co-registered. Matching
  array dimensions alone does not prove co-registration. Compare orientation,
  origin, and affine/header metadata with an imaging tool; the bundled
  validator can optionally compare affines.
- Use one voxel size throughout the database. This lets the same convolution
  kernels represent the same physical scale for every subject. The bundled
  validator checks voxel sizes within each subject and against the first case;
  investigate any mismatch rather than hiding it with a large tolerance.
- Do not silently transpose, crop, or resample only one modality. If a
  resampling or crop is needed, apply the same spatial operation to all
  subject-associated volumes, using label-safe interpolation for labels and
  masks.

The image data type may be floating point or integer. Labels and masks are
loaded by the sampling code and, when non-integer, DeepMedic rounds and casts
them to `int16` with a warning. Do not rely on this conversion: write labels
as integer-valued data and validate them before a run.

## List-file manifests (the classic configuration)

A channel parameter is a Python-style list of list-file paths:

```text
channelsTraining = ["trainChannels_modalityA.cfg", "trainChannels_modalityB.cfg"]
channelsValidation = ["validationChannels_modalityA.cfg", "validationChannels_modalityB.cfg"]
channels = ["testChannels_modalityA.cfg", "testChannels_modalityB.cfg"]
```

Each channel list contains one image path per subject, in exactly the same
subject order. The corresponding entries across all channel lists form one
subject. A labels list (`gtLabelsTraining`, `gtLabelsValidation`, `gtLabels`)
and an ROI list (`roiMasksTraining`, `roiMasksValidation`, `roiMasks`) must
therefore have the same number of entries as the channel lists they
accompany. Labels are required for training; they are optional for testing
and are used to report metrics when present. ROI lists are optional. Without
an ROI, sampling/inference considers the whole volume.

A list file is line-oriented:

- Blank lines and lines beginning with `#` are ignored.
- Other nonempty lines are one path, stripped of surrounding whitespace.
- A relative image path is resolved relative to the directory containing its
  list file, not relative to the process's current directory. Keep nested
  manifests self-contained and do not depend on where the launcher happens
  to be called.
- In a channel list only, a line containing exactly `-` means that modality
  is absent for that subject. The loader makes a zero-filled channel. Use it
  only deliberately, and ensure another real channel provides the subject's
  spatial shape. `-` is not valid as a label or ROI entry.
- Paths may use `.nii` or `.nii.gz`; the loader's dimensional rules above
  still apply.

The parser helpers that implement these semantics are:

```text
parse_filelist(filelist_path, make_abs=False)
parse_fpaths_of_channs_from_filelists(list_of_filelists, abs_path_root)
abs_from_rel_path(pathGiven, absolutePathToWhereRelativePathRelatesTo)
```

`parse_filelist(..., make_abs=True)` resolves each relative item against the
list file's directory. `parse_fpaths_of_channs_from_filelists` reads one list
file per channel, then transposes the result into
`[[case0_channel0, case0_channel1, ...], ...]`. If list lengths disagree,
the transpose can truncate or later processing can fail; validate lengths
before launching a session. The runtime has a helper for this purpose named
`scripts/validate_nifti_manifest.py`.

Training can additionally take one list file per sampling category through
`weightedMapsForSamplingEachCategoryTrain` (and the validation equivalent).
These files are also one entry per subject. Weight maps must be non-negative;
zero maps cannot supply samples for a category. Weight maps are outside this
sub-skill's required validator, so validate their shape and non-negativity
before use.

Prediction-name lists are different: they contain output name tokens, not
input image paths. They are not used as modality manifests and should not be
validated as NIFTI paths.

## CSV/dataframe input

Version 0.8.4 also contains a dataframe path for training, validation, and
testing. It is supported by the parser even though the general documentation
mostly demonstrates list files. Set `dataframe_train`, `dataframe_val`, or
`dataframe` in the relevant configuration instead of the classic channel
parameters. The CSV is read with pandas and each path is resolved relative to
the directory containing that CSV.

Required and optional column signals are:

| Column | Meaning | Required |
|---|---|---|
| `channel_<name>` | One modality path per row/subject | At least one; channel columns are sorted alphabetically |
| `ground_truth` | Label path for that row | Required for training and validation; optional for testing |
| `roi_mask` | ROI path for that row | Optional |
| `prediction_filename` | Output-name token for that row | Optional; used when saving validation/test outputs |

The implementation collects every column whose name starts with
`channel_` and sorts those names lexicographically. Name channels so this
ordering is unambiguous (for example, `channel_01_t1` before
`channel_02_flair`, rather than relying on `channel_1`/`channel_10`). Values
are joined to the CSV directory unless already absolute. A training dataframe
without `ground_truth` is an error; a test dataframe may omit it. A dataframe
row is the subject unit, so all paths in one row must refer to the same grid.
Do not mix a dataframe source and list-file source for one session without
checking which configuration branch is active.

## Labels and classes

Labels represent classes by integer index:

- background is exactly `0`;
- foreground/classes are `1, 2, ...` with no gaps across the task;
- do not encode classes as values such as `0, 10, 20`;
- the model's number of output classes includes background, so the valid range
  for `N` configured classes is `0 <= label < N`.

The runtime check in `sampling.py` rejects a loaded label greater than
`num_classes - 1`. It does not by itself guarantee that a task's dataset
uses every intermediate class. Check the union of labels across all training
subjects and confirm it is `{0, 1, ..., K}` for the intended task. A subject
may legitimately lack a class that exists in another subject; do not require
all classes in every single subject.

ROI masks are treated as boolean by `roi_mask > 0`: positive voxels are inside
and zero/non-positive voxels are outside. A missing ROI means an all-true mask
for normalization and whole-volume sampling/inference. A provided ROI must
have the same shape and grid as its subject's channels. It should not be an
accidentally empty mask unless the downstream sampling plan explicitly
handles that case.

## Normalization

DeepMedic's exact public normalization entry point is:

```text
normalize_zscore_subj(log, channels, roi_mask, prms,
                      verbose_lvl=0, job_id='', in_place=True)
```

`channels` is shaped `[n_channels, x, y, z]`; `roi_mask` is `[x, y, z]` or
`None`; `prms` is a dictionary. The wrapper
`normalize_int_of_subj(log, channels, roi_mask, prms, job_id)` applies the
configured normalizers. Current 0.8.4 code implements z-score normalization.

The z-score dictionary supports:

```text
{
  'apply_to_all_channels': True or False,
  'apply_per_channel': None or [bool, ...],
  'cutoff_percents': None or [low, high],
  'cutoff_times_std': None or [low, high],
  'cutoff_below_mean': True or False
}
```

`apply_to_all_channels=True` and a non-`None` `apply_per_channel` are
incompatible. Otherwise `apply_per_channel` must have exactly one boolean per
channel. If no channels are selected, no normalization is applied. With no
ROI, statistics use the whole volume; with an ROI, statistics are computed
from positive ROI voxels. Optional percentile, standard-deviation, and
below-image-mean cutoffs exclude voxels from the statistics, but the returned
normalization is applied to the complete channel array. The operation is
in-place by default; use `in_place=False` when retaining the source array is
important.

The implementation divides by the selected standard deviation. A constant or
empty selected ROI can therefore produce invalid values; reject empty/near-
constant normalization regions before a run or choose a preprocessing policy
that handles them. The README recommendation is zero mean/unit variance
within the relevant ROI, but the shipped example files already use names such
as `Flair_subtrMeanDivStd`, so avoid normalizing twice without an explicit
reason. Validate post-normalization statistics on representative subjects.

## Safe preflight

Run the bundled validator against every channel list in order. It resolves
list-relative paths, checks existence, loads NIFTI headers, accepts the same
2-D/singleton-4-D shape conventions as DeepMedic, checks per-case shape and
voxel-size agreement (including the database-wide voxel-size baseline), and
optionally checks affines and label ranges. It does not import DeepMedic,
change any file, resample data, or write outputs. Add
`--read-data` when compressed payload corruption is a concern. Add
`--num-classes N --require-contiguous-labels` for a dataset-level label gate.
The validator does not validate sampling weight maps or CSVs; validate those
separately using the contracts above.
