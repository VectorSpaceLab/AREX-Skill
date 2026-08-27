# Preprocessing Troubleshooting

Use this guide for failures in face detection, alignment, crop expansion, segmentation-mask loading, RGBA composition, and white-background compositing. For generator-weight or ONNX/PyTorch inference failures, route to `portrait-inference`. For dataset/training workflow failures, route to `data-and-training`.

## Quick Triage

Run the safe checker first when diagnosing a checkout or a port:

```bash
python sub-skills/preprocessing/scripts/preprocess_contract_check.py --repo-root /path/to/photo2cartoon-checkout
```

Then separate the failure into one of these stages:

1. Input decode and RGB/BGR conversion.
2. Detector/landmark installation and runtime.
3. No-face or multiple-face selection behavior.
4. Rotation and crop expansion/padding.
5. TensorFlow graph loading and tensor-name lookup.
6. Alpha mask shape/range and white-background composition.

## Missing `seg_model_384.pb`

Symptoms:

- `NotFoundError`, file-open error, or graph-parse failure when constructing `FaceSeg()`.
- Preprocessing fails before any image-specific face result is produced.

Cause:

- `FaceSeg` expects an external TensorFlow frozen graph named `seg_model_384.pb` beside the preprocessing utility module in a checkout. This generated skill does not bundle that model file.

Checks:

```bash
python sub-skills/preprocessing/scripts/preprocess_contract_check.py \
  --repo-root /path/to/photo2cartoon-checkout \
  --require-seg-model
```

Fixes:

- Place the correct `seg_model_384.pb` asset where the checkout's preprocessing code expects it, or pass an explicit model path if using a port that supports that parameter.
- Do not rename tensors unless you also update the tensor lookup names. The expected names are `input_1:0` and `sigmoid/Sigmoid:0`.
- Do not auto-download this file inside helper scripts; keep asset acquisition an explicit user action.

## TensorFlow 1.x / 2.x Compatibility

Symptoms:

- `AttributeError` around `tf.GraphDef`, `tf.Session`, `gfile.FastGFile`, or graph import.
- `KeyError: The name 'input_1:0' refers to a Tensor which does not exist`.
- TensorFlow eager-mode or v2 behavior conflicts with old graph/session code.

Contract:

- The implementation uses `tf.compat.v1.ConfigProto()`, `tf.Graph()`, and `tf.compat.v1.Session(...)`.
- It imports a frozen GraphDef and looks up exact tensors:
  - input: `input_1:0`
  - output: `sigmoid/Sigmoid:0`

Fixes:

- Prefer a TensorFlow version that still supports `tf.compat.v1` graph/session execution for frozen `.pb` graphs.
- If modern TensorFlow lacks `tensorflow.python.platform.gfile.FastGFile`, port the file open to `tf.io.gfile.GFile` while preserving the graph import and tensor names.
- If tensor lookup fails, inspect the graph operations in a throwaway diagnostic script and confirm the `.pb` is the Photo2Cartoon portrait segmentation graph, not another segmentation model.
- Keep the segmentation input contract as `1 x 384 x 384 x 3` NHWC with values in `[0, 1]`.

## `dlib` / `face_alignment` Installation Errors

Symptoms:

- Import errors for `face_alignment`, `dlib`, `torch`, or detector-specific dependencies.
- Build failures mentioning CMake, compiler, Boost, CUDA, or Python ABI.
- Runtime detector errors when selecting `detector='dlib'` or `detector='sfd'`.

Contract:

- `FaceDetect` creates `face_alignment.FaceAlignment(face_alignment.LandmarksType._2D, device=device, face_detector=detector)`.
- Valid detector choices covered by this skill are `dlib` and `sfd`.
- `device='cuda'` requires a compatible GPU-enabled stack; it is not proven by a CPU import.

Fixes:

- Start with `device='cpu'` and the detector already installed in the environment.
- If `dlib` wheels are unavailable for the Python version, use a compatible Python version or install the system build prerequisites before installing `dlib`.
- If `sfd` is chosen, ensure the local `face_alignment` version supports it and that its deep-learning dependencies are installed.
- Do not treat detector installation as part of the safe bundled checker; the checker intentionally avoids importing these packages.

## No Face Detected

Symptoms:

- `Preprocess.process(image)` returns `None`.
- Inference wrappers print a face-detect failure and skip generator execution.

Likely causes:

- Face is too small, profile/occluded, motion-blurred, or outside the detector's assumptions.
- Input is in BGR order but treated as RGB, reducing detector quality.
- The image is half-body or full-body and the visible face is below the effective scale; repository guidance recommends face regions larger than about `200 x 200` pixels.

Fixes:

- Convert OpenCV reads from BGR to RGB before calling preprocessing.
- Crop the source image around the target face and retry.
- Try the other supported detector if installed (`dlib` vs `sfd`).
- For half-body portraits, pre-crop to the head/shoulder region before segmentation; the segmentation graph is specialized for already-cropped faces.

## Multiple Faces / Wrong Face Selected

Symptoms:

- The output crop belongs to the wrong person in a group image.
- A background face is selected when it has the largest landmark bounding box.

Contract:

- The implementation selects the face with the largest landmark bounding-box area, not the central, sharpest, or most semantically important face.

Fixes:

- Pre-crop the input so the intended subject is the largest visible detected face.
- Run separate crops for separate people if batch-processing group photos.
- Keep detector choice constant when comparing results, because detector choice may change the list of landmark arrays.

## Rotation or Crop Looks Too Wide/Tall

Symptoms:

- Large white borders after alignment.
- Hair/forehead space looks larger than chin/lower-face space.
- Near-edge subjects produce square crops with white padding.

Contract:

- The crop expands by `0.8 x` landmark height above, `0.3 x` below, and `0.3 x` landmark width on both left and right.
- The expanded rectangle is forced square.
- The crop canvas starts white and only the visible source intersection is copied in.
- Inclusive dimensions use `bottom - top + 1` and `right - left + 1`.

Fixes:

- Treat white padding as intentional behavior, not a failed crop, when landmarks extend near the image boundary.
- If a port must match Photo2Cartoon exactly, preserve the asymmetrical expansion ratios and inclusive indexing.
- If too much padding degrades a downstream custom model, crop the original image more tightly before running the canonical preprocessing path rather than silently changing the contract.

## Alpha Mask Shape or Broadcasting Errors

Symptoms:

- `ValueError` from broadcasting during `face * mask + (1 - mask) * 255`.
- Output has black/transparent background or jagged incorrect alpha.
- Generator input has the wrong number of channels.

Contract:

- `face_rgba[:, :, :3]` is `H x W x 3`.
- `face_rgba[:, :, 3]` is `H x W`.
- Convert alpha to `H x W x 1` before composition:

```python
face = face_rgba[:, :, :3].copy()
alpha = face_rgba[:, :, 3].copy()
mask = alpha[:, :, np.newaxis] / 255.0
face_white_bg = (face * mask + (1 - mask) * 255).astype(np.uint8)
```

Fixes:

- Do not pass the 4-channel RGBA array directly into the generator; use the whitened 3-channel RGB face.
- If resizing before inference, resize the RGBA array together so RGB and alpha remain aligned, then split channels.
- Keep alpha values in `0..255` before dividing by `255.0`; avoid boolean masks unless the downstream behavior is intentionally changed.

## RGB/BGR Mixups

Symptoms:

- Face detector behaves poorly on otherwise valid photos.
- Saved preprocessing output has swapped red/blue colors.

Contract:

- OpenCV reads/writes are BGR.
- The preprocessing functions operate on RGB arrays.
- Before writing a whitened RGB face with OpenCV, convert back to BGR.

Fixes:

```python
img_rgb = cv2.cvtColor(cv2.imread(photo_path), cv2.COLOR_BGR2RGB)
rgba = pre.process(img_rgb)
# ... compose face_white_bg in RGB ...
cv2.imwrite(save_path, cv2.cvtColor(face_white_bg, cv2.COLOR_RGB2BGR))
```

## When to Stop and Route Elsewhere

- If preprocessing returns a valid RGBA array but cartoon generation fails, route to `portrait-inference`.
- If the problem is dataset folder placement or whether preprocessed images belong in `trainA`, `testA`, `trainB`, or `testB`, route to `data-and-training`.
- If the task is to alter model layers, checkpoint keys, or tensor shapes inside the generator/discriminator, route to `model-internals`.
