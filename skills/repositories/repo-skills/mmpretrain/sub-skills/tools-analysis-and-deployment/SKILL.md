---
name: tools-analysis-and-deployment
description: "Route post-training analysis, visualization, checkpoint
  publishing, conversion, and TorchServe workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Tools Analysis and Deployment

Use this sub-skill after you already have a log, result file, checkpoint, or image and need post-run analysis or packaging.

## Use here for
- JSON log summaries and curve plots
- offline metrics and confusion matrices from saved predictions
- dataset browsing, scheduler plots, CAM, and t-SNE
- FLOPs / parameter estimates from a config or model name
- checkpoint publishing, conversion, reparameterization, and TorchServe packaging

## Route elsewhere for
- Training, testing, resume, distributed launch, or command planning -> `../training-and-evaluation/SKILL.md`
- Dataset schema, annotation formats, or custom registries -> `../datasets-and-customization/SKILL.md`
- Simple inference or model listing -> `../model-zoo-inference/SKILL.md`

## Bundled helpers
- `scripts/analyze_json_log.py` — summarize JSON logs and optionally plot curves
- `scripts/estimate_flops.py` — estimate FLOPs/params from a config or model reference
- `scripts/publish_checkpoint.py` — publish a checkpoint without mutating the source file

## Dependency gates
- Core: `torch`, `mmcv`, `mmengine`, `matplotlib`
- Optional: `seaborn` for plot styling, `grad-cam` for CAM, `scikit-learn` for t-SNE, `torchserve` and `torch-model-archiver` for packaging

## Safe defaults
- Prefer file output over interactive display in headless environments.
- Treat external checkpoint formats as family-specific; choose the matching converter first.
- Preserve the source checkpoint and write published artifacts to a new path.
