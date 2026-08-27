---
name: training-evaluation
description: "Launch, troubleshoot, and inspect MMSegmentation training,
  validation, testing, metrics, logs, and distributed jobs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and Evaluation

Use this sub-skill when the task is to run or debug MMSegmentation training, validation, testing, metrics, log analysis, checkpoint resume/fine-tuning, distributed launch, Slurm jobs, AMP, TTA, offline result formatting, or test-time visualization.

## Route Here When

- The user needs a safe MMSegmentation training/testing command, `Runner.from_cfg` guidance, distributed launch, or Slurm launch.
- A run failed around checkpoints, `work_dirs`, `--resume`, `load_from`, `--amp`, `--cfg-options`, launcher settings, ports, ranks, or unavailable CUDA.
- The user needs IoU, Cityscapes, or depth metric behavior explained, including `output_dir`, `format_only`, and saved prediction files.
- The user wants to summarize MMSegmentation JSON logs, compare loss/metric curves, or inspect training progress without starting a long run.
- Testing needs `--out`, TTA, visualized predictions, or hidden-test/offline submission formatting.

## Do Not Handle Here

- Dataset registration, data roots, annotation format, pipelines, or config authoring details; route those to `data-configuration`.
- Implementing models, decode heads, losses, optimizers, hooks, or registries beyond runtime troubleshooting; route those to `model-customization`.
- Inference-only APIs such as `init_model`, `inference_model`, or inferencers; route those to `inference`.

## Start With

1. Identify whether the user wants a dry-run command, a real execution, or a diagnosis of an existing log/error.
2. For training/testing commands, prefer the bundled safe wrappers first:
   - `scripts/mmseg_train_wrapper.py --help`
   - `scripts/mmseg_test_wrapper.py --help`
3. For log summaries, use `scripts/analyze_mmseg_log.py --help`; it has no MMSegmentation import requirement and works on small JSON-line fixtures.
4. If direct commands are clearer than wrappers, use the exact patterns in `references/train-test-workflows.md` and `references/distributed-training.md`.
5. For metric/output questions, check `references/metrics-and-logs.md` before changing evaluator config.
6. For failures, match the symptom in `references/troubleshooting.md` before changing code or re-running expensive jobs.

## Key References

- `references/train-test-workflows.md` covers single-process training/testing, `Runner.from_cfg`, AMP, resume/fine-tune, TTA, visualization, output formatting, and `work_dirs`.
- `references/metrics-and-logs.md` covers `IoUMetric`, `DepthMetric`, Cityscapes-style evaluation, JSON log summaries, confusion-matrix inputs, and benchmark cautions.
- `references/distributed-training.md` covers `torch.distributed.launch`, multi-node environment variables, Slurm variables, port conflicts, and NPU launch shape.
- `references/troubleshooting.md` maps common training/evaluation failures to checks and safe fixes.

## Safety Defaults

- The bundled training/testing wrappers are dry-run/preflight tools unless `--execute` is passed.
- Do not start full training, testing, distributed, Slurm, or benchmark jobs without explicit user approval and a bounded config/checkpoint scope.
- Prefer short help checks, config parsing, tiny log fixtures, or metric unit tests before native long-running jobs.
- Keep offline formatting and hidden-test workflows explicit: set evaluator `format_only=True` only when ground truth is unavailable or evaluation should be skipped.
