# Detection Workflows

## Predict / infer

`detect.py` is the main detection inference CLI. Common sources include:

- `0` or another integer webcam index
- a local image or video path
- a directory of images or videos
- a glob pattern
- a list file containing sources
- a YouTube, RTSP, RTMP, or HTTP stream URL
- `screen` for screen capture

The inspected CLI parser supports flags such as `--weights`, `--source`, `--data`, `--imgsz`, `--conf-thres`, `--iou-thres`, `--max-det`, `--device`, `--view-img`, `--save-txt`, `--save-format`, `--save-csv`, `--save-conf`, `--save-crop`, `--nosave`, `--classes`, `--agnostic-nms`, `--augment`, `--update`, `--project`, `--name`, `--exist-ok`, `--line-thickness`, `--hide-labels`, `--hide-conf`, `--half`, `--dnn`, and `--vid-stride`.

Practical guidance:

- Prefer explicit local input paths for deterministic runs.
- Use `--nosave` when you only need parsed predictions.
- Choose `--device cpu` for parser checks or when no GPU is available.
- Use `--half` only on compatible CUDA devices.
- Use `--save-txt`/`--save-csv` only when downstream parsing is needed.
- Keep `--project`/`--name` explicit to avoid run-directory collisions.

### Example command shapes

```bash
python detect.py --weights yolov5s.pt --source data/images/zidane.jpg --imgsz 640 --device cpu
python detect.py --weights yolov5s.pt --source 0 --view-img --device 0
python detect.py --weights yolov5s.pt --source 'path/to/*.jpg' --nosave
```

Use `sub-skills/detection/scripts/plan_detection_command.py` to preview a command and see warnings before execution.

## Train

`train.py` supports single-GPU and DDP training.

Common flags from the inspected parser include `--weights`, `--cfg`, `--data`, `--hyp`, `--epochs`, `--batch-size`, `--imgsz`, `--rect`, `--resume`, `--nosave`, `--noval`, `--noautoanchor`, `--noplots`, `--evolve`, `--evolve_population`, `--cache`, `--image-weights`, `--device`, `--multi-scale`, `--single-cls`, `--optimizer`, `--sync-bn`, `--workers`, `--project`, `--name`, `--exist-ok`, `--quad`, `--cos-lr`, `--label-smoothing`, `--patience`, `--freeze`, `--save-period`, `--seed`, `--local_rank`, `--entity`, `--upload_dataset`, `--bbox_interval`, `--artifact_alias`, `--ndjson-console`, and `--ndjson-file`.

Guidance:

- Use a tiny dataset like `coco128.yaml` for smoke-scale work.
- From scratch, pair `--cfg` with `--weights ''`.
- Fine-tuning usually uses pretrained weights and an appropriate data YAML.
- DDP requires the appropriate launch command and multiple devices.
- Training writes under `--project`/`--name` and may create many artifacts.

### Example command shapes

```bash
python train.py --data coco128.yaml --weights yolov5s.pt --imgsz 640 --batch-size 16 --device 0
python train.py --data coco128.yaml --weights '' --cfg yolov5s.yaml --imgsz 640 --batch-size 16
python -m torch.distributed.run --nproc_per_node 4 --master_port 1 train.py --data coco128.yaml --weights yolov5s.pt --device 0,1,2,3
```

## Validate

`val.py` handles detection validation and many exported formats. The inspected parser includes `--data`, `--weights`, `--batch-size`, `--imgsz`, `--conf-thres`, `--iou-thres`, `--max-det`, `--task`, `--device`, `--workers`, `--single-cls`, `--augment`, `--verbose`, `--save-txt`, `--save-hybrid`, `--save-conf`, `--save-json`, `--project`, `--name`, `--exist-ok`, `--half`, and `--dnn`.

Guidance:

- Choose `--task val` for accuracy-style checks and `--task speed` for throughput-style checks.
- Use `--save-json` only when the evaluation path consumes JSON output.
- Use `--augment` for test-time augmentation only when the user wants it.
- Some exported formats require `--dnn` or other backend-specific options.

### Example command shapes

```bash
python val.py --weights yolov5s.pt --data coco128.yaml --imgsz 640
python val.py --weights yolov5s.pt --data coco.yaml --task speed --batch-size 1
python val.py --weights yolov5s.pt --data coco.yaml --imgsz 1536 --iou-thres 0.7 --augment
```

## PyTorch Hub

Hub loading is the usual lightweight API path for custom code:

```python
import torch
model = torch.hub.load("ultralytics/yolov5", "yolov5s")
results = model("data/images/zidane.jpg")
```

Key notes:

- `yolov5n`/`yolov5s`/... names load standard detection checkpoints.
- `custom(path)` loads a local or checkpoint path.
- `autoshape=True` is useful for file/URI/PIL/cv2/numpy inputs.
- Segmentation and classification models are not fully AutoShape-compatible in all cases; use the task-specific sub-skill instead.
- Hub may download checkpoints and use cache; avoid cache/network mutation unless the task authorizes it.

## Validation and output tips

- Detection outputs are boxes with confidence and class ids/names.
- Use local test images such as `bus.jpg` or `zidane.jpg` only as evidence and smoke fixtures, not as a hard runtime dependency in generated skill content.
- Keep `--device`, `--imgsz`, `--weights`, and `--data` explicit to avoid ambiguous defaults.
