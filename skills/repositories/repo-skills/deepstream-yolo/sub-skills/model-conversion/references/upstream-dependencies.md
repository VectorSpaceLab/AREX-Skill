# Upstream dependency notes

## Bundled / verified stack

| Family | Upstream dependency | Notes |
| --- | --- | --- |
| YOLOv8, YOLO11, YOLOv10, YOLOv12, YOLOv13, YOLO26, YOLO-Master, YOLOv5u, RT-DETR Ultralytics | `ultralytics`, `torch`, `onnx`, `onnxslim`, `onnxruntime` | Verified in the inspection environment; exporter scripts are bundled under `scripts/` |

## Reference-only stacks

| Family group | Upstream dependency | Why reference-only here |
| --- | --- | --- |
| YOLOv5 legacy, YOLOv6, YOLOv7, YOLOv7-u6, YOLOv9 legacy, YOLOR, YOLOX | their legacy repo-specific `models` / `utils` / `yolov6` / `yolox` packages | separate codebases and external repo layouts were not installed in the confirmed Python environment |
| PP-YOLOE / PP-YOLOE+ and RT-DETR Paddle | PaddlePaddle, PaddleDetection, `paddle2onnx` | the Paddle stack is heavier and was excluded from the confirmed inspection scope |
| RTMDet / CO-DETR | MMDetection / MMYOLO / `mmengine` | requires the OpenMMLab stack outside the confirmed scope |
| YOLO-NAS | Super-Gradients | not installed in the confirmed scope |
| DAMO-YOLO | DAMO-YOLO repo stack | not installed in the confirmed scope |
| Gold-YOLO | YOLOv6/Gold-YOLO stack | not installed in the confirmed scope |
| D-FINE | D-FINE repo stack | not installed in the confirmed scope |
| RF-DETR | RF-DETR package | not installed in the confirmed scope |

## Practical rule

If the family is not in the bundled verified table, keep the task in the reference-only matrix unless a future environment-preparation pass explicitly installs the required upstream stack.
