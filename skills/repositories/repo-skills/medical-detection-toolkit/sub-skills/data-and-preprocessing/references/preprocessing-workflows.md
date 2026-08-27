# Preprocessing workflows

[Back to the data-and-preprocessing skill](../SKILL.md) · Related: [data formats](data-formats.md), [loader contracts](data-loader-contracts.md), [utilities](data-utilities.md), [troubleshooting](troubleshooting.md)

Preprocessing is an offline boundary: it converts external/raw data into
small, loader-readable arrays and a manifest. The checked-out examples are
schemas and implementation evidence, not runnable access to the underlying
LIDC-IDRI, PET/CT/TNM, or toy data.

## Shared boundary

A preprocessing implementation should declare, before it runs:

1. source image/annotation format and trust boundary;
2. target spacing, axis order, crop policy, intensity transform, and dtype;
3. whether labels are instance-valued or binary;
4. output filenames and manifest fields;
5. a bounded validation case and a rollback/backup location.

Write image and segmentation with the same spatial transform. Use linear or
higher-order interpolation only for intensities; use nearest-neighbor/order 0
for discrete masks. Preserve source spacing/origin/direction separately if
physical-coordinate evaluation is required.

## LIDC example

`experiments/lidc_exp/preprocessing.py`:

1. Reads `<pid>_ct_scan.nrrd` with SimpleITK and obtains the source array and
   spacing.
2. Resamples image and each annotator ROI to
   `cf.target_spacing=(0.7, 0.7, 1.25)` using `skimage.transform.resize`.
   `resample_array` reverses the spacing order while constructing the target
   shape because the SimpleITK array is z-first.
3. Clips CT to `[-1200, 600]`, converts to float32, and performs global z-score
   normalization.
4. Collects ROI masks, pads missing rater votes with zeros, averages votes,
   suppresses pixels below `0.5`, and assigns each surviving lesion a new
   positive id in `final_rois`. Malignancy labels are averaged over available
   rater scores and stored aligned to those ids.
5. Saves `<pid>_rois.npy`, `<pid>_img.npy`, and a per-patient
   `meta_info_<pid>.pickle` containing `pid`, `class_target`, source `spacing`,
   and `fg_slices`. `aggregate_meta_info` writes `info_df.pickle`.

The `fg_slices` calculation assumes there is at least one foreground voxel;
make that precondition explicit in a new implementation instead of allowing
`np.argwhere(... )[:, 0]` to fail ambiguously. Also check for zero standard
deviation before z-scoring a synthetic or degenerate volume.

LIDC's `pack_dataset.py` can convert arrays in `.npz` files into `.npy` files
and has a `delete_npy` helper. These are storage operations only. They are
explicitly non-runnable from this skill because they can consume substantial
storage or delete source-derived files.

## PET-CT example

`experiments/pet_ct_tnm_classification/preprocessing.py` is a narrow,
selection-based research script, not a general-purpose converter:

1. It finds raw patient directories containing `lsa_pet` under paths containing
   `TNM`.
2. For selected indices only, it reads CT/PET with SimpleITK and a
   `lsa.seg.nrrd` label map with pynrrd. It treats non-background segment names
   as foreground and collapses all retained components to binary `1`.
3. It resamples CT/PET/segmentation to a CT reference, crops z with
   `get_z_crops`, clips/scales CT, z-scores CT and PET, and concatenates the two
   modalities to `(2, z, y, x)` float32.
4. It writes `<pid>_img.npy`, `<pid>_rois.npy`, and appends `pid`, `raw_pid`,
   clinical `class_target`, and `fg_slices` to `info_df.pickle`.

`get_z_crops` uses connected components of `x < -600`, border clearing, size,
center, and recursion thresholds. It can fail when no qualifying slice exists;
never assume it is safe for a new cohort. The source also contains a
normalization expression for PET that should be reviewed carefully before
reuse; test finite values and the intended operator precedence on synthetic
arrays.

`PatientBatchIterator.preprocess_patient` is a separate inference-time path
for external NIfTI CT/PET and is not equivalent to the offline preprocessing
above. It has no ground-truth segmentation in its returned batch.

## Toy example

The toy config is intentionally lightweight and 2D-only. Its loader expects a
manifest row with `pid` and `class_id` and an array file `<pid>.npy` containing
an image plane and segmentation plane. It uses no dynamic 3D resampling or
patch tiling, and its default `patch_size` and `pre_crop_size` are `320 x 320`.
Use it to test a model/data-loader integration with a caller-owned generated
case, not as evidence that a clinical image can be interpreted in the same
axis convention.

## Output handoff

For each case family, record:

```text
source identifier (not a private path)
array filenames and shape/dtype
axis convention before and after loader transpose
intensity range/normalization and target spacing
segmentation mode: instance ids or binary
ROI-id-to-class-target alignment rule
foreground slice convention
manifest schema and split policy
```

Run the bundled validator on a bounded explicit image/segmentation pair after
writing outputs. Use JSON metadata when possible; do not create a new pickle
reader in the validator. Keep raw data and clinical labels out of the runtime
skill tree.
