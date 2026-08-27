# Image Detection Troubleshooting

## Purpose

Use this when still-image inference or the no-weight smoke helper fails. Start with the bundled helper when the problem might be preprocessing, OpenCV, IoU, or postprocessing rather than weight/model loading.

```bash
python scripts/check_image_pipeline.py --reso 64
python scripts/check_image_pipeline.py --repo-root <repo-root> --reso 64
```

## Missing weights

Symptoms:

- `FileNotFoundError`, failed `open`, failed `load_weights`, or a message involving `yolov3.weights`.
- The detector prints `Loading network.....` and fails before image prediction.

Likely causes:

- The default `--weights yolov3.weights` file is not present in the current working directory.
- The user supplied a path to a missing, truncated, or incompatible weights file.

Recovery:

1. Do not download weights automatically.
2. Ask the user for the intended local weights path.
3. Rebuild the command with the bundled launcher, for example `python scripts/run_image_detection.py --repo-root <repo-root> --images <image-or-dir> --det <output-dir> --weights <weights-file>`.
4. Confirm the cfg/classes/weights family matches; route detailed compatibility questions to [../../model-and-config/SKILL.md](../../model-and-config/SKILL.md).
5. Use `scripts/check_image_pipeline.py` if the user only needs to verify image preprocessing/postprocessing without weights.

## No detections

Symptoms:

- The detector prints `No detections were made`.
- The output directory exists but no annotated images appear.
- The console lists no objects for images that should contain COCO classes.

Likely causes:

- `--confidence` is too high.
- The image path was wrong, unreadable, or directory filtering found no supported lowercase extensions.
- The cfg/weights/classes are mismatched or weights are not the expected COCO YOLOv3 weights.
- The image content is too small, heavily distorted, or outside the trained classes.

Recovery:

1. Confirm the image list: only lowercase `.jpg`, `.jpeg`, and `.png` are discovered in directory mode.
2. Run the no-weight helper with `--image` to prove OpenCV can read the file:

   ```bash
   python scripts/check_image_pipeline.py --image <image-file> --reso 64
   ```

3. Retry actual inference with a lower threshold such as `--confidence 0.25` or `--confidence 0.35`.
4. Keep `--nms_thresh 0.4` initially; tune it only after object-confidence filtering is plausible.
5. Check cfg/classes/weights alignment through `../model-and-config/SKILL.md` if the pipeline runs but labels or detections remain implausible.

## Bad `--reso` assertion

Symptoms:

- `AssertionError` soon after network load.
- Failure occurs around the input-resolution validation.

Likely causes:

- `--reso` is not divisible by 32.
- `--reso` is `32` or lower.
- The user passed a non-integer string.

Recovery:

- Use a valid value greater than 32 and divisible by 32, such as `64` for smoke checks or `320`, `416`, `608` for actual inference.
- On CPU, reduce resolution before increasing batch size.
- Re-run the helper with the same resolution to catch invalid values before loading weights:

  ```bash
  python scripts/check_image_pipeline.py --reso 416
  ```

## Image path or extension mistakes

Symptoms:

- `No file or directory with the name ...`.
- Directory mode silently processes fewer files than expected.
- OpenCV read failures or `NoneType`/`.shape` errors in preprocessing.

Likely causes:

- The command was run from a current working directory where the relative paths do not resolve.
- Directory mode ignores uppercase `.JPG`, `.JPEG`, `.PNG`, and non-supported formats.
- The path points to a directory when a single image was intended, or to a single file when a directory was intended.

Recovery:

1. Prefer absolute input/output paths in user-facing commands.
2. Rename or copy images to lowercase `.jpg`, `.jpeg`, or `.png` for directory mode.
3. Use `scripts/check_image_pipeline.py --image <image-file>` to verify a single file is readable before running model inference.
4. Keep output under a separate detection directory; the detector writes `det_<input-name>` there.

## OpenCV import or read failures

Symptoms:

- `ModuleNotFoundError: No module named 'cv2'`.
- `cv2.error` during resize/write.
- `AttributeError` involving `orig_im.shape` after image read.

Likely causes:

- OpenCV is not installed in the user's Python environment.
- The image file is corrupt, unsupported by the installed OpenCV codecs, inaccessible, or not an image.
- The output directory is not writable.

Recovery:

- Install an OpenCV build appropriate for the user's environment before actual inference.
- Validate one image with the bundled helper.
- Use standard `.jpg`, `.jpeg`, or `.png` images for detector directory mode.
- Check write permissions on the output directory if `cv2.imwrite` returns false or no annotated file appears.

## Class, cfg, and weights mismatch

Symptoms:

- Weight loading fails with tensor-size or layer-shape errors.
- Predictions run but labels are wrong or class ids are out of range.
- Changing names files produces inconsistent labels.

Likely causes:

- The default detector assumes 80 COCO classes.
- The cfg, names file, and weights are from different YOLO variants or datasets.
- The user changed class count without changing the final detection filters and weights accordingly.

Recovery:

- Route cfg, names, anchors, filters, and weight-format details to [../../model-and-config/SKILL.md](../../model-and-config/SKILL.md).
- For this image workflow, rebuild only the command flags after the model/config owner confirms the correct files.

## CPU and CUDA expectations

Symptoms:

- Runs are slow on CPU.
- CUDA out-of-memory errors when resolution or batch size is high.
- Device mismatch errors during low-level IoU/postprocessing checks.

Likely causes:

- Actual detector inference uses CUDA automatically when `torch.cuda.is_available()` is true.
- Larger `--reso` and `--bs` increase memory use.
- Some low-level helper code branches on CUDA availability rather than tensor device.

Recovery:

- For safe validation, use `scripts/check_image_pipeline.py --device cpu --reso 64`.
- For optional CUDA validation, use `scripts/check_image_pipeline.py --device cuda --reso 64` only when the user has a CUDA-capable environment.
- For actual inference on constrained hardware, use `--bs 1` and a smaller valid `--reso`, then increase gradually.
- Treat CUDA as acceleration, not as proof that CPU fallback works; run a CPU helper check when CPU support matters.

## Pandas and palette output issues

Symptoms:

- `ModuleNotFoundError: No module named 'pandas'` near output-name construction.
- Errors unpickling or opening `pallete` before drawing boxes.
- Detections print but annotated images are missing or drawing fails.

Likely causes:

- `pandas` is imported by the detector for output filename construction.
- The drawing path loads a local pickled color palette file named `pallete`.
- Output directory permissions or OpenCV write support are insufficient.

Recovery:

1. Install `pandas` in the runtime environment if actual detection reaches output construction.
2. Keep the palette file available alongside the detector entrypoint in the user's checkout when running actual inference.
3. Verify output path permissions.
4. Use the no-weight helper to isolate preprocessing/postprocessing from drawing/pandas/palette problems; the helper does not require weights, pandas, the palette file, GUI, or sample images.
