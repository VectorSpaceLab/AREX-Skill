# Segmentation Workflows

## Predict

The segmentation prediction entrypoint accepts image/video/directory/glob/list/webcam/screen/stream sources similarly to detection and adds mask-aware output options.

Common flags include:

- `--weights`: use a `*-seg.pt` checkpoint or exported segmentation artifact.
- `--source`: local image/video/directory or an explicitly approved stream.
- `--data`: class names/data config when needed.
- `--imgsz`, `--conf-thres`, `--iou-thres`, `--max-det`, `--device`.
- `--save-txt`, `--save-conf`, `--save-crop`, `--nosave`, `--classes`.
- `--augment`, `--half`, `--dnn`, `--vid-stride`, `--retina-masks`.
- `--project`, `--name`, `--exist-ok`.

Example shape:

```bash
python segment/predict.py --weights yolov5m-seg.pt --source data/images/bus.jpg --imgsz 640 --device cpu
```

Use the planner script to preview a command; it never downloads weights or opens media.

## Train

Segmentation training uses `segment/train.py` and a segmentation data config such as `coco128-seg.yaml`.

```bash
python segment/train.py --data coco128-seg.yaml --weights yolov5s-seg.pt --imgsz 640 --epochs 1 --device 0
```

For scratch training, use a matching `models/segment/*.yaml` with empty weights. DDP uses the torch distributed launcher and multiple devices.

Important choices:

- `--data` must describe segmentation labels and class names.
- `--weights` must be a segmentation checkpoint or be intentionally omitted for scratch training.
- `--imgsz`, batch size, cache, workers, and device determine memory/runtime.
- `--overlap` and mask downsample behavior affect label/metric semantics; read `data-formats.md` before changing them.
- Training creates run directories and may fetch weights/data.

## Validate

Use `segment/val.py` for box and mask metrics.

```bash
python segment/val.py --weights yolov5s-seg.pt --data coco.yaml --imgsz 640 --device cpu
```

The validation parser supports the common detection validation flags plus segmentation-specific `--overlap` and `--mask-downsample-ratio` behavior. Use `--save-json` or plot outputs only when required by the evaluation consumer.

## Export handoff

Segmentation checkpoints can use the shared export entrypoint:

```bash
python export.py --weights yolov5s-seg.pt --include onnx engine --imgsz 640 --device 0
```

Treat ONNX, TensorRT, CoreML, OpenVINO, TensorFlow, TFLite, Paddle, and Edge TPU as export sub-skill work. Export prerequisites and runtime compatibility are not guaranteed by a successful PyTorch segmentation run.
