---
name: data-and-preprocessing
description: "Prepare, inspect, and safely adapt MedicalDetectionToolkit array
  datasets, labels, preprocessing, patching, and batchgenerators pipelines for
  toy, LIDC, and PET-CT-style experiments."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Data and preprocessing

Use this sub-skill when a Researcher must turn a preprocessed medical-image case
into the dictionaries and arrays expected by MedicalDetectionToolkit (MDT), or
when adapting one of the example loaders without silently changing axes, label
semantics, or patch coordinates. This is an operating reference, not a data
acquisition recipe. The repository is legacy and explicitly no longer
maintained; reproduce the contracts below and verify the installed environment
before changing them.

## Operating contract

Given an experiment config `cf`, a logger, a manifest/data directory, and
preprocessed image/segmentation arrays, produce one of these observable
contracts:

- `load_dataset` returns an `OrderedDict` keyed by `pid`. Each value contains
  paths under `data` and `seg`, the `pid`, and a `class_target` list. LIDC and
  PET-CT additionally carry `fg_slices`; toy uses one array path for a packed
  two-plane `[image, segmentation]` file and does not carry foreground-slice
  metadata.
- A training batch contains `data`, `seg`, `pid`, and `class_target`. `data` is
  batched channels-first and `seg` has a singleton segmentation-channel axis.
  The spatial axes are `(x, y)` for 2D or `(x, y, z)` for 3D at the point the
  network sees them; the exact loader transposes are documented in
  [data-formats](references/data-formats.md).
- After `ConvertSegToBoundingBoxCoordinates`, a batch also contains
  `bb_target` and `roi_labels`. Patient iterators preserve patient-level
  targets as `patient_bb_target` and `patient_roi_labels`, plus
  `original_img_shape`; tiled batches additionally carry `patch_crop_coords`.

Before loading a real case, validate a portable image/segmentation pair with
[`validate_preprocessed_case.py`](scripts/validate_preprocessed_case.py). The
validator accepts only `.npy`/`.npz` arrays and optional JSON metadata, has hard
size/voxel bounds, performs no repository imports, and never downloads or
modifies data. Its JSON metadata format is described in
[troubleshooting](references/troubleshooting.md).

## Required workflow

1. **Select the evidence-backed family.** Use the toy loader only for small 2D
   onboarding data; use LIDC for per-patient CT volumes with instance-valued
   ROIs and optional 2D/3D operation; use PET-CT for the two-channel CT/PET
   classification-style example with a binary foreground segmentation. Read
   [preprocessing-workflows](references/preprocessing-workflows.md) before
   changing normalization, resampling, or label creation.
2. **Freeze the manifest contract.** The configured `input_df_name` is normally
   `info_df.pickle`. Its rows must agree with the filenames derived from `pid`.
   Do not infer a different axis order from a filename. Check `class_target`,
   `fg_slices` (where present), and spacing/shape metadata before training.
3. **Validate arrays and metadata.** Use the bundled validator on a copied or
   synthetic case. Never pass arbitrary pickle files to a new utility. The
   source loaders read pandas pickle manifests, so treat them as trusted local
   inputs only and keep their paths outside portable skills.
4. **Construct the generator.** Instantiate the appropriate `BatchGenerator`,
   then use `create_data_gen_pipeline`. Training composes optional mirror and
   `SpatialTransform`; validation/testing uses `CenterCropTransform`; both then
   call `ConvertSegToBoundingBoxCoordinates`. Exact flags and version-sensitive
   signatures are in [data-loader-contracts](references/data-loader-contracts.md).
5. **Check labels after every geometric transform.** Image and segmentation
   must be transformed together. Use interpolation order 0 / background 0 for
   segmentation. Confirm the resulting `bb_target` coordinates fit the
   post-transform patch and that class labels still correspond to ROI ids.
6. **Record reversible customization.** Keep a small manifest schema note and
   a before/after shape example for every custom loader. If a change affects
   axes, label mode, patch size, or channel count, update config and tests
   together rather than patching a downstream model.

## Label and geometry rules

- Background is label `0`; positive integer ROI ids are foreground. In LIDC,
  each nonzero ROI id is an individual lesion and `class_target` is aligned to
  those ids after the preprocessing script's `rix` assignment. Do not relabel
  ROIs without updating the aligned class vector.
- A **pixelwise instance map** has increasing ROI ids and needs
  `get_rois_from_seg_flag=False`. A **binary map** has foreground `1` and does
  not identify individual lesions; use `get_rois_from_seg_flag=True` so the
  batchgenerators converter performs connected-component labeling. The PET-CT
  pipeline uses this binary mode. A box-only source must first be represented
  as a pseudo-mask if it is to go through the same spatial augmentation path.
