# Validation Troubleshooting

| Symptom | Likely cause | Action |
| --- | --- | --- |
| `best.pt` missing | Training smoke did not run or saved elsewhere | Use the training sub-skill to pin `--project`, `--name`, and `--exist-ok`. |
| `--save-json` fails | pycocotools or COCO annotations unavailable | Install optional metrics dependencies or disable `--save-json`. |
| Class count mismatch | Dataset YAML `nc/names` differs from checkpoint | Validate YAML and checkpoint class names; retrain or choose matching data. |
| Empty metrics | Missing labels, wrong split path, or no detections | Check dataset paths, labels, confidence thresholds, and image/label pairing. |
| CPU validation is slow | Large image size/model/data on CPU | Use tiny smoke settings or verify CUDA before accelerator runs. |
| `--half` fails | FP16 requested on CPU or unsupported backend | Use FP32 on CPU; enable FP16 only on compatible CUDA paths. |
| COCO JSON is unexpectedly enabled | `val.py` auto-enables JSON when data path ends with `coco.yaml` | Rename/use different YAML or pass a non-COCO data file when JSON is not wanted. |
