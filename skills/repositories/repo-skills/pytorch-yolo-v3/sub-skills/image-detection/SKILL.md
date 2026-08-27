---
name: image-detection
description: "Guide pytorch-yolo-v3 image and directory detection,
  preprocessing, postprocessing, NMS, output interpretation, and safe smoke
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NO_LICENSE
---

# Image Detection

Use this sub-skill when a user asks to run or debug image/file-directory inference with the pytorch-yolo-v3 detector, interpret detector outputs, validate image preprocessing/postprocessing helpers, or perform a safe dry run that does not need weights.

## Route first

- Model architecture, cfg details, class-name/weight compatibility, or weight-loading internals: route to `../model-and-config/SKILL.md`.
- Video files, camera capture, GUI loops, or fp16 demo loops: route to `../video-camera-demos/SKILL.md`.
- Training, fine-tuning, dataset preparation for training, and weight downloads are out of scope.

## Safe operating policy

- Do not download weights, fetch data, open a GUI, use a camera, or write into a user's image directory as a default check.
- Actual image inference needs user-supplied local YOLO weights plus a matching cfg/classes setup; the bundled smoke helper deliberately does not load weights.
- Prefer CPU-safe checks first. CUDA can accelerate actual inference when PyTorch reports an available CUDA device, but do not require CUDA for preprocessing/postprocessing validation.
- When constructing an actual detection command, use only user-approved local image paths, output directories, cfg files, and weight files.

## What to consult inside this sub-skill

- `references/image-workflow.md` for image/directory discovery, exact detector flags, command templates, output naming, and result interpretation.
- `references/preprocessing-postprocessing.md` for the distilled preprocessing and postprocessing API contracts.
- `references/troubleshooting.md` for missing weights, no detections, bad resolution, image I/O, class/cfg/weight mismatch, CPU/CUDA, pandas, and palette failures.
- `scripts/check_image_pipeline.py` for a deterministic smoke check that creates a tiny image and exercises preprocessing, IoU, and NMS-style postprocessing without weights:

  ```bash
  python scripts/check_image_pipeline.py --reso 64
  ```

  To inspect a user's checkout modules without reading source files, pass the checkout root explicitly:

  ```bash
  python scripts/check_image_pipeline.py --repo-root <repo-root> --reso 64
  ```

- `scripts/run_image_detection.py` for a bundled dry-run/launcher wrapper around the repository image detector. It validates local paths and prints the command by default; add `--execute` only after the user approves loading local weights and writing annotated outputs:

  ```bash
  python scripts/run_image_detection.py --repo-root <repo-root> --images <image-or-dir> --det <output-dir> --weights <weights-file>
  ```
