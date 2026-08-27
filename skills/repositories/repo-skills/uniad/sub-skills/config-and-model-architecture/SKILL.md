---
name: config-and-model-architecture
description: "Explain UniAD config variants, plugin registration, public model
  components, and task-head relationships."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Config and Model Architecture

Use this sub-skill when the question is about choosing, editing, or comparing UniAD configs, understanding which model component owns a task, or diagnosing a BEV encoder swap or registry problem.

## Read first
- `references/config-reference.md` for the three public config families, queue lengths, checkpoints, and plugin fields.
- `references/model-architecture.md` for the detector/head ownership map and task flow.
- `references/api-reference.md` for verified constructor signatures and key call contracts.
- `references/troubleshooting.md` for import, memory, anchor, BEV swap, and planning-metric failures.
- `scripts/summarize_uniad_config.py` for a safe one-file config summary.

## Covers
- BEVFormer base, stage 1 track/map, and stage 2 end-to-end configs.
- `plugin = True` / `plugin_dir` and the `projects.mmdet3d_plugin` import root.
- Verified public classes: `UniAD`, `UniADTrack`, `BEVFormerHead`, `BEVFormerTrackHead`, `PansegformerHead`, `MotionHead`, `OccHead`, and `PlanningHeadSingleMode`.
- Queue length, `load_from`, freeze flags, and task-loss ownership.
- Planning metric ambiguity and the `planning_evaluation_strategy` switch.
- BEV encoder replacement rules: preserve the `bev_embed` / `bev_pos` contract.

## Do not cover
- Training or evaluation command construction → `training-evaluation`
- Dataset downloads or info generation → `data-preparation`
- Visual result interpretation or plotting → `visualization-and-results`

## Use this when
- You need to pick the right UniAD config for an experiment.
- You need to explain why a stage is missing a head or a loss.
- You are diagnosing plugin, registry, or import failures tied to model construction.
- You need to identify which module owns a reported loss or output.
- You want a safe summary of a config file before editing it.

## Output expectation
Lead with the minimal config or architecture answer, then cite the specific config field or class contract that justifies it.
