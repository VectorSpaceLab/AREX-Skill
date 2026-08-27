# Photo2Cartoon Preprocessing Pipeline

This reference captures the runtime contract for the face preprocessing path used before Photo2Cartoon training and inference. It is self-contained guidance; use a local Photo2Cartoon checkout only as an implementation target, not as a linked runtime dependency.

## Scope and Routing

Use this reference for:

- `Preprocess.process(image)` orchestration.
- `FaceDetect.align(image)` landmark detection, largest-face selection, and rotation alignment.
- Landmark-bbox crop expansion and white padding.
- TensorFlow segmentation graph input/output tensor contracts.
- RGBA output and white-background composition.

Route these elsewhere:

- Generator inference, PyTorch/ONNX assets, and cartoon tensor postprocessing -> `portrait-inference`.
- Dataset folder layout, batch preprocessing policy, and training commands -> `data-and-training`.

## Inputs

The preprocessing code expects an in-memory image, not a filename:

```python
# OpenCV readers produce BGR. Convert before preprocessing.
img_bgr = cv2.imread(photo_path)
img_rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
rgba = pre.process(img_rgb)
```

Input contract:

- Shape: `H x W x 3`.
- Channel order: RGB.
- Typical dtype: `uint8`, values `0..255`.
- Subject: a front-facing portrait works best; the project guidance recommends faces larger than roughly `200 x 200` pixels and notes the released model was trained mainly on young Asian female portraits.

## Orchestration: `Preprocess.process`

`Preprocess(device='cpu', detector='dlib')` constructs two components:

- `FaceDetect(device, detector)` for landmark-based face alignment.
  - `device`: `'cpu'` or `'cuda'`.
  - `detector`: `'dlib'` or `'sfd'` as passed into `face_alignment.FaceAlignment(..., face_detector=detector)`.
- `FaceSeg()` for portrait segmentation with an external TensorFlow `.pb` graph.

`process(image)` flow:

1. `face_info = self.detect.align(image)`.
2. If no landmarks are returned, return `None`.
3. Otherwise unpack `(image_align, landmarks_align)`.
4. Crop the aligned image using expanded landmark bounds.
5. Run segmentation on the crop to get a 2-D alpha mask.
6. Return `np.dstack((face, mask))`, an RGBA array with the RGB crop and alpha channel.

Success/failure contract:

```python
rgba = pre.process(img_rgb)
if rgba is None:
    # No detectable face. Do not call generator preprocessing on this image.
    ...
else:
    assert rgba.ndim == 3 and rgba.shape[2] == 4
```

## Face Detection and Largest-Face Selection

`FaceDetect.align(image)` calls `face_alignment.FaceAlignment(...).get_landmarks(image)`.

- If the detector returns `None`, preprocessing returns `None`.
- If exactly one face is detected, its 68-point landmark array is used.
- If multiple faces are detected, the selected face is the one with the largest landmark bounding-box area:

```python
area = (landmarks_bottom - landmarks_top) * (landmarks_right - landmarks_left)
```

Implications:

- In a group photo, the largest visible face wins, not necessarily the central or most frontal face.
- To process a smaller/secondary face, crop the input image first so the target face becomes the largest detected face.
- Detector choice can change which faces are detected; keep `detector` fixed when reproducibility matters.

## Rotation Alignment

Alignment uses the outer eye-corner landmarks:

- left eye corner: `landmarks[36]`
- right eye corner: `landmarks[45]`

The rotation angle is:

```python
radian = np.arctan((left_eye_corner[1] - right_eye_corner[1]) /
                   (left_eye_corner[0] - right_eye_corner[0]))
```

The code computes a new canvas size that can contain the rotated image, then applies `cv2.warpAffine(..., borderValue=(255, 255, 255))`. New canvas regions are white. The same affine matrix is applied to the landmark coordinates so the crop stage uses rotated landmarks.

Operational notes:

- Very small eye horizontal distance, extreme profile poses, or wrong landmarks can cause unstable rotations.
- Rotation is based on the eye-corner line only; it does not perform full similarity alignment to a fixed template.
- White rotation borders are expected and may later become part of the crop if the expanded box crosses the source image boundary.

## Crop Expansion Contract

After rotation, the crop uses the min/max landmark bounding box and expands it asymmetrically:

```python
landmarks_top = np.min(landmarks[:, 1])
landmarks_bottom = np.max(landmarks[:, 1])
landmarks_left = np.min(landmarks[:, 0])
landmarks_right = np.max(landmarks[:, 0])

box_h = landmarks_bottom - landmarks_top
box_w = landmarks_right - landmarks_left

top = int(landmarks_top - 0.8 * box_h)
bottom = int(landmarks_bottom + 0.3 * box_h)
left = int(landmarks_left - 0.3 * box_w)
right = int(landmarks_right + 0.3 * box_w)
```

