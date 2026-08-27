---
name: training-and-configs
description: "Configure and launch Neuralangelo training runs, validate configs,
  manage checkpoints, W&B, CUDA, and memory trade-offs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Neuralangelo Training and Configs

Use this sub-skill when the user needs to configure, validate, launch, monitor,
or resume Neuralangelo training from an already prepared dataset and config.
Assume commands are run from the user's Neuralangelo project root unless a
command explicitly says otherwise.

## Owns

- `train.py` command construction, including `torchrun` versus single-process
  launch choices.
- Neuralangelo YAML config inheritance, command-line override syntax, and
  strict override validation.
- Operational meaning of the base, DTU, Tanks and Temples, and generated custom
  config fields.
- Training-time API map for `Config`, `Model`, `Dataset`, `Trainer`, optimizer,
  scheduler, W&B, logging, checkpoints, resume, CUDA, DDP, and memory settings.
- Safe preflight summaries using the bundled scripts:
  - `scripts/plan_training_command.py`
  - `scripts/inspect_config_summary.py`

## Reroute

- Raw video, image extraction, COLMAP, `transforms.json` generation, DTU/Tanks
  conversion, pose inspection, or bounding-sphere adjustment: use the
  `data-preparation` sub-skill.
- Mesh/isosurface extraction, `extract_mesh.py`, texturing, block resolution, or
  post-training mesh cleanup: use the `mesh-extraction` sub-skill.

## Fast workflow

1. Confirm a prepared data root exists and contains `transforms.json` plus the
   image paths named in that file.
2. Inspect or generate a YAML config, then summarize it with
   `scripts/inspect_config_summary.py`.
3. Plan the launch command with `scripts/plan_training_command.py` instead of
   hand-editing a long `torchrun` line.
4. For the first expensive run, reduce `max_iter`, validation frequency, and
   checkpoint interval with command-line overrides, then scale back to the full
   schedule after the config and data loader are proven.
5. Monitor `logs/<group>/<name>/config.yaml`, checkpoints, W&B status, and
   CUDA memory; use the recipes in `references/troubleshooting.md` for common
   failures.

## Reference map

- `references/workflows.md`: concrete launch, resume, multi-GPU, logging, and
  smoke-test workflows.
- `references/configuration.md`: inherited config fields, strict overrides,
  dataset/model knobs, memory reductions, and validation checklist.
- `references/api-reference.md`: operational source-code map for the training
  stack and safe boundaries.
- `references/troubleshooting.md`: CUDA, tiny-cuda-nn, config, DDP, W&B,
  checkpoint, and data-shape failures.
