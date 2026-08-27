---
name: "evaluation"
description: "Evaluate TensorRT SSD and YOLO object detectors on COCO-style bbox
  annotations with the repository's mAP scripts, preserving dataset contracts,
  class-ID mapping, legacy dependency gates, and historical benchmark context."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# COCO mAP evaluation

Use this skill when a Researcher needs to compare an SSD TensorFlow/TensorRT
model or a YOLO TensorRT engine against COCO-style object-detection ground
truth. It describes the repository's two evaluators; it does **not** download
COCO, build an engine, or claim that a modern host can run this legacy stack.
Keep any review reports, generated result JSON, and full evaluation logs outside
this runtime skill tree.

## Applicability and hard gates

- The supported SSD model names are exactly `ssd_mobilenet_v1_coco` and
  `ssd_mobilenet_v2_coco`; SSD `--mode` is `trt` by default and can be `tf`.
- YOLO requires a serialized engine at `yolo/<model>.trt`, a built
  `plugins/libyolo_layer.so`, TensorRT, PyCUDA, OpenCV, `pycocotools`, and
  `progressbar2`. Its model string is a YOLO family plus input size, such as
  `yolov3-tiny-288` or `yolov4-416`; see the model list in
  [benchmarks.md](references/benchmarks.md).
- `eval_ssd.py` imports `tensorflow` only through `utils.ssd_tf`, so even
  `--mode trt` can be blocked by a missing/incompatible TensorFlow 1.x stack.
  Preserve the signal; do not hide it by editing imports or claiming a partial
  evaluation is a full one.
- `eval_yolo.py` imports `utils.yolo_with_plugins` at startup. A missing
  `./plugins/libyolo_layer.so` produces its explicit “failed to load” error;
  `make` in `plugins/` is a prerequisite, but this skill does not run the build.
- `pycuda.autoinit` means both scripts need a usable CUDA driver/context even
  when the requested task is only to inspect the CLI. `pycocotools` and
  `progressbar2` are separate Python requirements.
- Do not start a 5,000-image or network-backed run in a verification pass.
  First validate a tiny local fixture with the bundled script, then obtain
  explicit task approval for a real dataset and GPU run.

## Source-of-truth workflow

1. Confirm the model, precision/engine variant, dataset split, image directory,
   annotation file, class vocabulary, and desired comparison. Record the exact
   git revision and TensorRT/JetPack environment in the experiment log.
2. Check a local dataset layout without mutating it. The default paths are
   `${HOME}/data/coco/images/val2017` and
   `${HOME}/data/coco/annotations/instances_val2017.json`. A custom dataset must
   be converted to COCO Object Detection `bbox` format and must satisfy the
   result contracts below.
3. Verify the engine/model and dependencies before inference. Run `--help` or
   a tiny fixture check first; do not infer engine correctness from a parser
   check. For TensorFlow SSD, confirm the legacy TensorFlow graph can load.
4. Run the selected evaluator from the repository root so its relative output
   and engine paths resolve:

   ```bash
   # SSD (one model name is mandatory)
   python3 eval_ssd.py --mode trt \
     --imgs_dir "$HOME/data/coco/images/val2017" \
     --annotations "$HOME/data/coco/annotations/instances_val2017.json" \
     ssd_mobilenet_v1_coco

   # TensorFlow frozen graph comparison (legacy TF dependency)
   python3 eval_ssd.py --mode tf ssd_mobilenet_v1_coco

   # YOLO (engine name is mandatory)
   python3 eval_yolo.py --imgs_dir "$HOME/data/coco/images/val2017" \
     --annotations "$HOME/data/coco/annotations/instances_val2017.json" \
     -m yolov4-416

   # YOLO letterbox preprocessing, if the engine was configured for it
   python3 eval_yolo.py -l -m yolov4-csp-256
   ```

5. Preserve the generated result file and the complete `COCOeval.summarize()`
   output. SSD writes `ssd/results_<model>_<mode>.json`; YOLO writes
   `yolo/results_<model>.json`. These are overwritten on a subsequent run, so
   copy or rename them into an external experiment directory first.