The expanded rectangle is then made square:

- If `bottom - top > right - left`, widen left/right around the box.
- Otherwise, expand top/bottom around the box.

The output crop array is allocated as white with inclusive dimensions:

```python
image_crop = np.ones((bottom - top + 1, right - left + 1, 3), np.uint8) * 255
```

Then the visible source intersection is copied into the corresponding position. If `top` or `left` is negative, or `bottom`/`right` extends beyond the image, the uncovered area remains white.

Practical consequences:

- The crop includes substantial forehead/hair room above the landmarks (`0.8 x` landmark height above) and less space below (`0.3 x`).
- Width grows by `0.3 x` landmark width on both sides.
- Near-edge faces produce white padding rather than clipping to a non-square crop.
- Because the final dimensions are inclusive (`+1`), expect sizes like `211 x 211` when the expanded side length is `210`.

## TensorFlow Segmentation Contract

`FaceSeg` loads an external graph file named `seg_model_384.pb` by default. The graph file is reference-only for this skill and is not bundled.

Runtime contract from the implementation:

- Session style: TensorFlow compat v1 graph/session APIs.
- Default graph path: `seg_model_384.pb` located beside the preprocessing utility module in a checkout.
- Input tensor name: `input_1:0`.
- Output tensor name: `sigmoid/Sigmoid:0`.
- Segmentation input size: `384 x 384`.
- Feed shape: `1 x 384 x 384 x 3` (`NHWC`).
- Feed values: `image / 255.0`.
- Output handling: run session, take `[0]`, resize to original crop shape `(crop_h, crop_w)`, multiply by `255`, cast to `uint8`.

Equivalent contract sketch:

```python
image_input = cv2.resize(face_crop, (384, 384), interpolation=cv2.INTER_AREA)
image_input = (image_input / 255.0)[None, :, :, :]
mask = sess.run(output_op, feed_dict={input_op: image_input})[0]
mask = cv2.resize(mask, (face_crop.shape[1], face_crop.shape[0]))
mask = (mask * 255).astype(np.uint8)
```

Do not feed full-body or half-body images directly into the segmentation graph. The repository Q&A states that this segmentation model is specialized for already-cropped face regions.

## RGBA Output Semantics

`Preprocess.process` returns:

```python
face_rgba = np.dstack((face, mask))
```

Where:

- `face_rgba[:, :, :3]` is the RGB crop.
- `face_rgba[:, :, 3]` is a 2-D alpha mask resized to crop height/width.
- Alpha is `uint8`-style `0..255`; downstream code treats `255` as foreground and `0` as background.

Validation checks:

```python
assert face_rgba.ndim == 3
assert face_rgba.shape[2] == 4
face = face_rgba[:, :, :3].copy()
alpha = face_rgba[:, :, 3].copy()
assert alpha.shape == face.shape[:2]
```

## Background Whitening

Both training-data preparation and inference compose the face over white before passing pixels onward:

```python
face = face_rgba[:, :, :3].copy()
mask = face_rgba[:, :, 3].copy()[:, :, np.newaxis] / 255.0
face_white_bg = (face * mask + (1 - mask) * 255).astype(np.uint8)
```

For generator inference, the RGBA result is resized to `256 x 256` first, then the whitened RGB face is normalized to `[-1, 1]`:

```python
face_rgba = cv2.resize(face_rgba, (256, 256), interpolation=cv2.INTER_AREA)
face = face_rgba[:, :, :3].copy()
mask = face_rgba[:, :, 3][:, :, np.newaxis].copy() / 255.0
face = (face * mask + (1 - mask) * 255) / 127.5 - 1
```

For data preparation, the whitened RGB face is written as an image after converting RGB back to BGR for OpenCV writers.

## Safe Contract Checks

The bundled script performs static and synthetic checks without importing TensorFlow, dlib, face-alignment, OpenCV, or local repo modules:

```bash
# From the generated photo2cartoon skill directory:
python sub-skills/preprocessing/scripts/preprocess_contract_check.py --help
python sub-skills/preprocessing/scripts/preprocess_contract_check.py --repo-root /path/to/photo2cartoon-checkout
python sub-skills/preprocessing/scripts/preprocess_contract_check.py --repo-root /path/to/photo2cartoon-checkout --require-seg-model
```

Use the `--require-seg-model` form only when the real segmentation graph should be present. Without that flag, a missing graph is reported as a warning because the graph is an external asset.
