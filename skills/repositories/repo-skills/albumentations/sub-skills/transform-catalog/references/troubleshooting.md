# Transform troubleshooting

Use this when Albumentations 2.x transform selection or constructor validation fails.

## Old parameter names fail

Symptoms:

- `ValidationError` or `TypeError` mentioning unexpected parameters such as `value`, `mask_value`, `min_holes`, `max_holes`, `min_height`, `max_height`, `min_width`, `max_width`, `height`, or `width`.
- A v1-style pipeline no longer constructs in Albumentations 2.x.

Fixes:

| Replace | With |
| --- | --- |
| `value=...` | `fill=...` |
| `mask_value=...` | `fill_mask=...` |
| `RandomResizedCrop(height=H, width=W)` | `RandomResizedCrop(size=(H, W))` |
| `min_holes=MIN, max_holes=MAX` | `num_holes_range=(MIN, MAX)` |
| `min_height=MIN, max_height=MAX` | `hole_height_range=(MIN, MAX)` |
| `min_width=MIN, max_width=MAX` | `hole_width_range=(MIN, MAX)` |
| `unit_size_min=MIN, unit_size_max=MAX` | `unit_size_range=(MIN, MAX)` |

Probe command:

```bash
python scripts/transform_probe.py migrate --transform CoarseDropout --params min_holes=1 max_holes=4 min_height=8 max_height=16 min_width=8 max_width=16 value=0 mask_value=255
```

Then verify against the installed signature:

```bash
python scripts/transform_probe.py signature CoarseDropout
```

## Invalid range tuple shapes

Symptoms:

- Validation errors mention a tuple, nondecreasing values, bounds, or an invalid range.
- A dropout, crop, blur, rotate, noise, or color transform rejects a scalar/list you expected to work.

Fixes:

- Use two-element tuples `(min, max)`, not lists of many values.
- Keep ranges nondecreasing: `(0.1, 0.2)`, not `(0.2, 0.1)`.
- Respect bounds: dropout fractions should be in valid fractional or pixel ranges; `GridDropout(ratio=...)` must be greater than 0 and at most 1.
- For `CoarseDropout`, float `hole_height_range` and `hole_width_range` values represent fractions of image size when less than 1; int values represent pixels.
- For `XYMasking`, at least one of `mask_x_length` or `mask_y_length` must be positive, and sampled mask lengths must fit the current image width/height.

## Dtype and range mismatches

Symptoms:

- Output appears washed out, saturated, all zeros, or far outside model expectations.
- Normalization behaves differently after switching from `uint8` to `float32` images.
- RGB-specific transforms reject grayscale, multispectral, or channel-first arrays.

Fixes:

- Albumentations image transforms generally expect NumPy arrays in HWC layout for images.
- Common image dtypes are `uint8` in `[0, 255]` and `float32`; confirm the expected range before `Normalize`, `ToFloat`, or `FromFloat`.
- `A.Normalize(normalization="standard")` uses `(img - mean * max_pixel_value) / (std * max_pixel_value)`. Set `max_pixel_value=1.0` only if float images are already in `[0, 1]`.
- For RGB-only color transforms, avoid grayscale/multispectral input or convert explicitly with a transform such as `ToRGB` when appropriate.
- Keep tensor conversion after NumPy-space transforms; route tensor issues to `../framework-integration/`.

## Segmentation masks get corrupted

Symptoms:

- Mask contains fractional labels after resize/rotate/affine.
- New border labels are not recognized by the loss.
- Dropout changes mask labels unexpectedly or fails to mark ignored pixels.

Fixes:

- Set `mask_interpolation=cv2.INTER_NEAREST` or `cv2.INTER_NEAREST_EXACT` on transforms that expose it.
- Set `fill_mask` to a valid background class or ignore index when using constant borders or padding.
- For dropout transforms, choose `fill_mask=None` to leave masks unchanged, or a numeric label/ignore value to overwrite dropped mask regions.
- Do not use image-only blur/noise/weather transforms on masks directly. Put them in `Compose` as image transforms so masks pass through unchanged.
- Run a tiny probe and check `set(np.unique(mask_after))` is still a subset of expected class ids plus any intended ignore id.

