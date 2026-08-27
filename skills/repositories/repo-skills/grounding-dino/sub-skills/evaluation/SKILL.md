---
name: evaluation
description: "Evaluate GroundingDINO on COCO-style data and diagnose zero-shot AP results."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# GroundingDINO Evaluation

Use this sub-skill when a user wants COCO zero-shot evaluation, bbox AP summaries, or evaluator API guidance for GroundingDINO. It covers dataset layout, config/checkpoint/device choices, category-caption postprocessing, and common AP failure modes.

## Routes

- For a full COCO or COCO-style AP run, follow [COCO evaluation](references/coco-evaluation.md) and use the bundled helper at [scripts/grounding_dino_coco_eval.py](scripts/grounding_dino_coco_eval.py).
- For evaluator internals, prediction formats, and reusable APIs, read [API reference](references/api-reference.md).
- For failures such as missing COCO data, `pycocotools` import errors, CUDA/device mismatch, missing custom ops, or unexpectedly low AP, use [troubleshooting](references/troubleshooting.md).
- For single-image inference, prompts, token spans, or annotated outputs, route to [inference](../inference/).
- For pseudo-labeling folders or COCO export from detections, route to [dataset annotation](../dataset-annotation/).

## Required Inputs

- A GroundingDINO config file matching the checkpoint, such as the Swin-T OGC or Swin-B config distributed with the package/release.
- A matching checkpoint file already downloaded by the user; this sub-skill does not download weights.
- A COCO annotation JSON such as `instances_val2017.json` and an image directory containing the referenced `file_name` entries.
- A device choice: `cuda`, `cuda:0`, or `cpu`; CPU is useful for smoke tests but not benchmark-speed evaluation.

## Fast Start

```bash
python sub-skills/evaluation/scripts/grounding_dino_coco_eval.py \
  -c configs/GroundingDINO_SwinT_OGC.py \
  -p weights/groundingdino_swint_ogc.pth \
  --anno_path datasets/coco/annotations/instances_val2017.json \
  --image_dir datasets/coco/val2017 \
  --device cuda \
  --num_select 300 \
  --num_workers 4
```

Expected output includes the constructed category prompt, progress messages, the `IoU metric: bbox` COCO summary table, and `Final results: [...]` with the `bbox` stats list. With the matching Swin-T OGC config, Swin-T OGC checkpoint, and official COCO val2017 data, the documented benchmark signal is about `48.5` bbox AP; mini-subsets and CPU smoke tests are validation checks, not benchmark evidence.
