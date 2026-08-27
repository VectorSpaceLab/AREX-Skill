# Evaluation workflows and flags

This reference is a procedural companion to the evaluation skill. Commands are
shown for a checkout rooted at the repository root. Replace paths explicitly;
do not rely on the defaults when documenting a custom split.

## Common preparation gate

Before either evaluator:

1. Identify the exact model/engine, precision (FP16/INT8/DLA where relevant),
   TensorRT version, JetPack or host platform, and source revision.
2. Confirm that the image directory contains only the intended `.jpg` split and
   that each filename's final numeric token is the corresponding COCO `image_id`.
   The programs do not sort the directory listing and do not limit inference to
   annotation IDs.
3. Confirm the annotation JSON is a COCO detection annotation file and that its
   `images`, `annotations`, and `categories` agree with the result vocabulary.
4. Run the bundled tiny-layout checker. This is deliberately CPU-only and does
   not substitute for inference or COCOeval.
5. Confirm dependencies and engine artifacts. Do not download the 5K COCO
   validation set as part of skill verification.

The repository's documented default dataset locations are:

```text
${HOME}/data/coco/images/val2017/*.jpg
${HOME}/data/coco/annotations/instances_val2017.json
```

`README_mAP.md` describes COCO 2017 val images and train/val annotations, but a
real run requires the user to provide or approve those data. The evaluator
writes result JSON beneath `ssd/` or `yolo/`, relative to the current working
directory, so archive the file before rerunning.

## SSD evaluator

### CLI contract

```text
python3 eval_ssd.py [--mode {tf,trt}] [--imgs_dir IMGS_DIR]
                    [--annotations ANNOTATIONS]
                    {ssd_mobilenet_v1_coco,ssd_mobilenet_v2_coco}
```

- `model` is required and restricted to the two COCO MobileNet checkpoints.
- `--mode trt` is the default and constructs `utils.ssd.TrtSSD`, loading
  `ssd/TRT_<model>.bin`.
- `--mode tf` constructs `utils.ssd_tf.TfSSD`, loading `ssd/<model>.pb` and
  requiring the repository's legacy TensorFlow graph API.
- `--imgs_dir` defaults to `${HOME}/data/coco/images/val2017` and must be a
  directory.
- `--annotations` defaults to `${HOME}/data/coco/annotations/instances_val2017.json`
  and must be a file.

Run from the checkout root. Examples:

```bash
python3 eval_ssd.py --mode trt ssd_mobilenet_v1_coco
python3 eval_ssd.py --mode tf  ssd_mobilenet_v2_coco
python3 eval_ssd.py --mode trt --imgs_dir ./tiny/images \
  --annotations ./tiny/instances.json ssd_mobilenet_v2_coco
```

The last command is only a valid *execution shape* if a compatible engine and
runtime are present; the tiny checker is the safe verification path.

For every JPEG, the SSD detector is called with confidence threshold `0.01`.
SSD TensorRT preprocessing resizes to `(300, 300)`, converts BGR to RGB, and
normalizes channels to approximately `[-1, 1]`. TensorFlow SSD uses its own
input preprocessing helper and returns normalized boxes. These preprocessing
paths are part of the mode comparison; do not call a TF-vs-TRT difference an
engine precision regression without checking them.

Result path:

```text
ssd/results_<model>_<mode>.json
```

### SSD sequence

1. `check_args()` checks only that the image directory and annotation path
   exist.
2. The detector is constructed before images are enumerated.
3. Each `.jpg` is read with OpenCV and passed to `detect(img, conf_th=1e-2)`.
4. Detections are serialized as COCO result dictionaries.
5. `COCO(args.annotations)` loads ground truth; `loadRes(results_file)` loads
   detections; `COCOeval(cocoGt, cocoDt, 'bbox')` evaluates sorted ground-truth
   image IDs; `evaluate()`, `accumulate()`, and `summarize()` emit metrics.

## YOLO evaluator

### CLI contract

```text
python3 eval_yolo.py [--imgs_dir IMGS_DIR] [--annotations ANNOTATIONS]
                     [--non_coco] [-c CATEGORY_NUM] -m MODEL [-l]
```

- `-m/--model` is required. The script checks for `yolo/<model>.trt`.
- `--imgs_dir` and `--annotations` have the same COCO defaults as SSD and are
  existence-checked.
- `--non_coco` disables the default raw-YOLO-to-COCO category translation. Use
  this only for annotations whose category IDs intentionally equal raw model
  IDs.
- `-c/--category_num` defaults to `80` and must be greater than zero. It must
  match the engine's configured category count; custom class counts are not
  automatically made COCO-compatible.
- `-l/--letter_box` enables aspect-ratio-preserving preprocessing and inverse
  padding correction. Use the same setting used by the engine/inference task.

Examples from the repository's documented usage:

```bash
python3 eval_yolo.py -m yolov3-tiny-288
python3 eval_yolo.py -m yolov4-tiny-416
python3 eval_yolo.py -m yolov4-608
python3 eval_yolo.py -l -m yolov4-csp-256
python3 eval_yolo.py -l -m yolov4x-mish-640
```

Result path:

```text
yolo/results_<model>.json
```

### YOLO sequence and coordinate behavior

The script imports `TrtYOLO`, which loads `./plugins/libyolo_layer.so`, then
checks the engine file, constructs the engine wrapper, and calls
`detect(img, conf_th=1e-2)` for each JPEG. The wrapper filters detections by
`box_confidence * class_probability`, applies per-class NMS at threshold `0.5`,
scales coordinates to the original image, and clips corners to image bounds.
The evaluator then writes `[x, y, width, height]` using the repository's `+1`
corner conversion.

When letterbox mode is enabled, preprocessing puts the resized image on a
value-127 canvas. Postprocessing subtracts the computed padding offsets before
clipping. A mismatch between engine construction, inference flags, and
`eval_yolo.py -l` can produce plausible-looking but systematically misplaced
boxes and a large AP loss.

By default, `eval_yolo.py` maps each raw class index through
`yolo_cls_to_ssd`, because YOLO's 80 contiguous COCO labels differ from the
non-contiguous COCO category IDs used by the SSD/COCO annotation convention.
The mapping is not a generic custom-label converter. For custom training, build
and validate an explicit mapping and use `--non_coco` only when the ground
truth was deliberately authored with raw IDs.

## Metric collection and stop rules

Capture stdout/stderr and record:

- number of input JPEGs and annotation images;
- result file path and a checksum if it will be compared later;
- model, mode, engine precision, TensorRT/JetPack, GPU, and letterbox flag;
- `COCOeval` AP/AR summary, not just one rounded mAP value;
- any skipped, unreadable, or extra images and all dependency errors.

Stop before inference if paths, IDs, categories, or result layout fail the tiny
checker. Stop and classify rather than bypassing a missing YOLO plugin,
TensorFlow graph runtime, CUDA context, TensorRT engine, or `pycocotools`.
Never claim COCO mAP from a parser/help run or from a tiny fixture.
