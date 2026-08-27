---
name: mmengine
description: "Use MMEngine to configure, train, evaluate, inspect, visualize,
  and troubleshoot PyTorch/OpenMMLab workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MMEngine Repo Skill

Use this skill when a task mentions MMEngine, OpenMMLab engine utilities, `Config`, `Registry`, `Runner`, `FlexibleRunner`, hooks, optim wrappers, schedulers, `BaseDataset`, `BaseModel`, `BaseMetric`, `Visualizer`, or MMEngine distributed/runtime helpers.

## Start Here

- `references/package-overview.md`: Understand MMEngine's package layout, dependency model, public API families, and how the sub-skills fit together.
- `references/troubleshooting.md`: Diagnose cross-cutting install/import, optional dependency, config, runner, data, model, visualization, and distributed issues.
- `scripts/mmengine_import_check.py`: Run a safe import/API smoke check for the installed `mmengine` package before deeper debugging.
- `references/repo-provenance.md`: Check the source version and evidence baseline used to create this skill.
- `references/repo-routing-metadata.json`: Structured routing metadata consumed by DisCo's managed repo-skills router.

## Route by Task

| User task signal | Read this sub-skill | Why |
| --- | --- | --- |
| Config files, `_base_`, CLI overrides, lazy imports, `custom_imports`, `Registry`, `build_from_cfg`, `_scope_`, default scope | `sub-skills/configuration-and-registry/SKILL.md` | Owns MMEngine config parsing, merge/dump, registry scopes, object-build diagnostics, and a safe config inspection helper. |
| `Runner`, `FlexibleRunner`, training/validation/testing loops, hooks, checkpoint/resume, AMP, optimizers, schedulers, distributed launch, large-model strategies | `sub-skills/runner-and-training/SKILL.md` | Owns training orchestration, Runner config shape, hook/optimizer/scheduler interactions, checkpoint semantics, and dependency-gated distributed/strategy guidance. |
| `BaseDataset`, transforms, samplers, collate functions, `InstanceData`, `PixelData`, `LabelData`, `mmengine.fileio`, `backend_args` | `sub-skills/data-structures-and-io/SKILL.md` | Owns data contracts, dataset initialization, transform pipelines, data elements, and backend-agnostic file IO. |
| `BaseModel`, `BaseModule`, preprocessors, model step modes, `BaseMetric`, `Evaluator`, `DumpResults`, inferencers, TTA, complexity analysis | `sub-skills/models-metrics-and-inference/SKILL.md` | Owns model/evaluator contracts, prediction/result shapes, TTA wrappers, inferencer patterns, and analysis limits. |
| `MMLogger`, `MessageHub`, `Visualizer`, visual backends, `init_dist`, `collect_results`, `master_only`, devices, `collect_env`, timers, testing helpers | `sub-skills/runtime-utilities-and-visualization/SKILL.md` | Owns logging, visualization, optional tracking backends, distributed/device utilities, environment reports, and runtime diagnostics. |

## Common Workflows

1. For a full training project, read in this order: `configuration-and-registry`, `data-structures-and-io`, `models-metrics-and-inference`, `runner-and-training`, then `runtime-utilities-and-visualization` for logging/visual output.
2. For a config-only edit, stay in `configuration-and-registry` unless the edit changes runner loop placement, model/metric contracts, or dataset schemas.
3. For a failed training run, identify the failing layer first: config build, dataset/collate, model/metric contract, runner/hook/optimizer scheduling, or runtime backend.
4. For optional services or large-model/distributed workflows, keep the safe local path working first, then add TensorBoard/WandB/MLflow/DeepSpeed/FSDP/ColossalAI only when dependencies, credentials, launchers, and hardware are available.

## Safe Checks

From this skill directory, these helpers are safe and self-contained:

```bash
python scripts/mmengine_import_check.py --json
python sub-skills/configuration-and-registry/scripts/inspect_config.py --help
python sub-skills/runner-and-training/scripts/runner_config_smoke.py --demo
python sub-skills/data-structures-and-io/scripts/data_contract_smoke.py --help
python sub-skills/models-metrics-and-inference/scripts/model_metric_smoke.py --help
python sub-skills/runtime-utilities-and-visualization/scripts/runtime_env_check.py --help
```

The helpers do not download data, start distributed jobs, require credentials, or run long training. Full examples and native repository tests remain verification evidence, not runtime dependencies for this skill.

## Boundaries

- This skill is for using MMEngine as a package in user projects, not for maintaining MMEngine release infrastructure.
- Do not assume optional services such as WandB, MLflow, ClearML, Aim, DVCLive, Neptune, DeepSpeed, ColossalAI, or FSDP extras are installed unless the user's environment proves it.
- Do not route downstream task-library behavior, such as MMDetection-specific datasets or MMSegmentation models, into this skill except where generic MMEngine contracts apply.
- Prefer small import/config/smoke checks before running training, distributed launchers, or service-backed visualization.
