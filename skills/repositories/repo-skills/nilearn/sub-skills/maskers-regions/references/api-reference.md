# Maskers and Regions API Reference

## Decision Matrix

| Need | Use | Input contract | Output contract | Key checks |
| --- | --- | --- | --- | --- |
| Voxelwise features inside a mask | `NiftiMasker` | 3D/4D Niimg plus optional 3D `mask_img` | 3D -> `(n_voxels,)`; 4D -> `(n_scans, n_voxels)` | Mask is binary, non-empty, same field of view or intentionally resampled. |
| Multiple subjects or runs with one mask | `MultiNiftiMasker` | List of 3D/4D Niimgs | List of arrays, one per input image | `confounds` and `sample_mask` are lists with the same length as `imgs`. |
| Non-overlapping atlas labels | `NiftiLabelsMasker` | 3D integer `labels_img`, optional 3D/4D data | `(n_scans, n_labels_kept)` | Set `background_label`; decide what to do with masked-out labels. |
| Probabilistic or overlapping maps | `NiftiMapsMasker` | 4D `maps_img` where last axis is map index | `(n_scans, n_maps_kept)` | Set `allow_overlap`; watch `resampling_target` and masked maps. |
| Coordinate seeds | `NiftiSpheresMasker` | `seeds=[(x, y, z), ...]`, optional `radius`, optional `mask_img` | `(n_scans, n_seeds)` | Coordinates must be in image space; `inverse_transform` needs `mask_img`. |
| Multi-subject labels/maps | `MultiNiftiLabelsMasker`, `MultiNiftiMapsMasker` | List of images plus shared labels/maps | List of per-image arrays | Parallel with `n_jobs`; per-image confounds/sample masks must align. |
| Split continuous maps into regions | `RegionExtractor`, `connected_regions` | 4D maps or components | 4D regions image, then region signals | Tune threshold, `min_region_size`, `extractor`, and `smoothing_fwhm`. |
| Split disconnected label regions | `connected_label_regions` | 3D labels image | New 3D labels image, optionally names | Labels must be non-negative; `min_size` is in mm³. |
| Learn parcellations | `Parcellations` | List of fMRI images and optional mask/masker | Fitted labels image and transform output | Choose method by scale: `kmeans`, `ward`, `complete`, `average`, `rena`, or `hierarchical_kmeans`. |
| Fast feature clustering | `ReNA` | 2D array `(n_samples, n_features)` plus mask geometry | Reduced feature matrix | `mask_img` must match features unless using test-only dummy behavior. |
| Low-level label/map signal helpers | `img_to_signals_labels`, `img_to_signals_maps`, `signals_to_img_labels`, `signals_to_img_maps` | Already aligned images; no estimator state | Signals plus labels or reconstructed image | No automatic resampling; use when estimator overhead is not needed. |

## Core Masker Classes

