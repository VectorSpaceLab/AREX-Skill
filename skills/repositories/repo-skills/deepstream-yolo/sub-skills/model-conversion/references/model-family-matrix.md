# Model-conversion matrix

This matrix tells a future agent which exporter to use and whether the exporter is bundled or reference-only in this skill.

## Bundled Ultralytics-family exporters

| Script | Family | Upstream repo expectation | Status |
| --- | --- | --- | --- |
| `scripts/export_yoloV8.py` | YOLOv8 | `ultralytics` checkout or installed package | bundled |
| `scripts/export_yolo11.py` | YOLO11 | `ultralytics` checkout or installed package | bundled |
| `scripts/export_yoloV10.py` | YOLOv10 | `ultralytics` checkout or installed package | bundled |
| `scripts/export_yolov12.py` | YOLOv12 | `ultralytics` checkout or installed package | bundled |
| `scripts/export_yoloV13.py` | YOLOv13 | `ultralytics` checkout or installed package | bundled |
| `scripts/export_yolo26.py` | YOLO26 | `ultralytics` checkout or installed package | bundled |
| `scripts/export_yolomaster.py` | YOLO-Master | `ultralytics` checkout or installed package | bundled |
| `scripts/export_yoloV5u.py` | YOLOv5u | `ultralytics` checkout or installed package | bundled |
| `scripts/export_rtdetr_ultralytics.py` | RT-DETR (Ultralytics) | `ultralytics` checkout or installed package | bundled |

## Reference-only exporter families

| Family / source script | Upstream repo or stack | Reason it stays reference-only here |
| --- | --- | --- |
| `utils/export_yoloV5.py` | legacy YOLOv5 repo | external repo layout differs from the bundled Ultralytics path |
| `utils/export_yoloV6.py` | YOLOv6 repo | separate dependency stack |
| `utils/export_yoloV7.py` | YOLOv7 repo | separate dependency stack |
| `utils/export_yoloV7_u6.py` | YOLOv7-u6 repo | separate dependency stack |
| `utils/export_yoloV9.py` | legacy YOLOv9 repo | separate dependency stack |
| `utils/export_yolor.py` | YOLOR repo | separate dependency stack |
| `utils/export_yolox.py` | YOLOX repo | separate dependency stack |
| `utils/export_ppyoloe.py` | PaddleDetection / PaddlePaddle | heavy Paddle stack outside confirmed scope |
| `utils/export_rtdetr_paddle.py` | PaddleDetection / PaddlePaddle | heavy Paddle stack outside confirmed scope |
| `utils/export_rtmdet.py` | MMDetection / MMYOLO | OpenMMLab stack outside confirmed scope |
| `utils/export_codetr.py` | MMDetection | OpenMMLab stack outside confirmed scope |
| `utils/export_goldyolo.py` | Gold-YOLO / YOLOv6 stack | separate stack outside confirmed scope |
| `utils/export_damoyolo.py` | DAMO-YOLO | separate stack outside confirmed scope |
| `utils/export_yolonas.py` | Super-Gradients | separate stack outside confirmed scope |
| `utils/export_dfine.py` | D-FINE | separate stack outside confirmed scope |
| `utils/export_rfdetr.py` | RF-DETR | separate stack outside confirmed scope |

## Shared export rules

- Most bundled exporters accept `--size`, `--dynamic`, `--batch`, `--simplify`, and `--opset`.
- Most bundled exporters emit `labels.txt` when the upstream checkpoint contains class names.
- After export, route the ONNX file back to the deployment sub-skill and match the generated config template.

## Family selection rule

- Prefer the bundled Ultralytics helper when the checkpoint is one of the verified Ultralytics-style families.
- Prefer the reference-only table when the user asks about a family from another upstream repo.