- `class_specific_seg_flag` controls whether converted segmentation targets
  preserve class-specific channels/labels. It is not a substitute for making
  a binary mask into instance ids. Check `cf.head_classes` and
  `cf.num_seg_classes` when changing it.
- The loader may return no foreground in a sampled patch even when the patient
  has lesions. Do not treat an empty patch as a corrupt case; distinguish it
  from an invalid all-negative patient or an out-of-range `fg_slices` entry.
- Coordinates are local to the current patch. Patient-level targets must be
  retained separately when tiling so predictions can be mapped/consolidated.

## Dimensions, channels, and patching

- Toy is 2D only: its packed case stores image at index `0` and segmentation at
  index `1`; `BatchGenerator` adds a batch axis and a singleton data/seg channel
  axis. It uses `320 x 320` pre-crop and patch settings in the supplied config.
- LIDC preprocessing writes `(z, y, x)` image and ROI arrays. The loader
  transposes them to `(y, x, z)` before sampling; 2D mode selects a z slice,
  while 3D mode retains the volume. The supplied config uses `300 x 300`
  pre-crops / `288 x 288` 2D patches, or `156 x 156 x 96` pre-crops /
  `128 x 128 x 64` 3D patches, and enables 2D-to-3D prediction merging.
- PET-CT preprocessing writes a two-channel image `(c, z, y, x)` and a binary
  `(z, y, x)` mask. The loader transposes the image to `(c, y, x, z)` and
  samples 2D slices or 3D volumes. The supplied config is 3D with
  `280 x 280 x 48` pre-crops and `192 x 192 x 32` patches, two channels, and
  2D-to-3D merging enabled if 2D is selected.
- If an input is smaller than the configured pre-crop or patient patch, the
  loaders call `pad_nd_image`; padding is centered and defaults to constant
  zero in the shown paths. If larger, training samples a pre-crop (with
  foreground-biased sampling) and patient inference creates a coordinate grid
  using `get_patch_crop_coords`. A patch size of `1` in z means one patch per
  slice, not a three-dimensional slab.
- `n_3D_context` adds neighboring slices as channels in 2D mode. It changes
  `cf.n_channels` and requires matching model input configuration; padding is
  applied at the volume boundary. Do not enable it without checking channel
  count and the context coordinate adjustment.

## Safety boundaries

- The example raw data roots, mounted paths, `rsync` copies, and cloud/server
  branches are environment-specific. LIDC-IDRI, PET/CT/TNM, and the toy data
  directories are external datasets; the PET/CT paths and clinical labels may
  be private. Do not claim access, redistribute them, or run acquisition from
  this skill. The supplied examples are evidence of schema and behavior only.
- `experiments/lidc_exp/pack_dataset.py` and
  `utils/dataloader_utils.py::unpack_dataset`/`delete_npy` are storage helpers,
  not safe validation steps. Packing/unpacking can create many files and
  `delete_npy` is destructive. Treat pack, delete, `rsync`, multiprocessing
  preprocessing, and raw-data conversion as **non-runnable** unless a user
  explicitly reviews paths, backups, and a bounded dry run outside this skill.
- Do not run native final cases, download data, or import this operating graph
  during construction. Use signatures/import checks and bounded synthetic
  validator fixtures only.

## References and bundled script

- [Data formats and array axes](references/data-formats.md)
- [Data-loader and batchgenerators contracts](references/data-loader-contracts.md)
- [Preprocessing workflows](references/preprocessing-workflows.md)
- [Data utilities: padding, tiling, balancing, packing boundaries](references/data-utilities.md)
- [Troubleshooting and safe customization](references/troubleshooting.md)
- [Standalone preprocessed-case validator](scripts/validate_preprocessed_case.py)

All references link back here and to the other references so the graph remains
usable when a Researcher opens a leaf directly. Source evidence is the checked-
out `README.md`, the three experiment `configs.py`/`data_loader.py` pairs,
LIDC `preprocessing.py`/`pack_dataset.py`, PET-CT `preprocessing.py`, and
`utils/dataloader_utils.py`.

## Verification gate

Accept a customized data path only when: (a) the three example loaders import
with the documented loader dependency/API variant; (b) the validator passes a
bounded synthetic valid case and rejects mismatched shapes, non-integral labels,
or oversized input;
(c) the manifest-to-file naming and `class_target`/ROI semantics are recorded;
and (d) no native dataset case or destructive helper was run. Unresolved
backend, private-data, axis, or label ambiguities stay explicit in the handoff.
