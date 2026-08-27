---
name: metrics-and-evaluation
description: "Routes pytorch-grad-cam explanation metrics, ROAD, ARCC,
  RefineCAM, and Deep Feature Factorization workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Metrics and Evaluation

Use this sub-skill when the user wants to score, compare, or refine CAMs rather
than just generate one heatmap. It covers confidence-change metrics, ROAD,
ARCC, RefineCAM, and Deep Feature Factorization concept discovery.

## Read first

- [`references/metrics-and-factorization.md`](references/metrics-and-factorization.md)
  for confidence-change, ROAD, and DFF workflows.
- [`references/refinecam-and-arcc.md`](references/refinecam-and-arcc.md) for
  multi-layer refinement and ARCC usage.
- [`references/troubleshooting.md`](references/troubleshooting.md) for shape,
  runtime, dependency, and performance issues.
- Run [`scripts/tiny_metric_smoke.py`](scripts/tiny_metric_smoke.py) to verify
  metric wiring with a tiny synthetic model.

## Typical tasks

- "How good is this CAM?" -> use ROAD or confidence-change metrics.
- "Refine the CAM across layers" -> use `RefineCAM`.
- "Show concept components from activations" -> use Deep Feature Factorization.
- "Compute ARCC" -> use `ARCC(base_method=cam)` or a matching metric helper.

Keep the target callable, input tensor, and CAM output shapes aligned. These
metrics often call the model again, so use a small batch and a deterministic
model when debugging.
