---
name: star-vla
description: "Operate StarVLA for vision-language-action model development,
  training plans, LeRobot data integration, benchmark evaluation, and policy
  deployment."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# StarVLA repo skill

Use this repo skill when the task involves StarVLA, a Lego-like vision-language-action (VLA) research codebase for robot policies. It routes model-family selection, dataset/robot integration, training launch planning, simulation benchmark evaluation, and policy-server deployment without requiring the original repository docs to be reopened.

## Before acting

1. Confirm the user has a StarVLA checkout or installed package for code execution. This skill is self-contained as guidance, but StarVLA workflows still require the package, model checkpoints, datasets, and benchmark or robot environments.
2. Read [references/repo-provenance.md](references/repo-provenance.md) if the current checkout may differ from the skill snapshot.
3. Read [references/installation-and-environment.md](references/installation-and-environment.md) before installing dependencies or choosing CPU/GPU/ROCm/NPU paths.
4. Run [scripts/check_starvla_install.py](scripts/check_starvla_install.py) for a safe import/backend diagnostic. It does not download weights, start servers, or run training.
5. Use [scripts/inspect_starvla_config.py](scripts/inspect_starvla_config.py) to summarize a training/eval YAML before deciding which sub-skill owns the next step.

## Route by task

| User request | Read next |
| --- | --- |
| Choose `QwenOFT`, `QwenFAST`, `QwenPI_v3`, `QwenGR00T`, `ACT`, `DiffusionPolicy`, `CosmoPredict2*`, or `Wan*`; debug `Framework ... is not implemented`; inspect `baseframework` APIs | [model-frameworks](sub-skills/model-frameworks/SKILL.md) |
| Build or modify a training command, explain YAML/CLI overrides, plan Accelerate/DeepSpeed launches, freeze modules, set LR groups, resume/checkpoint layout | [training-config](sub-skills/training-config/SKILL.md) |
| Add a LeRobot dataset, write `modality.json`, add a `DataConfig`, register `data_mix`, fix `embodiment_tag` or statistics/cache issues | [data-integration](sub-skills/data-integration/SKILL.md) |
| Plan LIBERO, SimplerEnv, RoboCasa, RoboTwin, DOMINO, BEHAVIOR, VLA-Arena, Calvin, RoboDojo, or similar simulation benchmark evaluation | [benchmark-evaluation](sub-skills/benchmark-evaluation/SKILL.md) |
| Serve a checkpoint, debug websocket/ZMQ clients, `unnorm_key`, server metadata, server-side unnormalization, real-robot bridge contracts | [policy-deployment](sub-skills/policy-deployment/SKILL.md) |
| Cross-cutting install/import/backend/data/config errors | [references/troubleshooting.md](references/troubleshooting.md), then the nearest sub-skill troubleshooting file |

## Core operating facts

- StarVLA selects models with `framework.name`; the framework registry is populated by importing framework modules and maps string keys to classes.
- All main policy frameworks follow the `baseframework` contract: `forward(examples)` for training, `predict_action(examples)` for inference, and `compute_loss(tag, batch)` for trainer routing.
- StarVLA training scripts use YAML plus OmegaConf dotlist overrides. CLI override values have higher precedence than checkpoint or YAML defaults, and malformed overrides should be rejected early.
- VLA datasets are LeRobot-format datasets with `meta/modality.json`, a robot `DataConfig`, and `DATASET_NAMED_MIXTURES` entries. Registry files are auto-discovered from benchmark or robot `train_files/data_registry` locations in a StarVLA checkout.
- Current policy serving performs server-side action unnormalization and returns `actions`, not the older client-side `normalized_actions` contract still present in some example prose.
- Full training, checkpoint inference, simulator evaluation, and real-robot deployment usually require GPU/accelerator resources, pretrained weights, datasets, simulator packages, robot SDKs, or credentials. Treat CPU import checks as preparation only, not as proof of those workflows.

## Shared references

- [references/package-overview.md](references/package-overview.md) summarizes repository layout, model/data/training/deployment responsibilities, and public workflow boundaries.
- [references/installation-and-environment.md](references/installation-and-environment.md) gives install variants, dependency/backends, safe smoke checks, and what not to validate on CPU.
- [references/repo-routing-metadata.json](references/repo-routing-metadata.json) provides structured router metadata for managed repo-skill import.
- [references/troubleshooting.md](references/troubleshooting.md) covers cross-cutting symptoms before narrowing to a sub-skill.

## Safety and validation

- Do not run network download scripts, benchmark-scale evaluation, physical robot control, or destructive data conversion without explicit user approval and the right environment.
- Prefer dry-run planners and validators first: root install/config scripts, `data-integration` modality validator, `training-config` command planner, `benchmark-evaluation` checklist planner, and `policy-deployment` contract checker.
- For final verification or repo maintenance tasks, use safe native tests that mock heavy dependencies before any GPU/simulator/robot run.
