---
name: runner-and-training
description: "Build, adapt, and troubleshoot MMEngine Runner and FlexibleRunner
  training workflows, hooks, optimizers, schedulers, checkpoints, resume,
  distributed launch, and optional strategies."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Runner and Training

Use this sub-skill when a task mentions `Runner.from_cfg`, `Runner`, `FlexibleRunner`, `train_cfg`, `val_cfg`, `test_cfg`, hooks, checkpoints, resume, AMP, gradient accumulation, parameter schedulers, distributed launch, or large-model strategies.

## Read Order

- [references/runner-workflows.md](references/runner-workflows.md): Assemble `Runner` and `FlexibleRunner` configs, choose train/val/test loops, handle checkpoint/resume semantics, and understand runtime outputs.
- [references/hooks-optim-schedulers.md](references/hooks-optim-schedulers.md): Configure default/custom hooks, checkpoint best metrics, `OptimWrapper`/`AmpOptimWrapper`, gradient accumulation, clipping, and parameter schedulers.
- [references/large-model-and-distributed.md](references/large-model-and-distributed.md): Choose launchers, distributed backends, `FlexibleRunner` strategies, AMP/compile/checkpointing, and dependency-gated DeepSpeed/FSDP/ColossalAI paths.
- [references/troubleshooting.md](references/troubleshooting.md): Diagnose common Runner, hook, optimizer, scheduler, checkpoint, resume, launcher, and strategy failures by symptom.
- [scripts/runner_config_smoke.py](scripts/runner_config_smoke.py): Safely validate Runner-like JSON config shape without importing project code, downloading data, launching distributed jobs, or training.

## Scope

This sub-skill owns MMEngine training orchestration: `mmengine.runner`, `mmengine.hooks`, `mmengine.optim`, `mmengine._strategy`, training/validation/testing loops, checkpointing, resume/load behavior, randomness, log processors, distributed launch recipes, and optional strategy configs.

Route adjacent issues to sibling skills:

- Use `../configuration-and-registry/SKILL.md` for Python/YAML config syntax, `_base_`, custom imports, registry scopes, and `build_from_cfg` failures.
- Use `../models-metrics-and-inference/SKILL.md` for `BaseModel.forward`, `train_step`, `val_step`, evaluator, metric, TTA, and prediction contracts.
- Use `../data-structures-and-io/SKILL.md` for dataset, sampler, collate, data element, annotation, and file IO details.
- Use `../runtime-utilities-and-visualization/SKILL.md` for visualizer backends, logger internals, message hubs, device utilities, and general distributed helpers outside Runner orchestration.

## Fast Workflow

1. Identify the entry point: `Runner.from_cfg(cfg)` for config-driven projects, direct `Runner(...)` for small experiments, or `FlexibleRunner(...)` when `strategy`, `compile`, or large-model training is central.
2. Check loop completeness: training needs `model`, `work_dir`, `train_dataloader`, `train_cfg`, and `optim_wrapper`; validation/testing additionally need matching dataloaders, loop cfgs, and evaluators.
3. Align time units: if `train_cfg.by_epoch=False`, also align `default_hooks.checkpoint.by_epoch`, `default_hooks.logger.log_metric_by_epoch`, `log_processor.by_epoch`, and scheduler `by_epoch` or `convert_to_iter_based` settings.
4. Decide checkpoint semantics: `load_from` without `resume=True` loads weights only; `resume=True` restores optimizer and scheduler state from the latest or specified checkpoint.
5. Validate risky edits from this sub-skill directory with `python scripts/runner_config_smoke.py --config-json config.json` after converting the relevant config shape to JSON.

## Output Expectations

`Runner.train()` returns the trained model, while `Runner.val()` and `Runner.test()` return metric dictionaries. Runtime outputs normally include checkpoints, logs, and visualizer files under the configured `work_dir` or log directory; this sub-skill treats those as user project outputs, not managed skill files.
