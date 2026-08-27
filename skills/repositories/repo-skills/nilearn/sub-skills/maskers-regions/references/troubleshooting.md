# Maskers and Regions Troubleshooting

| Symptom | Likely cause | Fix |
| --- | --- | --- |
| Empty mask or `n_elements_ == 0` | Automatic mask strategy is wrong for the image intensity/background pattern, or a provided mask is empty after binarization/resampling | Provide a known-good `mask_img`, switch `mask_strategy` to `epi` or a template strategy, tune `mask_args`, and inspect `masker.mask_img_` or a report. |
| `Unknown value of mask_strategy` | Typo or deprecated strategy name | Use `background`, `epi`, `whole-brain-template`, `gm-template`, or `wm-template`. |
| Label columns are fewer than expected | Some labels are background, outside `mask_img`, lost during resampling, or dropped because `keep_masked_labels=False` | Compare unique label values, `background_label`, `masker.lut_`, `masker.labels_`, and output shape; adjust mask/resampling or consciously handle dropped labels. |
| Background appears as a region | `background_label` does not match the atlas value or labels/LUT include background inconsistently | Set `background_label` to the atlas background value and align `labels` or `lut` with image indices. |
| `No label left after resampling the labels image` | Atlas labels were resampled into data space with incompatible affine/shape or too coarse a grid | Try `resampling_target="labels"`, provide data in atlas space, or use a less aggressive target resolution. |
| Maps overlap error | `allow_overlap=False` but maps have shared non-zero voxels, possibly introduced by resampling | Use `allow_overlap=True` for probabilistic maps, or threshold/binarize/resample maps explicitly before fitting. |
| `No map left after applying mask` | `mask_img` removes every non-zero voxel in `maps_img` | Check field of view, affine, and mask coverage; use `resampling_target` deliberately and inspect map-mask overlap. |
| Wrong 3D/4D input behavior | A 3D image returns one feature vector while 4D returns samples by features | Normalize inputs before pipeline use; wrap single maps consistently and assert `array.ndim` and shape. |
| Confounds length mismatch | Confounds rows do not match original number of scans, or multi-masker confounds outer length does not match image list length | Validate `confounds.shape[0] == n_scans` before scrubbing; for multi maskers pass `confounds=[...]` and `sample_mask=[...]` with one item per image. |
| Filtering error with `low_pass` or `high_pass` | Temporal filtering needs sampling interval | Pass `t_r` in seconds whenever using temporal filters. |
| `runs` error or unexpected standardization | `runs` length does not match scans or run labels are missing for multi-run data | Pass a 1D run vector with one label per scan so detrending/cleaning can happen per run. |
| `inverse_transform` shape error | Signal columns do not match fitted voxels, labels, maps, or seeds | Use the same fitted masker for transform and inverse transform; assert `signals.shape[1] == masker.n_elements_` for 2D arrays. |
| Sphere inverse transform asks for a reference | `NiftiSpheresMasker` was built without `mask_img` | Provide `mask_img` at construction when inverse transformation is required. |
| Seed extraction gives empty or wrong voxels | Seed coordinates are in voxel index space instead of world coordinates, or outside the mask | Convert coordinates to the image world space, verify affine, and plot/report seed positions. |
| Region extraction returns no regions | Threshold too strict, `min_region_size` too large in mm³, or map values are sparse/noisy | Lower threshold, lower `min_region_size`, switch `extractor`, or tune `smoothing_fwhm` to map resolution. |
| `connected_label_regions` rejects labels | Labels image contains negative values or label names count does not match unique non-background labels | Recode labels to non-negative integers and pass names excluding background with the correct count. |
| `resampling_target` surprises memory or output columns | Using `"maps"`, `"labels"`, or `"mask"` changes final grid and can alter retained regions | Prefer `"data"` for extraction unless a target atlas/mask space is required; record expected shape and affine. |
| Report generation fails in a minimal environment | Optional plotting/report dependencies or display backend are unavailable | Set `reports=False` for extraction, or route dependency/backend setup and figure export details to `../plotting-reporting/SKILL.md`. |
| Report is blank or warns about missing data | `generate_report()` called before enough fit/transform data were stored | Call `fit(imgs)` or `fit_transform(imgs)` with `reports=True` before generating the report. |

## Debug Checklist

1. Print or assert each input image's `shape`, `affine`, and dimensionality.
2. Fit the masker, then inspect fitted attributes such as `mask_img_`,
   `labels_img_`, `maps_img_`, `lut_`, `labels_`, `seeds_`, and `n_elements_`.
3. Assert transform output shape before downstream modeling:
   `(n_scans_after_sample_mask, expected_features)`.
4. Validate confounds and sample masks before passing them to the masker.
5. Disable reports while debugging extraction; re-enable reports only after the
   numerical pipeline is correct.

## Synthetic Usability Cases for Verification

- **Masked atlas with missing labels:** Build a labels image with three labels,
  apply a mask that removes one label, and require the future agent to explain
  `background_label`, `keep_masked_labels`, `lut_`, and downstream label-name
  alignment.
- **Multi-run inverse sanity:** Build two short 4D runs with per-run confounds
  and `runs`, extract with a fitted masker, verify output rows after optional
  `sample_mask`, then inverse-transform one row and compare shape/affine to the
  fitted mask.
