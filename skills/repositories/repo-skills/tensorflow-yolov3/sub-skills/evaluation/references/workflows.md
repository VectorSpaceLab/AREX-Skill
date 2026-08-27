# Workflows

## 1) Evaluate a trained checkpoint

Before running the evaluator, make sure these fields line up with the checkpoint and dataset:

- `cfg.YOLO.CLASSES` — one class name per line, in the same order used during training.
- `cfg.YOLO.ANCHORS` — the anchor file expected by the checkpoint.
- `cfg.TEST.ANNOT_PATH` — the split file with `image_path xmin,ymin,xmax,ymax,class_id ...` rows.
- `cfg.TEST.WEIGHT_FILE` — the checkpoint file to restore.
- `cfg.TEST.WRITE_IMAGE_PATH` — a disposable directory, because `evaluate.py` removes it before writing.
- `cfg.TEST.WRITE_IMAGE` — controls whether drawn images are written.
- `cfg.TEST.SHOW_LABEL` — controls label rendering on written images.
- `cfg.TEST.INPUT_SIZE`, `cfg.TEST.SCORE_THRESHOLD`, `cfg.TEST.IOU_THRESHOLD` — evaluation geometry and filtering.

A minimal VOC-style configuration usually looks like this:

```python
__C.YOLO.CLASSES = "./data/classes/voc.names"
__C.YOLO.ANCHORS = "./data/anchors/basline_anchors.txt"
__C.TEST.ANNOT_PATH = "./data/dataset/voc_test.txt"
__C.TEST.WEIGHT_FILE = "./checkpoint/yolov3_test_loss=9.2099.ckpt-5"
__C.TEST.WRITE_IMAGE = True
__C.TEST.WRITE_IMAGE_PATH = "./data/detection/"
__C.TEST.SHOW_LABEL = True
__C.TEST.INPUT_SIZE = 544
__C.TEST.SCORE_THRESHOLD = 0.30
__C.TEST.IOU_THRESHOLD = 0.45
```

Run the evaluation from the repository root:

```bash
python evaluate.py
```

That script writes numbered files under:

- `./mAP/ground-truth/`
- `./mAP/predicted/`
- `./data/detection/` when `cfg.TEST.WRITE_IMAGE` is enabled

Then compute Pascal VOC-style AP/mAP from inside `mAP/`:

```bash
cd mAP
python main.py -na -np -q
```

Expected outputs from `mAP/main.py` include:

- `results/results.txt`
- `results/mAP.png` when plots are enabled
- `results/classes/*.png` when plots are enabled
- temporary JSON files under `tmp_files/`

## 2) Re-run mAP with ignored classes or per-class IoU

Use these flags when you want to adjust scoring without regenerating predictions:

```bash
cd mAP
python main.py -na -np -q --ignore person bicycle --set-class-iou person 0.75 bicycle 0.60
```

Notes:

- `--ignore` removes classes from AP counting and class histograms.
- `--set-class-iou` takes alternating class / IoU entries.
- The IoU values must be strictly between `0.0` and `1.0`.
- Keep the class names exactly as they appear in the text files.

## 3) Validate a hand-built mAP fixture

Run the bundled smoke checker before handing a file pair to `mAP/main.py`:

```bash
python scripts/map_fixture_check.py
```

The checker creates an isolated tiny fixture and validates:

- ground-truth line parsing,
- predicted line parsing,
- stem pairing,
- AP expectations for a perfect match,
- the class-name-mismatch case,
- the missing-predicted-counterpart case.

## 4) VOC test-set export helper

`YoloTest.voc_2012_test(voc2012_test_path)` is a separate export path inside `evaluate.py`.
It expects:

- `ImageSets/Main/test.txt`
- `JPEGImages/`

It writes per-class detection files under `results/VOC2012/Main/comp4_det_test_<class>.txt`.
