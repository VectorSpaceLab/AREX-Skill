---
name: validation-evaluation
description: "Run and interpret YOLOv3 validation, mAP metrics, val.py tasks,
  COCO JSON output, and evaluation artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: AGPL 3.0
---

# Validation and Evaluation Sub-skill

Read this for `val.py`, model mAP, precision/recall, COCO JSON output, text predictions, speed/study tasks, validation dataloaders, or post-training evaluation.

## Use

- Read `references/workflows.md` for validation commands, output interpretation, and task modes.
- Use `scripts/yolov3_eval_command_builder.py` to build validation commands and JSON plans safely.
- Read `references/troubleshooting.md` for metric, class-count, and dataset failures.

## Important facts

- Main entry point: `python val.py`.
- Key flags: `--data`, `--weights`, `--batch-size`, `--imgsz`, `--task`, `--device`, `--save-txt`, `--save-conf`, `--save-json`, `--half`, and `--dnn`.
- `--task` accepts `train`, `val`, `test`, `speed`, or `study`.
- `--save-json` is automatically enabled for `coco.yaml`; pycocotools is optional but needed for official COCO JSON metrics.
