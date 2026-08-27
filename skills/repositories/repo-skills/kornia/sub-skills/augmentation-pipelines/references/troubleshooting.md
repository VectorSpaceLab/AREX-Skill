# Augmentation Troubleshooting

Use these checks when an augmentation pipeline misbehaves, produces wrong shapes,
loses synchronization, or fails to export.

## 1. The pipeline returns the wrong number of outputs

Symptoms:

- `AssertionError` about input count or data keys.
- A positional call returns a value ordering that does not match expectations.

Checks:

- Ensure the number of positional inputs equals the number of `data_keys`.
- Ensure the first key is `"input"`/`"image"` when the pipeline samples
  params from the image.
- Keep the positional order exactly aligned with `data_keys`.
- For dictionary input, construct the container with `data_keys=None`.

Repair:

```python
aug = K.AugmentationSequential(..., data_keys=["input", "mask", "bbox_xyxy"])
```

## 2. The image is not in `[0, 1]`

Symptoms:

- Color jitter or other photometric transforms produce clipped or unreasonable
  values.
- Inputs come from `uint8` image loaders.

Checks:

- Convert images to floating point.
- Normalize to `[0, 1]` before augmentation.

Repair:

```python
image = image.to(torch.float32) / 255.0
```

## 3. The mask no longer matches the image

Symptoms:

- Segmentation mask edges look blurred.
- Shape or spatial alignment drift appears after augmentation.

Checks:

- Use `AugmentationSequential` rather than image-only augmentation when masks
  need the same spatial transform.
- Verify `data_keys` order.
- Use `keepdim=True` for stable output ranks.
- Confirm mask interpolation is nearest-like, not bilinear-like.

Repair:

- Keep masks in the same batch and spatial shape as the image.
- Use deterministic smokes with flips or identity-like affine parameters before
  testing more complex geometry.

## 4. Boxes or keypoints are malformed after augmentation

Symptoms:

- Boxes leave image bounds unexpectedly.
- Keypoints change order or shape.
- Bounding boxes appear to be interpreted incorrectly.

Checks:

- Confirm the target convention: `bbox`, `bbox_xyxy`, or `bbox_xywh`.
- Use floating point coordinate tensors.
- Keep coordinates in pixel `(x, y)` order.
- Ensure the box/keypoint batch dimension matches the image batch dimension.

Repair:

- Convert custom box formats to the exact data key the container expects.
- If the main task is low-level warp math, use [geometry-vision](../../geometry-vision/SKILL.md) instead of forcing a multi-target
  augmentation pipeline.

## 5. `transform_matrix` is `None`

Symptoms:

- The container forward works, but `.transform_matrix` is missing.
- A check expecting `(B, 3, 3)` or `(B, 4, 4)` fails.

Checks:

- Use a pipeline composed of matrix-producing geometric modules.
- Intensity-only transforms do not produce useful spatial matrices.
- `transformation_matrix_mode="skip"` intentionally disables collection.
- Some non-rigid modules are ignored or rejected depending on the matrix mode.

Repair:

- Switch to `transformation_matrix_mode="rigid"` for debugging rigid geometry.
- Remove intensity-only or unsupported modules from matrix-dependent tests.

## 6. Inverse fails or gives partial recovery

Symptoms:

- `inverse` raises `ValueError` about missing params.
- Recovered tensors are shifted, clipped, or not exact.

Checks:

- Run a forward pass first, or pass explicit `params=`.
- Only rigid geometric transforms are good inverse candidates.
- Crops, padding, resizing, interpolation, erasing, and color edits are not
  perfectly invertible.

Repair:

- Test inverse on flips and rigid affine transforms before using it on more
  complex chains.
- For export-friendly behavior, keep deterministic image preprocessing separate
  from stochastic training augmentation.

## 7. `random_apply` seems to ignore one transform

Symptoms:

- Only some children run.
- Order changes between calls.

Checks:

- `random_apply=True` does not mean "apply all in order"; it means "apply all
  in a random order".
- `random_apply=1` selects one child.
- Child-level `p` still matters.

Repair:

- Set child `p=1.0` when the container should decide the active branch.
- Use fixed seeds for reproducible diagnostics.

## 8. Video augmentation is incoherent across frames

Symptoms:

- Adjacent frames do not share the same spatial transform.

Checks:

- Confirm `VideoSequential(..., same_on_frame=True)` when temporal coherence is
  required.
- Confirm the input shape matches `data_format`.

Repair:

- Use `BTCHW` for a batch of clips and keep the clip-time dimension explicit.
- Wrap video targets in `AugmentationSequential` only when the target is a video
  image/mask/box/keypoint task.

## 9. Export or compile support is inconsistent

Symptoms:

- Exported output differs from eager.
- A random multi-target pipeline is not exportable in the target environment.

Checks:

- Deterministic preprocessing is safer than stochastic augmentation for export.
- `.transform_matrix` and `._params` are eager state and may be skipped during
  export capture.
- Optional export dependencies may not be installed.

Repair:

- Reduce the export smoke to a deterministic image-only pipeline.
- Keep augmentation training code and deployment preprocessing separate when the
  deployment backend has not been proven.

## 10. `same_on_batch` or `keepdim` surprises

Symptoms:

- Different batch items get different transforms when they should not.
- Output rank changes unexpectedly.

Checks:

- `same_on_batch=True` shares parameters across the batch.
- `keepdim=True` is the safest default for task code and smoke tests.

Repair:

- Set both explicitly in reproducibility-critical examples.
- Use shape assertions in the smoke script before checking numeric values.
