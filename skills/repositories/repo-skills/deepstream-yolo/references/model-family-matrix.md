# Model family matrix

This matrix helps the runtime skill choose the correct config template, exporter, and tuning knobs without needing any external repository files.

## Core families

| Family / template | Export path | Model file kind | Key DeepStream notes |
| --- | --- | --- | --- |
| Darknet YOLO (`config_infer_primary.txt`, `config_infer_primary_yoloV2.txt`) | `custom-network-config` + `model-file` | `.cfg` + `.weights` | `force-implicit-batch-dim=0`, `engine-create-func-name=NvDsInferYoloCudaEngineGet`, `cluster-mode=2`, `model-color-format=0` |
| Ultralytics ONNX (`yoloV5u`, `yoloV8`, `yoloV10`, `yolo11`, `yoloV12`, `yoloV13`, `yolo26`, `yolomaster`) | bundled Ultralytics-family exporter scripts | `.pt` -> `.onnx` | usually `maintain-aspect-ratio=1`, `symmetric-padding=1`, `model-color-format=0`, `net-scale-factor=0.0039215697906911373` |
| Legacy YOLOX / YOLOR / YOLOv6 / YOLOv7 / YOLOv7-u6 / YOLOv9 | legacy upstream exporter scripts | upstream model checkpoint -> `.onnx` | family-specific padding and color-format rules; verify against the sub-skill reference before changing `config_infer_primary*.txt` |
| Paddle / MMDetection / MMYOLO / Super-Gradients / RF-DETR / D-FINE / DAMO-YOLO / Gold-YOLO | reference-only in this skill | various upstream checkpoints -> `.onnx` | require the documented upstream repo stack, so they are routed through the matrix rather than bundled as runnable helpers in this environment |

## Template-level special knobs

| Config template | Special knobs that matter most |
| --- | --- |
| `config_infer_primary.txt` | Darknet path; `custom-network-config`, `model-file`, `force-implicit-batch-dim=0`, `maintain-aspect-ratio=0`, `symmetric-padding=1`, `cluster-mode=2` |
| `config_infer_primary_codetr.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=0`, `cluster-mode=2` |
| `config_infer_primary_damoyolo.txt` | `maintain-aspect-ratio=0`, `net-scale-factor=1`, `cluster-mode=2` |
| `config_infer_primary_dfine.txt` | `maintain-aspect-ratio=0`, `cluster-mode=4` |
| `config_infer_primary_goldyolo.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_ppyoloe.txt` | `maintain-aspect-ratio=0`, `net-scale-factor=0.0173520735727919486` |
| `config_infer_primary_ppyoloe_plus.txt` | `maintain-aspect-ratio=0`, `net-scale-factor=0.0039215697906911373` |
| `config_infer_primary_rfdetr.txt` | `maintain-aspect-ratio=0`, `cluster-mode=4` |
| `config_infer_primary_rtdetr.txt` | `maintain-aspect-ratio=0`, `cluster-mode=4` |
| `config_infer_primary_rtmdet.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1`, `model-color-format=1`, `net-scale-factor=0.0173520735727919486` |
| `config_infer_primary_yolo11.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yolo26.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1`, `cluster-mode=4` |
| `config_infer_primary_yoloV10.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1`, `cluster-mode=4` |
| `config_infer_primary_yoloV12.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yoloV13.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yoloV5.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yoloV5u.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yoloV6.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yoloV7.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yoloV8.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yoloV9.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yolomaster.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yolonas.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=0` |
| `config_infer_primary_yolonas_custom.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=0`, `net-scale-factor=1` |
| `config_infer_primary_yolor.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=1` |
| `config_infer_primary_yolox.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=0`, `model-color-format=1`, `net-scale-factor=1` |
| `config_infer_primary_yolox_legacy.txt` | `maintain-aspect-ratio=1`, `symmetric-padding=0`, `model-color-format=0`, `net-scale-factor=0.0173520735727919486` |

## Guidance

- Use the template name as the first routing clue, then confirm the family-specific knobs above.
- If a family is not in the bundled exporter group, keep it in the reference-only matrix unless the upstream framework stack is explicitly prepared.
- The deployment sub-skill owns the config-editing guidance; the model-conversion sub-skill owns exporter selection and labels generation.
