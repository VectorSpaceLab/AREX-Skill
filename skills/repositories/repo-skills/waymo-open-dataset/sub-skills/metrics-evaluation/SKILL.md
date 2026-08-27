---
name: metrics-evaluation
description: "Guides Waymo Open Dataset detection, tracking, motion, keypoint,
  and segmentation metric APIs, configs, TensorFlow ops, and submission
  artifacts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Metrics Evaluation

Use this sub-skill when a task asks for WOD detection, tracking, motion, keypoint, segmentation, AP/APH/APL, minADE/minFDE/MissRate/mAP, metric config breakdown names, `py_metrics_ops`, metric tensor shapes, or accuracy submission artifacts.

Read:

- [references/api-reference.md](references/api-reference.md) for verified metric wrapper signatures and tensor-shape contracts.
- [references/workflows.md](references/workflows.md) for detection/tracking/motion/keypoint metric flows, config breakdowns, fake fixtures, and when to use C++/Bazel tools.
- [references/data-formats.md](references/data-formats.md) for Objects/submission proto expectations.
- [references/troubleshooting.md](references/troubleshooting.md) for compiled op, TensorFlow v1 metric variables, shape assertions, breakdown, and no-label-zone failures.

Run [`scripts/inspect_metric_config.py`](scripts/inspect_metric_config.py) to verify installed metric imports and a tiny config breakdown.

Route raw Frame conversion to `dataset-utils`, latency timing to `latency-submissions`, camera segmentation optional dependency issues to `camera-and-segmentation`, and sim-agent challenge metrics to `motion-sim-agents`.
