---
name: vision-detection-metrics
description: "Use TorchMetrics image quality, segmentation, object detection,
  and panoptic metrics with correct tensor shapes, dependency gates, and smoke
  checks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Vision Detection Metrics

Use this sub-skill when the task is about TorchMetrics metrics for image quality, segmentation, object detection, instance segmentation, or panoptic segmentation, and the main risk is getting the tensor layout or backend dependency wrong.

Start here:

- Read [references/vision-detection-api.md](references/vision-detection-api.md) for metric families, constructor arguments, input contracts, return shapes, and optional dependency gates.
- Read [references/vision-detection-workflows.md](references/vision-detection-workflows.md) for copyable call patterns across image quality, multispectral fusion, segmentation, detection, and panoptic metrics.
- Read [references/troubleshooting.md](references/troubleshooting.md) when a metric fails on shape, dtype, class-count, backend, or missing-dependency checks.
- Run [scripts/vision_detection_metric_smoke.py](scripts/vision_detection_metric_smoke.py) for a tiny no-download sanity check against the installed package; it covers PSNR, SSIM, MS-SSIM, DiceScore, MeanIoU, HausdorffDistance, IoU, and mean average precision, with optional panoptic and CUDA paths.

Route away from this sub-skill when the task is better served by another skill:

1. Use `../model-based-metrics/SKILL.md` for CLIPScore, CLIP-IQA, FID, KID, Inception Score, LPIPS, DISTS, ARNIQA, or Perceptual Path Length, where pretrained encoders or model downloads are central.
2. Use `../collections-wrappers-plotting/SKILL.md` when the work is mainly metric collections, wrappers, plotting, or display helpers.
3. Use `../core-api/SKILL.md` when the question is about the shared Metric lifecycle such as `update`, `compute`, `reset`, synchronization, or accumulation semantics.

This sub-skill is intentionally narrow: it helps callers build valid calls and diagnose shape/backend failures for vision and detection metrics without turning into a generic TorchMetrics overview.
