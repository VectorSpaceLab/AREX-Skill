# Cross-Cutting Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `ModuleNotFoundError: models` or `utils` | Native command is not running from a YOLOv3 checkout root | Run repo scripts from the checkout root, or pass `--repo-root` to bundled helper scripts. |
| Editable install fails | Project metadata is incomplete for editable packaging | Use checkout plus `requirements.txt`; route packaging fixes to repo-maintenance. |
| Official weights are missing | `yolov3*.pt` names are release assets and can auto-download | Ask before network use; use an existing local checkpoint for offline tasks. |
| Dataset files are missing | Dataset YAML `path:` resolves to a missing location or has a `download:` stanza | Validate YAML and decide whether download is approved before training or validation. |
| CUDA requested but unavailable | CPU torch wheel, missing driver, no GPU passthrough, or bad `--device` value | Use `--device cpu` for correctness smokes or prepare a compatible CUDA stack. |
| TensorRT requested on CPU | TensorRT export is GPU-only in this repo | Use TorchScript, ONNX, or OpenVINO for CPU deployment. |
| Results saved in unexpected run directory | `project/name` auto-increments without `--exist-ok` | Pin `--project`, `--name`, and `--exist-ok` for reproducible smoke outputs. |
| No detections or empty labels | Confidence/class filters are too strict or weights/classes mismatch data | Lower `--conf-thres`, remove `--classes`, verify `--data`, and inspect logs. |
| COCO JSON metrics missing | `--save-json` requires COCO-style data and pycocotools | Install optional metrics dependencies or rely on printed mAP metrics. |
| A proposed source change adds broad guards or parallel abstractions | Repo policy prefers owner-level changes | Follow Delete > Replace > Add and solve behavior in the owning code path. |
