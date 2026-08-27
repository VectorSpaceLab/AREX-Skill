---
name: classification
description: "Route and operate PaddleViT image-classification workflows across
  standalone model directories, shared configuration/data/train/eval surfaces,
  checkpoint and AMP handling, and the facial-expression Swin variant."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# PaddleViT classification

Use this route for image-level classification in PaddleViT: choose a model
family, validate a config and ImageNet-style data layout, build a model, load a
checkpoint, evaluate, fine-tune, or decide whether AMP/distributed training is
appropriate. Use it also for the repository's Swin-based ABAW facial-expression
workflow.

## Route the request

1. Select exactly one standalone model directory. Keep its `config.py`, model
   module, `datasets.py`, and main script together: PaddleViT is a collection
   of standalone projects, not an installable Python package.
2. Read [model overview](references/model-overview.md) and select the family
   named by the config/checkpoint. If none is named, choose a baseline that
   meets the actual constraint (for example ViT for an explicit reference,
   SwinTransformer for hierarchical windows, or MobileViT/MobileOne for a
   mobile-oriented comparison), then state the choice.
3. Read [configuration](references/configuration.md), then run the safe standalone
   [config check](scripts/check_classification_config.py) with a YAML path. Its
   result is structural validation, not a claim that the model or dataset is
   usable.
4. For a no-data/no-checkpoint output-contract check, run the deterministic
   standalone [model smoke](scripts/classification_model_smoke.py). It defines
   a tiny independent Paddle classifier and never imports the checkout.
5. Use [workflows](references/workflows.md) for evaluation, fine-tuning, AMP, distributed
   operation, and facial expression. Consult [troubleshooting](references/troubleshooting.md)
   for recovery.

## Coverage

This sub-skill owns supervised classification across ViT, DeiT,
SwinTransformer, VOLO, CSwin, PVTv2, BEiT, MobileViT, ViP, XCiT, PiT, HaloNet,
PoolFormer, BoTNet, CvT, HVT, TopFormer, ConvNeXt, CoaT, ResT/ResTV2,
MLP-Mixer, ResMLP, gMLP, FF_Only, RepMLP, CycleMLP, ConvMixer, ConvMLP,
RepLKNet, MobileOne, and MAE fine-tuning/import surfaces. It preserves the
same operating conventions for related catalog folders when a task names one,
but requires that folder's own README/config/module before asserting a builder
or CLI detail.

MAE masked pretraining is not ordinary supervised classification; this route
covers its classifier fine-tuning surface and safe config/model inspection. The
facial-expression variant has aligned face frames and ABAW annotations, plus
`all`, `coarse`, and `negative` label mappings; it is not an ImageNet2012
list-file workflow.

## Boundaries and links

- Do **not** route object detection, semantic segmentation, GAN, or DINO here.
- Do not perform generic static export, inference-engine conversion, or
  deployment benchmarking here; route that to
  `../deployment-and-operations/SKILL.md`.
- Do not download data/checkpoints, launch full training, or infer benchmark
  accuracy from a config/smoke result.

## Source-root and environment contract

Run a chosen model from its own source directory or put **only that directory**
first on `PYTHONPATH`; several folders reuse bare module names such as
`config`, `datasets`, and `utils`. Importing multiple directories in one
interpreter can silently load the wrong module; use a fresh process per model.
The bundled scripts deliberately do not use this source-root import convention:
they are safe standalone checks.

The verified inspection environment contains PaddlePaddle GPU 2.6.2, yacs
0.1.8, and PyYAML. The repository documents older PaddlePaddle 2.1-era APIs,
so a per-family source/API smoke is required before claiming current-runtime
compatibility. The observed default ViT fact is `vit.build_vit(config)` with a
`[1, 1000]` output on `gpu:0`; it is a shape/import fact only.

Report the selected source-root directory, config and data/checkpoint paths,
model builder, preprocessing contract, device/AMP/distributed choice, checks
run, and unresolved incompatibilities. Never include machine-specific
activation commands or private environment paths in a downstream handoff.
