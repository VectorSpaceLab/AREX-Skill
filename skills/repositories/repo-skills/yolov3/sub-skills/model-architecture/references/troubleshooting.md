# Architecture Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Unexpected output final dimension | `nc` changed or wrong YAML loaded | Verify YAML `nc`; expected final dimension is `nc + 5`. |
| Prediction count differs | Image size or stride/head layers differ | Probe with the same `--imgsz` and inspect detection layer strides. |
| Checkpoint load has missing/unexpected keys | YAML architecture does not match checkpoint | Use matching YAML/checkpoint or accept partial transfer and retrain. |
| Anchor warnings during training | Dataset boxes do not match anchors | Let AutoAnchor run or update anchors deliberately. |
| Import cycle or missing layer name | New YAML references unsupported module | Add/modify the owning module in `models/common.py` or `models/yolo.py`, then probe. |
| Segmentation/classification request appears | This repository is detection-only | Route to another repo/skill unless the task is to intentionally add a new task head. |
