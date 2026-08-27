# Experimental Imaging Troubleshooting

Use this guide when `squidpy.experimental` SpatialData image workflows fail or produce surprising masks, tiles, features, stain outputs, QC tables, or plots.

## Experimental API Volatility

Symptoms:

- An import path, enum, parameter, or output column differs across Squidpy versions.
- A task found an example using a private module such as `squidpy.experimental.im._...`.

Fixes:

- Import public APIs through `import squidpy as sq` and `sq.experimental.im`, `sq.experimental.tl`, or `sq.experimental.pl`.
- Run `scripts/experimental_imaging_smoke.py` to confirm public imports, signatures, and parameter dataclasses in the active install.
- Avoid private imports except for debugging source behavior. Generated user workflows should call the public re-exported names.
- Keep examples defensive: explicit keys, explicit `scale`, no assumed default output key when the next step depends on it.

## SpatialData Key Ambiguity

Symptoms:

- `KeyError` or `ValueError` says an image, labels, shapes, or table key was not found.
- A plotting function runs but shows no scores or wrong regions.
- A downstream step reads the wrong tissue mask or QC table.

Fixes:

- Before each workflow, inspect available keys:

```python
print("images", list(sdata.images))
print("labels", list(sdata.labels))
print("shapes", list(sdata.shapes))
print("tables", list(sdata.tables))
```

- Pass `image_key`, `labels_key`, `shapes_key`, `spots_key`, `tissue_mask_key`, `table_key_added`, and `qc_table_key` explicitly.
- Use unique output names such as `image_tissue`, `image_tiles`, `cells_qc`, and `he_normalized`.
- Inspect linked table metadata before plotting: `sdata.tables[key].uns.get('spatialdata_attrs')`.

## Scale And Multiscale Selection

Symptoms:

- Masks appear shifted or resized relative to images.
- A workflow is slow or memory-heavy because it materializes full-resolution data.
- `scale="auto"` picks a surprising level.

Fixes:

- Use `scale="auto"` for exploratory tissue detection and stain fitting, then record the resolved behavior in reproducible pipelines.
- Use explicit scales such as `scale="scale0"` when output resolution matters or when matching a known labels pyramid.
- For stain fitting and `estimate_white_point`, keep the sampled scale coarse because the fit or median materializes a bounded image level.
- For normalization and decomposition, `scale="auto"` favors the finest output while computing source statistics on a coarse level; ensure output image size is expected.
- For labels, choose the labels scale closest to the target image. If in doubt, compare `sdata.images[image_key]` and `sdata.labels[labels_key]` dimensions at the selected scale.

## Mask Or Label Coordinate Mismatch

Symptoms:

- Tiles are mostly `background` despite visible tissue.
- `qc_image` tissue classification is wrong.
- `calculate_image_features` drops cells or assigns implausible features.
- Tiling QC scores only a subset of labels or produces many NaNs.

Fixes:

- Confirm image and labels share a coordinate system or equivalent transforms.
- Check mask dimensions against the image scale used by the function.
- Run `detect_tissue` explicitly and pass the resulting `tissue_mask_key` instead of relying on implicit default mask creation.
- Use `align_mode="strict"` in feature extraction during debugging so mismatches fail loudly.
- For label masks, verify background is `0` and cell ids are positive integers.
- For very small objects, lower `TilingQCParams(min_area=...)` only after confirming labels are at the intended resolution.

## Tissue Detection Problems

Symptoms:

- Otsu detects background as tissue.
- Slide borders or fiducials become tissue.
- Tiny tissue islands are removed or holes remain.
- WEKA-like detection is slow or unavailable.

Fixes:

- Set `channel_format` explicitly for nonstandard channel layouts.
- Use `BackgroundDetectionParams` to mark which corners are true background.
- Set `corners_are_background=False` only when corners are not reliable background samples.
- Use `border_margin_px` to remove frame artifacts; pass `(top, bottom, left, right)` for asymmetric frames.
- Tune `min_specimen_area_frac`, `close_holes_smaller_than_frac`, and `mask_smoothing_cycles` carefully on a preview or small image.
- Use `method="felzenszwalb"` with `FelzenszwalbParams` when global thresholding is unstable.
- Treat `method="weka"` as heavier and dependency-sensitive; start with a smaller image, fixed `random_state`, and conservative `n_samples`.

## Weka Parameters And Model Availability

Symptoms:

- Weka detection fails on imports or classifier features.
- Runtime is unexpectedly high.
- Results vary between runs.

Fixes:

- Confirm scikit-image and scikit-learn are importable in the target environment.
- Use `WekaParams(random_state=0)` for reproducible pseudo-labeling and random forest behavior.
- Reduce `rf_estimators`, `rf_max_samples`, or `refine_n_samples_per_class` for smoke tests or previews.
- Keep `pseudo_min_pixels` high enough to avoid fitting from a nearly empty tissue seed.
- Fall back to `method="otsu"` or `method="felzenszwalb"` if WEKA dependencies or runtime are not acceptable.

## Tiling Thresholds And Output Shapes

Symptoms:

- Too many tiles are classified as `partial_tissue` or `background`.
- Tiles do not cover the desired inference region.
- Spot-centered tiles have unexpected sizes.

Fixes:

- For strict inference, keep `min_tissue_fraction` high; for inclusive review/QC, lower it to include partial tiles.
- If `center_grid_on_tissue=True`, pass an explicit `image_mask_key` or `tissue_mask_key`; otherwise the grid may be centered on an automatically generated mask.
- Remember `tile_size` is `(height, width)` in full-resolution pixels for `make_tiles`.
- For `make_tiles_from_spots`, inspect spot geometry and vertical spacing before trusting the inferred tile size.
- Set `preview=False` in scripts and render previews separately in notebook/interactive sessions.

