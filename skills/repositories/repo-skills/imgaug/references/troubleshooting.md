# imgaug troubleshooting

Read this when installation, imports, shapes, data types, optional dependencies, or background augmentation behave unexpectedly.

## 1. Import fails after installing imgaug 0.4.0

**Symptoms**
- `ModuleNotFoundError: No module named 'imgaug'`
- `ImportError` from `cv2`, `skimage`, `scipy`, `shapely`, or `imageio`
- Import succeeds from one shell but not another

**Likely causes**
- The package was installed into a different environment than the one running Python.
- A dependency is missing or incompatible.
- NumPy 2.x was installed, but imgaug 0.4.0 still expects `np.sctypes`.

**Recovery**
- Reinstall into the active environment.
- Ensure `numpy<2` is present.
- Use `python scripts/check_imgaug_env.py` to confirm the import path and dependency set.

## 2. Editable local install breaks with modern setuptools

**Symptoms**
- Editable install fails while building metadata or getting requirements.
- Error mentions `pkg_resources`.

**Likely causes**
- Newer editable-build isolation uses a setuptools version that no longer exposes `pkg_resources`.

**Recovery**
- For a local clone of imgaug 0.4.0, install `setuptools<81` in the private inspection environment and retry a no-build-isolation editable install.
- Prefer the public wheel install when you only need runtime usage.

## 3. OpenCV or image backend problems

**Symptoms**
- `ImportError: libGL.so...` or similar OpenCV runtime issues
- Unexpected dependency conflicts involving OpenCV variants
- Color operations behave oddly on images loaded with OpenCV

**Likely causes**
- A non-headless OpenCV build is missing GUI libraries.
- OpenCV loads images as BGR, while imgaug examples assume RGB.

**Recovery**
- Prefer `opencv-python-headless` on servers/CI.
- Convert BGR to RGB before color augmentations.
- Check image dtype and range; imgaug examples generally assume `uint8` `0..255`.

## 4. Shape, dtype, or alignment problems

**Symptoms**
- Augmented images change shape unexpectedly.
- Keypoints or boxes drift away from the image.
- Segmentation maps look blurred or corrupted.
- Dtype conversion raises clipping or range errors.
- Single-channel/grayscale paths fail while 3-channel RGB smokes pass.

**Likely causes**
- The augmenter changed size and `keep_size` was not set as intended.
- Different augmentables were passed in separate calls instead of one aligned call.
- Dense maps were resized with the wrong interpolation semantics.
- Conversion helpers clipped values to the dtype range.
- Some current OpenCV/NumPy combinations expose imgaug 0.4.0 edge cases for single-channel arithmetic augmenters such as `Add`; verify grayscale paths separately.

**Recovery**
- Use one call with `images=...`, `keypoints=...`, `bounding_boxes=...`, etc.
- For segmentation maps, rely on nearest-neighbor semantics; for heatmaps, expect continuous interpolation.
- Prefer explicit `(H, W, 3)` RGB fixtures for general pipeline smokes; if a task needs grayscale, run a dedicated tiny check and be ready to keep a channel dimension or choose a compatible dependency stack.
- Inspect `Batch`/`UnnormalizedBatch` normalization if the input layout is flexible.
- Use the augmentable-specific sub-skill and the bundled smoke helpers.

## 5. Randomness and determinism confusion

**Symptoms**
- Two calls with the same augmenter produce different outputs.
- Replaying a pipeline gives slightly different annotation results.
- Deprecation warnings mention `random_state` or `deterministic`.

**Likely causes**
- The augmenter samples new parameters on each call unless made deterministic.
- `to_deterministic()` or a single aligned call was not used.

**Recovery**
- Use `to_deterministic()` when you need the same sampled transform in separate steps.
- Prefer current `seed`/`RNG` patterns and avoid deprecated `random_state` paths when possible.

## 6. Background augmentation hangs or is much slower than expected

**Symptoms**
- `augment_batches(background=True)` appears stalled.
- `Pool` or `BackgroundAugmenter` never finishes.
- Child-process behavior differs on macOS/NixOS/Windows.

**Likely causes**
- Too many workers or a bad `chunksize`/queue choice.
- The process is blocked on GUI display, a non-picklable lambda, or an unfinished consumer.
- Platform-specific multiprocessing start-method issues.

**Recovery**
- Start with the bundled tiny multicore smoke helper.
- Reduce to one or two batches and a small queue.
- Avoid GUI calls in workers.
- Ensure custom augmenters and callback functions are picklable.
- Prefer explicit `Pool` or threaded loading before process-backed `BatchLoader`; on current Python versions, legacy process-loader seeding can fail if a NumPy integer seed reaches `random.seed`.
- If a platform-specific hang appears, switch to a smaller smoke case before scaling up.

## 7. Optional dependency gaps

**Symptoms**
- `imgcorruptlike` augmenters fail to import or are missing.
- A docs example references behavior that is not available in the current environment.

**Likely causes**
- Optional packages such as `imagecorruptions` or `numba` were not installed.

**Recovery**
- Install the optional package only if the current task needs that family.
- Otherwise leave the capability unverified and use the rest of the skill normally.

## Next step

- For image-only pipelines, open `sub-skills/augmentation-pipelines/SKILL.md`.
- For aligned annotations, open `sub-skills/augmentables-and-batches/SKILL.md`.
- For randomness or dtype issues, open `sub-skills/parameters-random-and-utilities/SKILL.md`.
- For background augmentation or hangs, open `sub-skills/multicore-and-diagnostics/SKILL.md`.
