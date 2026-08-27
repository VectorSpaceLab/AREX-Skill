# Prompted Segmentation Troubleshooting

## `KeyError` or Wrong `model_type`

Symptoms:

- `KeyError: '...'` from `sam_model_registry[model_type]`.
- State-dict size mismatch while loading a checkpoint.

Fix:

- Use only `default`, `vit_h`, `vit_l`, or `vit_b`.
- Match the checkpoint to the model type. `default` is the same builder as `vit_h`.
- Check that the checkpoint path is a local `.pth` file supplied by the user; this skill and its helper scripts do not download checkpoints.

## Missing Checkpoint File

Symptoms:

- `FileNotFoundError` from `open(checkpoint, "rb")` inside model construction.

Fix:

- Ask the user for the actual checkpoint path.
- Do not silently switch model types or attempt downloads.
- If the user has no checkpoint, explain that SAM v1 requires a compatible ViT-H, ViT-L, or ViT-B checkpoint before inference.

## `An image must be set...`

Symptoms:

- `RuntimeError: An image must be set with .set_image(...) before mask prediction.`
- Similar error from `get_image_embedding()`.

Fix:

- Call `predictor.set_image(image, image_format="RGB")` before every first prediction on a new image.
- If using `reset_image()`, call `set_image(...)` again.
- Keep one predictor per active image when managing concurrent or interleaved prompt sessions.

## Invalid `image_format`

Symptoms:

- Assertion: `image_format must be in ['RGB', 'BGR']`.

Fix:

- Pass exactly `"RGB"` or `"BGR"`; lowercase strings are invalid.
- If using OpenCV image loading, either convert BGR to RGB and pass `"RGB"`, or pass the original OpenCV array with `image_format="BGR"`.

## Wrong Image Dtype or Layout

Symptoms:

- PIL/torch conversion errors in resizing.
- Unexpected colors or poor masks.
- Shape errors around channel or tensor dimensions.

Fix:

- For `set_image(...)`, pass a NumPy array with shape `H x W x 3`.
- Use `uint8` pixels in `[0, 255]` unless you intentionally know the transform path accepts your format.
- Do not pass `C x H x W`, grayscale `H x W`, RGBA `H x W x 4`, normalized float tensors, or batched arrays to `set_image(...)`.
- For pre-transformed torch images, use `set_torch_image(...)` only when you have already resized with SAM's expected transform and can satisfy `1 x 3 x H x W` with longest side `1024`.

## `point_labels must be supplied if point_coords is supplied`

Symptoms:

- Assertion from `predict(...)`.

Fix:

- Always pass `point_labels` with the same number of entries as `point_coords`.
- Use `1` for foreground points and `0` for background points.
- Ensure `point_coords.shape == (N, 2)` and `point_labels.shape == (N,)`.

## Box and Coordinate Shape Mistakes

Symptoms:

- Transform reshape errors.
- Masks appear shifted or target the wrong object.

Fix:

- Use original image pixel coordinates before resizing.
- For NumPy `predict(...)`, pass one box as a length-4 array `[x0, y0, x1, y1]` in `XYXY` order.
- Do not use COCO `XYWH` boxes unless you convert to `XYXY` first.
- For torch batch boxes, use shape `B x 4` and transform with `predictor.transform.apply_boxes_torch(boxes, image.shape[:2])` before `predict_torch(...)`.

## Device Mismatch

Symptoms:

- Torch errors mentioning tensors on different devices, such as CPU and CUDA.

Fix:

- Move the model once: `sam.to(device=device)` before prediction.
- Create torch prompt tensors on `predictor.device` when using `predict_torch(...)`.
- The NumPy `predict(...)` path internally converts prompts onto `predictor.device`, so prefer it for simple scripts.

## Ambiguous Multimask Selection

Symptoms:

- `masks` has shape `3 x H x W` when the user expected one mask.
- The chosen mask is not the desired object after a single click.

Fix:

- `multimask_output=True` returns three masks and three scores. Pick `np.argmax(scores)` for an automatic best guess.
- For a box, multiple points, or a refined prompt where one object is intended, set `multimask_output=False`.
- If a single click remains ambiguous, ask for a box, a second foreground point, or a background point rather than relying only on score ranking.

## Low-Resolution Mask Refinement Shape

Symptoms:

- Shape errors when passing `mask_input`.
- Refinement behaves unpredictably.

Fix:

- Use `low_res_masks` from the previous prediction, not the high-resolution boolean `masks` output.
- Select one candidate before refinement: `mask_input = low_res_masks[np.argmax(scores)][None, :, :]`.
- For NumPy `predict(...)`, `mask_input` must be `1 x 256 x 256`.
- For torch `predict_torch(...)`, `mask_input` must be `B x 1 x 256 x 256`.

## Batch API Prompt Transform Mistakes

Symptoms:

- Direct `sam(...)` or `predict_torch(...)` produces shifted masks or shape errors.

Fix:

- `predict_torch(...)` expects already transformed prompts. Use `predictor.transform.apply_coords_torch(...)` or `apply_boxes_torch(...)` with the original `(H, W)` image size.
- Direct `sam(...)` expects each record's `image` tensor to already be resized to SAM's input frame and each prompt to already be transformed.
- For interactive and one-off work, use `SamPredictor.predict(...)` because it performs prompt transforms from original image coordinates internally.