## Image QC Metric Errors

Symptoms:

- H&E metrics fail on non-H&E or non-RGB images.
- `outlier_threshold` raises a validation error.
- QC table exists but plot cannot find metrics.

Fixes:

- Set `is_hne=False` for fluorescence or generic multichannel images and choose non-H&E metrics explicitly.
- Use `QCMetric` enum members rather than free-form strings when constructing metric lists.
- Keep `outlier_threshold` strictly between `0` and `1`.
- If plotting fails, confirm `sdata.tables[f"qc_img_{image_key}"]` exists and has `.uns['qc_image']` metadata.
- If tissue-aware outlier detection is wrong, run `detect_tissue` separately and pass `tissue_mask_key`.

## Feature Extraction Drops Or Invalid Values

Symptoms:

- `features=None` raises an error.
- `cpmeasure:*` feature names raise `NotImplementedError`.
- Feature values are zero or NaN.
- Large cells at tile boundaries are missing or duplicated.

Fixes:

- Always pass explicit feature groups such as `['skimage:morphology']` or `['squidpy:summary']`.
- Do not use `cpmeasure:*` flags; they are recognized but not implemented.
- Set `invalid_as_zero=False` during debugging to expose invalid feature calculations as NaN.
- Increase `overlap_margin` when cells are large relative to `tile_size`; `overlap_margin="auto"` is usually safer than `0`.
- Ensure requested `channels` exist in the image element. If names are unavailable, inspect channel coordinates or use defaults cautiously.
- Use `n_jobs=1` until key/scale alignment is verified.

## Stain Validation Errors

Symptoms:

- `fit_stain_reference` says no tissue mask exists.
- `StainReference` rejects shape, method, white point, `mu`, or `sigma` values.
- Macenko/Vahadane fitting raises a stain-fitting or angle-gate error.
- Normalization would overwrite an existing image key.

Fixes:

- Run `detect_tissue` first and pass `tissue_mask_key` to every stain API.
- Use `StainReference(method="reinhard", mu=..., sigma=...)` only for Reinhard; do not pass a stain matrix or white point.
- Use `StainReference(method="macenko" or "vahadane", stain_matrix=(3,3), white_point=(3,))` for decomposition methods.
- Keep decomposition white points strictly positive and finite.
- Use `MacenkoParams(alpha=..., beta=...)`, `VahadaneParams(beta=..., lambda1=..., n_iter=..., random_state=...)`, or matching dict fields only.
- If H/E vectors fail the canonical angle gate, inspect the tissue mask, image channel order, background, and `max_angle_deg` before relaxing validation.
- Choose a fresh `image_key_added`; normalization and decomposition validate target keys to avoid silent overwrites.

## Background And White-Point Assumptions

Symptoms:

- Normalized background is tinted.
- `estimate_white_point` gives implausible values.
- Decomposition concentration maps are dominated by background.

Fixes:

- Keep `preserve_background=True` in `normalize_stains` unless full-frame color transfer is required.
- Use `estimate_white_point` only when non-tissue background is truly not full white; otherwise default dtype-aware full white is usually safer.
- Ensure the tissue mask is not inverted: `estimate_white_point` samples non-tissue pixels, while fitting uses tissue pixels.
- Do not estimate white point from a fine whole-slide scale unless memory is intentionally provisioned.
- Inspect the residual concentration map from `decompose_stains` to identify extra chromogens, artifacts, or poor stain-basis fits.

## Tiling QC And Stitching Issues

Symptoms:

- `calculate_tiling_qc` marks too many or too few cells as outliers.
- `assign_stitch_groups` finds no stitch groups.
- Stitch confidence appears high for unrelated cells.
- Plotting tiling QC cannot find scores.

Fixes:

- Verify the labels element is the tiled segmentation output whose artifacts you want to diagnose.
- Tune `nmads_cut`, `nmads_smoothed`, `outlier_use_cut`, and `outlier_use_smoothed` before changing low-level geometry params.
- Use `TilingQCParams(distance_tol=..., min_area=..., max_contour_points=...)` when contour geometry or object size differs from defaults.
- For stitching, tune `min_confidence`, `max_gap`, `max_group_size`, and `StitchParams(close_radius=...)` on a known artifact region.
- Remember `assign_stitch_groups` annotates likely groups only; it does not alter the labels image.
- Confirm the QC table key passed to `tiling_qc` contains the selected `score_col`.

## Memory, Dask, And Parallelism

Symptoms:

- A workflow consumes too much memory.
- Computation is slow or oversubscribes CPU.
- Dask operations appear lazy until a large compute is triggered.

Fixes:

- Start with coarse scales and small generated data to validate API usage.
- Increase `tile_size` for whole-slide images to reduce scheduling overhead, but keep enough overlap for complete cells.
- Keep `n_jobs=1` during debugging; use `n_jobs=-1` only after the workflow is correct and the machine has spare cores.
- Disable previews and progress bars in noninteractive scripts.
- For stain fits, remember the fit materializes tissue pixels at the chosen fit scale; choose coarse scales for large slides.
- For `qc_image`, metric arrays are computed with Dask; choose tile sizes that divide reasonably into image dimensions.

## Headless Plotting

Symptoms:

- `preview=True` fails on a server.
- `experimental.pl.qc_image` or `tiling_qc` opens windows or cannot display.

Fixes:

- Use `preview=False` in all computational calls inside scripts.
- Set a noninteractive Matplotlib backend before plotting in batch jobs:

```python
import matplotlib
matplotlib.use("Agg", force=True)
```

- Use plotting functions only after the corresponding QC table exists.
- Route general spatial scatter, segmentation overlays, and graph/statistics plots to the `visualization` sub-skill.
