---
name: segmentation-workflows
description: "Operate MedicalZooPytorch 3D segmentation model selection,
  training, checkpointing, TensorBoard logging, and inference/visualization
  workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: MIT
---

# Segmentation workflows

Use this sub-skill for the 3D segmentation branch of MedicalZooPytorch: model selection, model construction, training loops, checkpointing, TensorBoard logging, and inference/visualization.

## What this sub-skill covers

- Model factory routing through `lib.medzoo.create_model(args)`.
- The common model base in `BaseModel` for checkpoint save/restore and inference.
- The bundled training loop in `lib.train.Trainer` and the generic scaffold in `lib.train.BaseTrainer`.
- TensorBoard and CSV logging through `lib.visual3D_temp.TensorboardWriter`.
- Non-overlap inference and 3D volume visualization helpers in `lib.visual3D_temp.viz`.
- 3D model families: `UNET3D`, `VNET`, `VNET2`, `DENSENET1`, `DENSENET2`, `DENSENET3`, `HYPERDENSENET`, `SKIPDENSENET3D`, `DENSEVOXELNET`, `RESNET3DVAE`, `RESNETMED3D`, and `HIGHRESNET`.

## Fast path

1. Choose a model family and a valid channel count for that family.
2. Build the model with `lib.medzoo.create_model(args)`.
3. Create the loss, loaders, and trainer.
4. Train, checkpoint, and monitor scalars.
5. Use the visualization helpers for patch-based inference and saved volumes.

## Entry points

- `references/model-overview.md` for the supported 3D model families and factory behavior.
- `references/workflows.md` for training, checkpointing, TensorBoard, and inference patterns.
- `references/troubleshooting.md` for known model- and workflow-level pitfalls.
- `scripts/smoke_model_factory.py` for a safe factory-and-forward smoke check.
- `scripts/smoke_writer.py` for a temp-directory TensorBoard writer smoke check.

## Operating notes

- The factory uses uppercase model ids and asserts membership in its model list.
- `HYPERDENSENET` selects the 2-channel or 3-channel variant from `inChannels`.
- `DENSENET2` and `DENSENET3` are multi-stream models; match the input channel count to the branch you want. The bundled factory smoke skips `DENSENET2` by default because the source channel math is known to fail there.
- `RESNETMED3D` is wired through the factory at depth 18; use the direct generator if you need a different depth.
- Some forward methods return tuples. Unpack them before you compute losses or log shapes.
- The bundled factory smoke has a `--include-known-broken` flag if you need to reproduce the `DENSENET2` channel-math failure explicitly.
- The legacy inference demo depends on a checkpoint and GPU-style tensor placement; treat it as reference-only.