6. Report the primary COCO AP (IoU 0.50:0.95, all areas, maxDets=100), AP50,
   AP75, area-specific AP, and AR values. Include image count, annotation
   revision, evaluator mode, model/engine, input/letterbox behavior, and
   confidence/NMS behavior so comparisons are reproducible.

## What the scripts actually do

Both programs list every filename ending in `.jpg`, derive an integer image ID
from the final underscore-separated token before `.jpg` (for example,
`COCO_val2017_000000123456.jpg` → `123456`), invoke a detector at
`conf_th=1e-2`, write detections, load the annotation with `COCO`, then run
`COCOeval(..., 'bbox')` over sorted ground-truth image IDs. The scripts do not
filter the directory to annotation IDs before inference. Therefore filenames
must encode valid IDs and the directory should contain only the intended split.
A missing/unreadable image can fail later in OpenCV/model code; validate the
layout before a long run.

SSD converts detector corner coordinates to COCO `[x, y, width, height]` using
`width = x2 - x1 + 1` and `height = y2 - y1 + 1`. TensorRT SSD postprocessing
scales normalized corners to the original image dimensions; TensorFlow SSD
scales normalized `[ymin, xmin, ymax, xmax]` and swaps to x/y corners. The
supported SSD COCO checkpoints emit COCO-compatible category IDs.

YOLO uses the same corner-to-xywh conversion. By default it translates YOLO's
contiguous 0–79 COCO class IDs through `utils.yolo_classes.yolo_cls_to_ssd` to
COCO/SSD category IDs (which are non-contiguous and include gaps). Pass
`--non_coco` only when the annotation category IDs intentionally match the
model's raw class IDs; using it against standard COCO annotations silently
corrupts the evaluation. `-c/--category_num` must be positive and must match
the engine's configured class count. `-l/--letter_box` must match how the model
expects preprocessing; the postprocessor compensates coordinates for the
letterbox padding.

For exact input/output and annotation constraints, read:

- [workflows.md](references/workflows.md) for flags, sequencing, and safe
  execution gates;
- [data-formats.md](references/data-formats.md) for image IDs, COCO JSON,
  categories, and detection result invariants;
- [benchmarks.md](references/benchmarks.md) for historical SSD/YOLO tables and
  interpretation boundaries;
- [troubleshooting.md](references/troubleshooting.md) for blocked dependencies,
  class mapping, path, and metric diagnosis.

## Verification and recovery

Run the dependency-free checker against a tiny fixture only:

```bash
python3 skills/disco/tensorrt-demos/sub-skills/evaluation/scripts/validate-coco-eval-layout.py \
  --images-dir /path/to/tiny/images \
  --annotations /path/to/tiny/instances.json \
  --results /path/to/tiny/results.json
```

The checker validates file existence, JPEG filename-to-ID parsing, COCO-like
`images`/`annotations`/`categories` structure, result fields, numeric bbox and
score values, positive dimensions, and that result image/category IDs are
present in the ground truth. It does not import TensorRT, TensorFlow, PyCUDA,
OpenCV, or `pycocotools`; it does not run inference or compute mAP. Its success
is only a layout gate. If it fails, repair the dataset/results contract before
spending GPU time. If a real run fails after the layout gate, retain the exact
stderr and classify the failure as an environment, engine/plugin, dataset, or
semantic class-mapping blocker.

Do not use a tiny fixture's mAP as a model-quality estimate. A tiny fixture can
prove deterministic plumbing and a perfect-box result can prove result
serialization, but only the declared validation split supports comparison to
the historical numbers.

## Non-goals and evidence limits

This skill does not prescribe downloading COCO, changing the evaluator to
support arbitrary filename conventions, converting custom annotations, fixing
TensorRT plugin ABI mismatches, or modernizing TensorFlow 1 APIs. It records
repository behavior observed in `README_mAP.md`, `eval_ssd.py`, `eval_yolo.py`,
`utils/ssd.py`, `utils/ssd_tf.py`, `utils/yolo_with_plugins.py`,
`utils/yolo_classes.py`, and the model tables in `README.md`. Historical values
are reference observations, not guarantees on another GPU, TensorRT version,
engine build, preprocessing mode, or dataset.
