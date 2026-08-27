---
name: training-evaluation
description: "Train, evaluate, checkpoint, and troubleshoot Detectron2 models
  with safe commands and APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Detectron2 Training & Evaluation

Use this sub-skill when the task is to run or prepare Detectron2 training/evaluation, customize trainers/hooks/evaluators/checkpointing, or diagnose training/eval failures. It assumes datasets and configs have already been selected or registered by the dataset/configuration sub-skills.

## Fast Routing

- Build safe training/eval commands with `scripts/train_command_builder.py`; it prints commands only and never starts training.
- Plan evaluator/checkpoint setup with `scripts/evaluation_plan.py`; it prints checks and next steps only and never runs evaluation.
- Read `references/training-workflows.md` for standard Detectron2 train/eval driver semantics, `DefaultTrainer`, `SimpleTrainer`, hooks, launch, solver scaling, and resume/eval-only behavior.
- Read `references/evaluation-checkpointing.md` for evaluator selection, `inference_on_dataset`, `verify_results`, `DetectionCheckpointer`, and checkpoint loading/resume behavior.
- Read `references/troubleshooting.md` before starting long jobs, changing GPU count, using a custom dataset, switching Yacs/LazyConfig syntax, or debugging failed evaluation.

## Safe Defaults

- Prefer a dry-run command/planning step before running a long job; stop for user approval when training would be long, multi-GPU, dataset-heavy, or hardware-dependent.
- Use a project-local driver with the standard Detectron2 parser shape: `python PROJECT_TRAIN_DRIVER.py --config-file CONFIG --num-gpus N [--resume|--eval-only] KEY VALUE ...`.
- Use LazyConfig syntax only for Python config files: `python PROJECT_LAZY_TRAIN_DRIVER.py --config-file CONFIG.py train.output_dir=... dataloader.train.total_batch_size=...`.
- Do not use the repository demo CLI as a runtime dependency; in this checkout its demo imports a missing `vision.fair.detectron2.demo.predictor` module.

## Common APIs

- Yacs training: subclass `DefaultTrainer`, override `build_evaluator`, optionally override `build_train_loader`, `build_optimizer`, `build_lr_scheduler`, or register hooks.
- Minimal loop: use `SimpleTrainer(model, data_loader, optimizer)` when `DefaultTrainer` assumptions are too restrictive.
- Distributed entry: call `launch(main_func, num_gpus_per_machine, num_machines=1, machine_rank=0, dist_url=None, args=())`.
- Evaluation: use `COCOEvaluator`, `SemSegEvaluator`, `DatasetEvaluator`, `DatasetEvaluators`, and `inference_on_dataset(model, data_loader, evaluator)`.
- Checkpointing: use `DetectionCheckpointer(model, save_dir, trainer=trainer)` and distinguish `load`, `resume_or_load`, `--resume`, and `--eval-only`.
