---
name: training-and-evaluation
description: "Plan MMAction2 training, testing, distributed launch, evaluation,
  result dumps, and analysis workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMAction2 Training And Evaluation

Use this sub-skill when a task asks how to train, resume, test, evaluate, dump predictions, launch distributed or Slurm jobs, interpret work directories/checkpoints, or debug MMAction2 metrics and training/test CLIs.

## Start Here

1. Read [references/train-test-reference.md](references/train-test-reference.md) for train/test parser flags, command templates, CPU/GPU selection, resume/load-from behavior, AMP, auto-scaled learning rate, work directory outputs, quick tiny-dataset caveats, and distributed/Slurm launch patterns.
2. Read [references/evaluation-reference.md](references/evaluation-reference.md) for evaluator configuration, `AccMetric`, retrieval, AVA, ActivityNet/localization, result dumps, offline metric evaluation, fusion, confusion matrix, and mAP reporting tools.
3. Read [references/troubleshooting.md](references/troubleshooting.md) before advising a retry after a CLI, runtime, metric, checkpoint, GPU, distributed, or work-directory failure.
4. Use [scripts/mmaction2_train_test_command_builder.py](scripts/mmaction2_train_test_command_builder.py) to preview a shell command without launching training or testing.

## Routing Boundaries

- Data annotation schemas, dataset roots, pipeline transforms, config inheritance, and precise dataset-specific `data_prefix` keys belong to [../data-and-configs/SKILL.md](../data-and-configs/SKILL.md).
- Inference-only APIs, demos, label maps, and visualization for single media inputs belong to [../inference-and-demos/SKILL.md](../inference-and-demos/SKILL.md).
- Model family selection, registry/custom component implementation, export, conversion, publishing, and deployment belong to [../models-and-extension/SKILL.md](../models-and-extension/SKILL.md).

## Operating Rules

- Do not launch training, testing, distributed jobs, Slurm jobs, downloads, or checkpoint conversion unless the user explicitly asks for execution and the required compute/data/checkpoints are available.
- Prefer command previews first. Confirm config path, checkpoint path for test/evaluation, work directory, target device, and whether the run may write checkpoints, logs, metric files, visualization images, or result dumps.
- For CPU-only commands, prefix the eventual command with `CUDA_VISIBLE_DEVICES=-1`. MMAction2 otherwise prefers an available GPU.
- Treat quick tiny-dataset recipes as smoke/debug workflows, not as benchmark evidence. They often depend on user-provided data and optional pretrained checkpoints.
- Keep future instructions self-contained: use the references above and bundled command builder instead of sending users to repository docs or examples.