## Transform does not support a target

Symptoms:

- Errors mention unsupported targets, missing bbox/keypoint processors, or unchanged coordinates.
- A pixel transform did not update bboxes/keypoints, or a standalone transform call ignored labels.

Fixes:

- Use pixel transforms for image appearance only; they do not move coordinates.
- Use spatial `DualTransform` classes for masks, bboxes, and keypoints.
- Put bbox/keypoint workflows inside `A.Compose(..., bbox_params=..., keypoint_params=...)` with matching label fields.
- Route coordinate format and label-field debugging to `../targets-and-formats/`.
- For volumes or `mask3d`, confirm whether the selected 2D transform lists those targets; otherwise use the 3D transform family from `../targets-and-formats/`.

## Missing metadata for mixing or domain adaptation

Symptoms:

- Errors mention `mosaic_metadata`, `overlay_metadata`, `fda_metadata`, `hm_metadata`, `pda_metadata`, or a custom `metadata_key`.
- Domain adaptation warns that `reference_images` and `read_fn` are deprecated.

Fixes:

- Pass metadata arrays in the transform call, not as source file paths. Example: `transform(image=image, hm_metadata=[reference_image])`.
- `FDA`, `HistogramMatching`, and `PixelDistributionAdaptation` expect the configured metadata key to contain a non-empty sequence of NumPy arrays.
- `Mosaic` expects additional samples in `mosaic_metadata`; include masks/bboxes/labels when the workflow needs them.
- `OverlayElements` metadata items need at least `image`; optional `mask`, normalized `bbox`, and ids control placement and mask updates.
- Avoid deprecated constructor `reference_images=` unless maintaining legacy code; if used, provide a valid `read_fn`.

## Text, Pillow, and font issues

Symptoms:

- `TextImage` fails to load a font, cannot render text, or complains about missing metadata.
- Text augmentation choices fail validation.

Fixes:

- `font_path` must be a readable font file available to the running project.
- Provide `textimage_metadata` or the configured `metadata_key` at call time.
- Use only `None`, `"insertion"`, `"swap"`, and `"deletion"` in `augmentations`.
- Keep `fraction_range` and `font_size_fraction_range` as `(min, max)` tuples within `[0, 1]`.
- Treat Pillow/font availability as an environment issue; do not hard-code local font paths in reusable skills or libraries.

## OpenCV interpolation, border, and fill constraints

Symptoms:

- OpenCV raises errors about unsupported interpolation or border values.
- Constant padding/rotation fill color has wrong channels.
- Inpainting fill fails.

Fixes:

- Use valid OpenCV interpolation constants, commonly `cv2.INTER_NEAREST`, `INTER_LINEAR`, `INTER_CUBIC`, `INTER_AREA`, `INTER_LANCZOS4`, and where supported exact variants.
- Use `cv2.INTER_NEAREST` for masks.
- Use valid border modes: `cv2.BORDER_CONSTANT`, `BORDER_REPLICATE`, `BORDER_REFLECT`, `BORDER_WRAP`, or `BORDER_REFLECT_101`.
- For color images, `fill` may be a scalar or per-channel tuple; ensure tuple length matches channel count.
- Inpainting fills (`"inpaint_telea"`, `"inpaint_ns"`) are for grayscale/RGB image holes and are not mask fill strategies.

## Quick debug sequence

1. Print the installed constructor signature with `transform_probe.py signature TransformName`.
2. Convert obvious old names with `transform_probe.py migrate`.
3. Run `transform_probe.py smoke --transform TransformName` for image-only or image/mask basics.
4. If masks or coordinates are involved, verify unique mask labels and route coordinate details to `../targets-and-formats/`.
5. If construction still fails, reduce the transform to its default constructor and add parameters back one at a time.