| API | Important parameters | Fitted attributes or methods | Notes |
| --- | --- | --- | --- |
| `NiftiMasker` | `mask_img`, `runs`, `smoothing_fwhm`, `standardize`, `standardize_confounds`, `detrend`, `low_pass`, `high_pass`, `t_r`, `target_affine`, `target_shape`, `mask_strategy`, `mask_args`, `dtype`, `memory`, `reports`, `clean_args` | `mask_img_`, `affine_`, `n_elements_`, `fit`, `transform`, `fit_transform`, `inverse_transform`, `generate_report` | `mask_strategy` accepts `background`, `epi`, `whole-brain-template`, `gm-template`, or `wm-template`. |
| `MultiNiftiMasker` | Same as `NiftiMasker` plus `n_jobs` | Same core attributes; `transform` returns a list for a list input | Automatic mask computation uses multi-image mask helpers. |
| `NiftiLabelsMasker` | `labels_img`, `labels`, `lut`, `background_label`, `mask_img`, preprocessing args, `resampling_target`, `strategy`, `keep_masked_labels`, `reports`, `clean_args` | `labels_img_`, `lut_`, `region_atlas_`, `n_elements_`, `labels_`, `region_names_`, `inverse_transform`, `generate_report` | `strategy` accepts `mean`, `median`, `sum`, `minimum`, `maximum`, `standard_deviation`, or `variance`. |
| `NiftiMapsMasker` | `maps_img`, `mask_img`, `allow_overlap`, preprocessing args, `resampling_target`, `keep_masked_maps`, `reports`, `clean_args` | `maps_img_`, `mask_img_`, `n_elements_`, `inverse_transform`, `generate_report` | Extraction uses least-squares map signals; `allow_overlap=False` raises on overlapping non-zero voxels. |
| `NiftiSpheresMasker` | `seeds`, `radius`, `mask_img`, `allow_overlap`, preprocessing args, `reports`, `clean_args` | `seeds_`, `mask_img_`, `n_elements_`, `inverse_transform`, `generate_report` | Without `radius`, extraction is from the seed voxel; overlapping spheres need explicit `allow_overlap=True`. |
| `MultiNiftiLabelsMasker` | Same as `NiftiLabelsMasker` plus `n_jobs` | List-returning multi-image transform | Use when each subject should keep a separate time-series matrix. |
| `MultiNiftiMapsMasker` | Same as `NiftiMapsMasker` plus `n_jobs` | List-returning multi-image transform | Same overlap and resampling rules as `NiftiMapsMasker`. |

## Region APIs

| API | Main purpose | Key parameters | Outputs |
| --- | --- | --- | --- |
| `RegionExtractor` | Threshold and split 4D maps into connected regions, then behave like a `NiftiMapsMasker` | `maps_img`, `mask_img`, `min_region_size`, `threshold`, `thresholding_strategy`, `two_sided`, `extractor`, `smoothing_fwhm`, `allow_overlap` | Fitted `regions_img_`, `index_`, transform output `(n_scans, n_regions)`. |
| `connected_regions` | Functional helper for continuous map splitting | `maps_img`, `min_region_size`, `extract_type`, `smoothing_fwhm`, `mask_img` | `(regions_extracted_img, index_of_each_map)` or `(None, None)` with warning when no regions survive. |
| `connected_label_regions` | Split disconnected components inside each integer label | `labels_img`, `min_size`, `connect_diag`, `labels` | New labels image, and new names if `labels` were provided. |
| `Parcellations` | Learn a parcellation from fMRI images | `method`, `n_parcels`, `mask`, `smoothing_fwhm`, `standardize`, `mask_strategy`, `scaling`, `n_iter`, `n_jobs` | Fitted `labels_img_`, `masker_`, `variance_`, transform/reduction behavior. |
| `ReNA` | Recursive Neighbor Agglomeration reducer | `mask_img`, `n_clusters`, `scaling`, `n_iter`, `threshold` | `labels_`, `n_clusters_`, `sizes_`, reduced arrays. |

## Shape and State Rules

- Niimg maskers accept 3D and 4D image inputs; 4D time is always the samples
  axis in returned arrays.
- Multi-masker `transform(list_of_imgs)` returns a Python list of arrays, not
  one concatenated matrix.
- Labels and maps maskers may drop fully masked regions/maps unless the
  currently deprecated `keep_masked_labels=True` or `keep_masked_maps=True` is
  used; prefer explicit validation of `lut_`, `labels_`, output shape, and
  warnings rather than silently relying on dropped columns.
- `resampling_target="data"` usually keeps extracted signals in data space;
  `"labels"`, `"maps"`, or `"mask"` can increase memory use or change which
  regions survive.
- `generate_report()` reads stored report data from fitted/transformed maskers;
  disable `reports` in non-interactive or dependency-minimal runs.

## Surface Family Overview

Surface maskers mirror the volume concepts for `SurfaceImage` data:
`SurfaceMasker`, `MultiSurfaceMasker`, `SurfaceLabelsMasker`,
`MultiSurfaceLabelsMasker`, `SurfaceMapsMasker`, and `MultiSurfaceMapsMasker`.
Use them only after the task is already in Nilearn surface object space. For
mesh construction, hemisphere part alignment, and volume-to-surface projection,
route to `../surface-workflows/SKILL.md`.
