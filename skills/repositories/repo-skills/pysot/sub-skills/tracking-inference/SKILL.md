---
name: tracking-inference
description: "Run PySOT tracking demos, benchmark tests, and tracker APIs safely
  with validated config/snapshot/video/dataset inputs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PySOT tracking inference

Use this sub-skill when the task is to run or debug PySOT inference rather than to redesign a model or evaluate benchmark metrics.

## Read when

- The user wants a PySOT demo from webcam, a video file, or an image sequence.
- The user has a config and snapshot and asks how to track an object or load a checkpoint.
- The user wants to call `build_tracker`, `tracker.init(img, bbox)`, or `tracker.track(img)` directly.
- The user wants to construct a `tools/test.py` benchmark run or understand where it writes result files.
- The user reports wrong `bbox`, `best_score`, `mask`, or `polygon` outputs.

## Start here

1. Confirm the user has a PySOT checkout/import context, a config YAML, and a snapshot file. PySOT's package metadata installs `toolkit`; importing `pysot` normally depends on running from the checkout, setting `PYTHONPATH`, or equivalent editable-development registration.
2. Run the bundled safe preflight before any GUI, CUDA, dataset, or snapshot-loading workflow:

   ```bash
   python scripts/validate_tracking_inputs.py \
     --mode demo \
     --config path/to/config.yaml \
     --snapshot path/to/model.pth \
     --video-name path/to/video.mp4
   ```

   The helper checks paths and config basics and prints a command skeleton. It does not open OpenCV, load weights, download datasets, or run tracking.
3. For CLI workflows, follow [references/workflows.md](references/workflows.md).
4. For direct Python API usage, follow [references/tracker-api.md](references/tracker-api.md).
5. For failures, inspect [references/troubleshooting.md](references/troubleshooting.md) before changing source code.

## Boundaries and routing

- Stay here for demo/test command construction, tracker loading, tracker API lifecycle, output file locations, and inference-specific failures.
- Route config edits, model-family selection, architecture mismatches, and deep `cfg`/`ModelBuilder` tables to the sibling `configuration-models` sub-skill.
- Route metric interpretation, `eval.py`, result-layout validation, benchmark scoring, and hyperparameter search to the sibling `evaluation-toolkit` sub-skill.
- Route training from scratch, training snapshots, data cropping, and training dataset preparation to the sibling `training-data` sub-skill.

## Safety notes

- Full native demo runs are GUI/webcam/video/snapshot-bound and need user artifacts.
- Full native benchmark runs need a user-supplied dataset and snapshot. The source benchmark path calls `.cuda()`, so treat CUDA as required unless the user explicitly adapts the script for CPU.
- Do not use a full `test.py`, training, or evaluation run as a default smoke check. Use parser help and the bundled validator for safe preflight.
