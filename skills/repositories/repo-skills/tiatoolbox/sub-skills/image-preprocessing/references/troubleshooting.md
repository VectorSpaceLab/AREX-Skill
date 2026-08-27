# Image Preprocessing Troubleshooting

Use this guide when TIAToolbox preprocessing returns no data, unstable stain results, unexpected patch shapes, or memory/codec failures.

## Stain Normalization and Augmentation

### Bad Stain Method Name

Symptoms:

- `get_normalizer(...)` raises a method-not-supported error.
- `StainAugmentor(...)` raises `Unsupported stain extractor method`.

Checks and fixes:

- For `get_normalizer`, use one of `reinhard`, `ruifrok`, `macenko`, `vahadane`, or `custom`.
- For `StainAugmentor`, use only `macenko` or `vahadane`.
- Normalize user input with `.lower().strip()` before passing it to TIAToolbox.
- Do not assume aliases such as `h&e`, `he`, `vah`, or `mac` are accepted.

### Custom Stain Matrix Shape or CSV Header Failure

Symptoms:

- Custom normalizer construction fails.
- CSV matrix loads as strings or has an unexpected shape.
- A matrix works in a spreadsheet but fails in TIAToolbox.

Checks and fixes:

- Use `get_normalizer("custom", stain_matrix=matrix_or_path)`.
- Ensure the matrix is numeric shape `(2, 3)` or `(3, 3)`.
- Use a headerless CSV; column names become nonnumeric data.
- Use `.npy` for the least ambiguous matrix handoff.
- Do not pass `stain_matrix` to non-custom methods; TIAToolbox rejects that combination.

### Missing Target Image

Symptoms:

- The `stain-norm` CLI receives source images but no target.
- API code calls `transform(source_image)` before `fit(target_image)`.
- Normalized colors look arbitrary or stale from a previous target.

Checks and fixes:

- Always fit the normalizer on a representative target image before transforming sources.
- For CLI workflows, provide the target image option and verify the path exists before launching batch work.
- Keep target image selection separate from source image discovery; do not accidentally fit on the first source image unless that is intentional.
- For custom matrices, a target image is still needed because `fit(target_image)` establishes target stain information.

### Blank or Tiny Tissue Inputs

Symptoms:

- Macenko/Vahadane extraction fails, logs warnings, or produces unstable colors.
- Augmentation changes background strongly or not at all.

Checks and fixes:

- Fit stain methods on representative tissue-rich RGB `uint8` images.
- Use `reinhard` for tiny smoke checks and broad color transfer.
- Precompute a target stain matrix from a good target when using `StainAugmentor` at scale.
- Keep `augment_background=False` unless background augmentation is desired.

## Tissue Masks and Patch Filtering

### Mask/Image Coordinate Mismatch

Symptoms:

- `SlidingWindowPatchExtractor` returns zero patches even though tissue is visible.
- The positive mask area appears shifted or scaled relative to the image.
- `PatchExtractor.filter_coordinates(...)` filters out plausible boxes.

Checks and fixes:

- Confirm image coordinates, mask coordinates, and `wsi_shape` refer to the same requested `resolution` and `units`.
- Remember patch parameters and coordinates use `(width, height)` ordering, while NumPy masks use `(height, width)`.
- If using a thumbnail mask with a baseline WSI, wrap it with WSI metadata or use a WSI-generated mask so rescaling is explicit.
- Temporarily set `min_mask_ratio=0` and inspect `len(extractor)`; if patches appear, the mask exists but filtering is too strict.
- Use `PatchExtractor.get_coordinates(...)` to debug the grid before reading pixels.

### `min_mask_ratio` Filters All Patches

Symptoms:

- Extractor construction logs that no candidate coordinates are left after filtering.
- `len(extractor) == 0` with a valid image and mask.

Checks and fixes:

- Start with `min_mask_ratio=0` or a low value such as `0.05`, then increase after counts look plausible.
- Inspect the mask's positive fraction with `mask.mean()` for boolean masks.
- Verify the mask polarity: TIAToolbox expects positive/true mask values to represent included tissue.
- Check patch size versus tissue islands; large patches over narrow tissue can have low positive ratios.
- For annotation masks, confirm `store_filter` selects the expected annotation classes.

### Stride and Patch Shape Confusion

Symptoms:

- Too many, too few, or overlapping patches are produced.
- Returned patch shape seems transposed.
- Point-centered patches are offset from expected centers.

Checks and fixes:

- `patch_size=(width, height)` and `stride=(x_stride, y_stride)`.
- Returned arrays are shaped `(height, width, channels)`.
- `stride=None` means `stride == patch_size` for sliding windows.
- Smaller stride than patch size creates overlap; larger stride skips gaps.
- `PointsPatchExtractor` treats supplied points as centers and shifts internal top-left coordinates by half the patch size.

### Padding and Out-of-Bounds Reads

Symptoms:

- Border patches include black/constant regions.
- Border patches are missing unexpectedly.
- A point near an edge returns a padded patch.

Checks and fixes:

- Use `within_bound=True` to skip windows whose requested bounds exceed image limits.
- Use `within_bound=False` to keep border windows and pad them.
- Set `pad_mode` and `pad_constant_values` intentionally when keeping border patches.
- For points near edges, decide whether padded context is acceptable for the downstream model.

## Large WSI and Pyramid Issues

### Large WSI Memory Pressure

Symptoms:

- Preprocessing tries to materialize a full WSI array.
- Kernel dies or memory grows during stain normalization or masking.
- Pyramid dumping creates unexpectedly many files.

Checks and fixes:

- Use WSI thumbnails for tissue masks instead of full-resolution reads.
- Stream patches with `SlidingWindowPatchExtractor` or `PointsPatchExtractor` instead of converting the whole slide to an array.
- Fit stain normalizers on representative tiles or target images, not entire WSIs.
- Estimate patch counts with `PatchExtractor.get_coordinates(...)` before reading pixels.
- Confirm output location and container options before running pyramid `dump(...)`.

### Optional Image Codec Failures

Symptoms:

- WSI/image open fails for formats such as SVS, NDPI, JP2, or tiled TIFF.
- A CLI finds files but cannot decode them.
- Behavior differs between PNG/JPEG smoke tests and production WSIs.

Checks and fixes:

- Route reader backend and metadata diagnosis to `wsi-io`.
- Verify optional dependencies and system codecs for the target format.
- Reproduce with a tiny PNG/JPEG array path to separate preprocessing logic from codec issues.
- If only one WSI format fails, avoid changing stain or patch parameters until reader support is confirmed.

## Difficult Debug Scenarios

### Zero Patches from Mask Resolution Mismatch

Scenario: A user creates a mask from a low-resolution thumbnail and passes it to a baseline sliding-window extraction with `min_mask_ratio=0.5`; `len(extractor)` is zero.

Debug path:

1. Confirm the requested extractor `resolution`/`units` and the mask's resolution.
2. Lower `min_mask_ratio` to `0` to separate grid generation from mask filtering.
3. Compute candidate boxes with `PatchExtractor.get_coordinates(...)` using the requested image shape.
4. Inspect mask positive fraction and polarity.
5. Recreate the mask using WSI-aware metadata or automatic `input_mask="otsu"`/`"morphological"` for the same WSI where appropriate.
6. Restore a conservative `min_mask_ratio` only after patch counts are plausible.

### Custom Matrix Plus Target Image Choice

Scenario: A user supplies `stain_matrix.csv` and a target image and asks which normalizer to use.

Decision path:

1. Validate that the CSV is numeric and headerless with shape `(2, 3)` or `(3, 3)`.
2. Choose `get_normalizer("custom", stain_matrix="stain_matrix.csv")` because the user supplied a matrix.
3. Still call `fit(target_image)` before transforming source images.
4. If the custom matrix is invalid or not trusted, fall back to `macenko` or `vahadane` with the target image; use `reinhard` for fast broad color matching.
