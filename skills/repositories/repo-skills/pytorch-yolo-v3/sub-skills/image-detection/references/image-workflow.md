# Image Detection Workflow

## Purpose

Read this when constructing or debugging still-image inference for pytorch-yolo-v3. It distills the detector CLI behavior, image discovery rules, output naming, and safe preflight checks so future agents do not need to reopen source files or external documentation.

## Safe preflight

1. Confirm whether the user wants actual image inference or a no-weight dry run.
2. For no-weight environment/API validation, use the bundled smoke helper:

   ```bash
   python scripts/check_image_pipeline.py --reso 64
   python scripts/check_image_pipeline.py --repo-root <repo-root> --reso 64
   ```

3. For actual inference, prefer the bundled launcher wrapper first. It validates local files and prints the command by default; it does not download weights:

   ```bash
   python scripts/run_image_detection.py \
     --repo-root <repo-root> \
     --images <image-or-directory> \
     --det <output-directory> \
     --cfg cfg/yolov3.cfg \
     --weights <local-yolov3-weights> \
     --reso 416
   ```

4. Add `--execute` to the wrapper only after the user approves loading local weights and writing annotated output images.
5. Do not download `yolov3.weights` by default. Actual inference requires the user to provide a local weights file.
6. Prefer a small batch size on CPU. CUDA is optional acceleration, not a requirement for the dry run.

## Detector flags wrapped by `run_image_detection.py`

The repository image detector exposes these flags; the bundled wrapper validates and forwards them.

| Flag | Default | Meaning |
| --- | --- | --- |
| `--images` | `imgs` in the source entrypoint; required by the bundled wrapper | Image file path or directory containing images to detect. |
| `--det` | `det` in the source entrypoint; required by the bundled wrapper | Directory where annotated images are written. Created by the detector if missing. |
| `--bs` | `1` | Batch size. Parsed to `int` before batching. |
| `--confidence` | `0.5` | Object-confidence threshold passed to postprocessing. Parsed to `float`. |
| `--nms_thresh` / wrapper `--nms-thresh` | `0.4` | NMS IoU threshold passed as `nms_conf`. |
| `--cfg` | `cfg/yolov3.cfg` | Model cfg path. Route cfg/architecture details to [../../model-and-config/SKILL.md](../../model-and-config/SKILL.md). |
| `--weights` | `yolov3.weights` | Local Darknet weights path. The repo does not bundle these weights. |
| `--reso` | `416` | Network input resolution as a string parsed to `int`; must be a multiple of 32 and greater than 32. |
| `--scales` | `1,2,3` | Accepted by the parser. Scale-index filtering is present in comments/disabled code, so do not rely on it as an active feature unless the user has modified the checkout. |

Use `scripts/run_image_detection.py --help` for the wrapper interface. The wrapper's dry-run mode is the preferred way to prepare real commands because it avoids accidental weight loading or output writes.

## Image path and directory behavior

- `--images` may be either a single image path or a directory.
- Directory mode lists only files whose extension is exactly `.png`, `.jpeg`, or `.jpg` in lowercase. Files such as `.JPG`, `.webp`, `.bmp`, or extensionless images are ignored by the detector's directory discovery.
- Single-file mode appends the provided path after directory listing raises `NotADirectoryError`; the detector does not perform the same extension filter for a single file, but OpenCV still must be able to read it.
- If the path does not exist, the detector prints `No file or directory with the name <value>` and exits.
- The detector builds directory-mode image paths relative to the detector process working directory. The bundled wrapper runs the detector from the supplied `--repo-root` so relative cfg/data/palette assumptions resolve against the user's checkout.

## Output naming and interpretation

- The output directory from `--det` is created if it does not already exist.
- Each annotated image is written as `det_<input-name>` inside the detection directory. Example: input `dog.jpg` with `--det det` writes `det/det_dog.jpg`.
- Console output is printed per processed batch/image. For each image with retained predictions, expect lines similar to:

  ```text
  image-name.jpg        predicted in  0.123 seconds
  Objects Detected:     person dog car
  ----------------------------------------------------------
  ```

- If no predictions survive thresholding and NMS for all images, the detector prints `No detections were made` and exits before writing annotated detections.
- A final `SUMMARY` block reports reading, batch loading, detection, output processing, drawing, and average time per image.

## Command templates

Dry-run a single-image command with concrete user paths:

```bash
python scripts/run_image_detection.py \
  --repo-root <repo-root> \
  --images <image-file> \
  --det <output-directory> \
  --cfg cfg/yolov3.cfg \
  --weights <local-yolov3-weights> \
  --reso 416 \
  --confidence 0.5 \
  --nms-thresh 0.4 \
  --bs 1
```

Execute only after approval:

```bash
python scripts/run_image_detection.py \
  --repo-root <repo-root> \
  --images <image-file> \
  --det <output-directory> \
  --weights <local-yolov3-weights> \
  --execute
```

Directory of lowercase `.jpg`, `.jpeg`, and `.png` images:

```bash
python scripts/run_image_detection.py \
  --repo-root <repo-root> \
  --images <image-directory> \
  --det <output-directory> \
  --cfg cfg/yolov3.cfg \
  --weights <local-yolov3-weights> \
  --reso 320 \
  --confidence 0.35 \
  --nms-thresh 0.4 \
  --bs 1
```

Safe no-weight pipeline check from this sub-skill directory:

```bash
python scripts/check_image_pipeline.py --reso 64 --confidence 0.5 --nms-thresh 0.4
```

Safe checkout-module inspection without weights:

```bash
python scripts/check_image_pipeline.py \
  --repo-root <repo-root> \
  --image <image-file> \
  --reso 64 \
  --confidence 0.5 \
  --nms-thresh 0.4
```

## Threshold and resolution tuning

- Lower `--confidence` when the model runs successfully but prints `No detections were made`; try `0.25` or `0.35` before changing model files.
- Raise `--confidence` when too many low-quality boxes survive.
- Lower `--nms_thresh` to suppress more overlapping boxes; raise it to keep more overlapping candidates.
- `--reso` trades speed and accuracy. It must satisfy both constraints: divisible by 32 and greater than 32. Common valid values include `320`, `416`, `608`, and the smoke-check value `64`.
- On CPU, prefer smaller `--reso` and `--bs 1` unless the user explicitly accepts slower inference.
