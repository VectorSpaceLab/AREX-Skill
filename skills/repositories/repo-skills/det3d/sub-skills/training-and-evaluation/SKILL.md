---
name: training-and-evaluation
description: "Route Det3D training, inference, evaluation, checkpoint, resume,
  and distributed-launch tasks."
metadata:
  disco-role: operating
disable-model-invocation: true
license: Apache 2.0
---

# Training and Evaluation

Use this route for `train.py`, `test.py`, distributed testing, checkpoint
resume/finetuning, result export, and metric evaluation. Read the CLI and
workflow references before constructing a command. Use
`scripts/plan_launch.py` to validate and print a launch plan without starting a
job.

## Safe sequence

1. Confirm the config, prepared dataset info files, checkpoint (for test),
   work directory, GPU count, and launcher.
2. Preflight imports and CUDA/compiled-op readiness via `runtime-ops`.
3. Plan a single-GPU dry run or distributed environment explicitly; do not infer
   distributed mode only from a shell's `CUDA_VISIBLE_DEVICES`.
4. Start with a bounded smoke/evaluation case if a real fixture exists.
5. Preserve config, Det3D version, class metadata, logs, and checkpoint paths in
   the work directory for reproducibility.

Training and normal evaluation are GPU/data/checkpoint workflows. CPU import
or config parsing is not a substitute. Full native runs are intentionally not
performed by this skill without user-provided data and an approved budget.

Use `datasets-and-preprocessing` for data generation, `configuration-and-models`
for architecture edits, and `visualization-and-analysis` for result artifacts.
