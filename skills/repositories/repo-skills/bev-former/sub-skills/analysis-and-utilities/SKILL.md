---
name: analysis-and-utilities
description: "Analyze BEVFormer logs and utility outputs while separating safe
  summaries from data-, checkpoint-, or GPU-bound analysis tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---
# analysis-and-utilities

Analyze BEVFormer log and utility questions without running training.

## Use this sub-skill for
- JSON or JSONL training and evaluation log summaries
- `analyze_logs`, `benchmark`, `visual`, `get_params`, `fuse_conv_bn`, and `visualize_results`
- model zoo log comparison and checkpoint utility questions

## Route away when
- install, import, or config questions need handling -> `installation-and-configs`
- train, eval, or FP16 launch commands are needed -> `training-and-evaluation`
- nuScenes data layout or CAN bus preparation is the real task -> `dataset-preparation`

## Bundled helper
- [scripts/summarize_bevformer_log.py](scripts/summarize_bevformer_log.py)

## Read first
- [references/analysis-utilities.md](references/analysis-utilities.md)
- [references/troubleshooting.md](references/troubleshooting.md)

## Operating rules
- Keep log summaries safe: run the bundled helper on small JSON or JSONL fixtures only.
- Treat benchmark, visualization, and checkpoint-fusion requests as gated by dataset, checkpoint, or mutation risk.
- Do not run training or evaluation from this sub-skill.
