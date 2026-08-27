---
name: training-and-evaluation
description: "Plan and safely launch VoxFormer stage-1 QPN and stage-2
  train/test workflows, including distributed execution, checkpoints,
  validation, outputs, and SSC evaluation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Training and Evaluation

Use this sub-skill for running or planning the repository's **stage-1 query
proposal network (QPN)** and **stage-2 VoxFormer** training and evaluation.
Start with [workflow commands](references/workflow-commands.md), then run the
non-launching [preflight helper](scripts/preflight_train_test.py) before any
expensive command. Use [evaluation and metrics](references/evaluation-and-metrics.md)
for result semantics and [troubleshooting](references/troubleshooting.md) for
failures.

## Hard gates

- This repository documents a two-stage pipeline: stage 1 produces QPN/query
  artifacts used by stage 2. Do not start stage 2 until its configured query
  files and labels are present; a stage-1 checkpoint alone is not a substitute
  for stage-2 query data.
- Full train/test requires a CUDA-capable, compatible legacy OpenMMLab stack,
  SemanticKITTI data and the required pretrained/checkpoint files. Distributed
  configs use NCCL. The documented examples use four GPUs; one GPU is a
  diagnostic/smaller run, not an equivalence claim.
- Never infer successful training or metric values from imports, config loads,
  or command construction. The prepared environment passed project dependency
  and `SSCMetrics` imports, but no full training/evaluation was run and no
  final metric values are verified without real SemanticKITTI artifacts.
- The repository has no small native train/test test suite. Prefer parser/help,
  config/static checks, and this preflight helper; do not download data/weights
  or launch training while creating or verifying this skill.

## Operating route

1. Identify stage and variant (`qpn.py`, `voxformer-S.py`, or
   `voxformer-T.py`; use the model-configuration sub-skill for variant details).
2. Validate environment/backend, dataset layout, labels, depth/pseudo-voxel and
   query artifacts with the sibling environment and dataset sub-skills.
3. Choose a fresh work directory or explicitly confirm resume/overwrite policy.
4. For a deterministic helper-only smoke check, run
   `python scripts/preflight_train_test.py --self-test`. It uses only a private
   temporary fixture, never launches a subprocess, and does not touch user
   paths. For an actual request, run `scripts/preflight_train_test.py` with the
   config and checkpoint paths. It only reads metadata/existence and prints a
   plan; it never launches, downloads, creates directories, or overwrites
   results.
5. Review the generated command, GPU count, port, checkpoint/config pairing,
   output paths, and expected validation behavior with the operator.
6. Only then run the repository command. Record the exact config, commit,
   checkpoint, GPU count, work directory, output/result paths, and metrics.

## Route boundaries

- Environment, CUDA/MMCV ABI, pretrained placement, and custom deform3D builds:
  `../environment-and-installation/SKILL.md`.
- SemanticKITTI layout, preprocessing, labels, and query suffixes:
  `../dataset-preparation/SKILL.md`.
- Stage/config selection, temporal cameras, and standard versus deform3D:
  `../model-configuration/SKILL.md`.
- Do not use this skill to regenerate data, build optional extensions, fetch
  weights, or claim a reproduced benchmark.

## Bundled resources

- [references/workflow-commands.md](references/workflow-commands.md)
- [references/evaluation-and-metrics.md](references/evaluation-and-metrics.md)
- [references/troubleshooting.md](references/troubleshooting.md)
- [scripts/preflight_train_test.py](scripts/preflight_train_test.py)
