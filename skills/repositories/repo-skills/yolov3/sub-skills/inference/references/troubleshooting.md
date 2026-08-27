# Inference Troubleshooting

| Symptom | Cause | Fix |
| --- | --- | --- |
| `yolov3-tiny.pt` not found | Official weights are not local and may need download | Ask before network use or pass a local checkpoint path. |
| `torch.hub.load` fails with cache/source errors | Hub cache stale or source mode mismatch | Use `force_reload=True` for remote Hub or `source='local'` from a checkout. |
| Helper import fails | `--repo-root` does not point to a YOLOv3 checkout | Pass a valid checkout root containing `models/` and `utils/`. |
| No detections | Thresholds/classes/source mismatch | Lower `--conf-thres`, remove `--classes`, verify image path and class names. |
| Empty or missing label files | `--save-txt` not enabled or no detections survived NMS | Enable `--save-txt`; tune confidence/NMS and inspect printed per-image logs. |
| Crop saving fails or is empty | No detections or invalid output path | Enable `--save-crop` only after a detection run shows boxes. |
| FP16 fails on CPU | `--half` is not portable on CPU | Use FP32 on CPU and reserve `--half` for CUDA. |
| ONNX DNN path fails | Runtime/backend mismatch | Verify ONNX export, OpenCV DNN support, and `--dnn` usage; otherwise use PyTorch `.pt`. |
