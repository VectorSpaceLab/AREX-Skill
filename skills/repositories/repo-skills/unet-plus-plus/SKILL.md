---
name: unet-plus-plus
description: "Routes UNet++ work across the official PyTorch nnU-Net stack and
  the legacy Keras segmentation-models stack."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# UNet++

Use this skill for the repository's two supported operating stacks:

- `sub-skills/nnunet/` for the official PyTorch nnU-Net implementation.
- `sub-skills/keras/` for the official Keras / segmentation_models implementation.

This repo is not a single uniform package. The PyTorch and Keras sides have
very different dependency and runtime assumptions, so future agents should pick
one sub-skill first instead of trying to force a combined environment.

## What this skill covers

- 3D nnU-Net training, preprocessing, inference, ensembling, pretrained-model
  management, and trainer/model-selection utilities.
- 2D Keras segmentation model construction, backbone selection, preprocessing,
  and the BRATS2013 application workflow.
- Safety guidance for legacy TensorFlow/Keras versus modern PyTorch/CUDA
  environments.

## Route first, then read deeper

If the user mentions any of these signals, route immediately:

- `nnUNet_train`, `nnUNet_predict`, `nnUNet_plan_and_preprocess`,
  `nnUNet_convert_decathlon_task`, `nnUNet_ensemble`, `nnUNet_determine_postprocessing`,
  `nnUNet_download_pretrained_model`, `nnUNet_change_trainer_class`,
  `TaskXXX`, `nnUNet_raw_data_base`, `nnUNet_preprocessed`, or `RESULTS_FOLDER`
  -> use `sub-skills/nnunet/`.
- `Unet`, `Nestnet`, `Xnet`, `FPN`, `PSPNet`, `segmentation_models`,
  `BRATS2013_application.py`, `backbone`, `vgg16`, `resnet50`, or legacy
  TensorFlow/Keras 1.x setup -> use `sub-skills/keras/`.

## Start here

- Read [`references/overview.md`](references/overview.md) for the stack split
  and a quick capability map.
- Read [`references/troubleshooting.md`](references/troubleshooting.md) for
  cross-cutting environment and routing pitfalls.
- Read [`references/repo-provenance.md`](references/repo-provenance.md) if you
  need to check whether the generated skill is stale relative to the source
  checkout.

## Minimal verification helpers

- [`sub-skills/nnunet/scripts/check-nnunet-runtime.py`](sub-skills/nnunet/scripts/check-nnunet-runtime.py)
  checks the nnU-Net import path, CLI entry points, CUDA status, and a tiny
  sliding-window smoke.
- [`sub-skills/keras/scripts/check-segmentation-models.py`](sub-skills/keras/scripts/check-segmentation-models.py)
  checks the Keras segmentation model builders on safe tiny inputs.

## Operating rules

- Do not mix the two stacks into one Python environment unless you already know
  the exact compatibility story. The inspected repo snapshot required separate
  environments.
- Do not depend on the original checkout at runtime. Every instruction here is
  written to be useful after the source repo is gone.
- Prefer the dedicated sub-skill for concrete workflows and use this root only
  as a router.
- Treat full nnU-Net training, legacy BRATS2013 training, pretrained model
  downloads, and other large workflows as documented operations, not as default
  smoke tests.

## Common user prompts this router should send onward

- "How do I train UNet++ with nnU-Net?" -> `sub-skills/nnunet/`
- "How do I build Xnet with a ResNet backbone?" -> `sub-skills/keras/`
- "Why does nnUNet_predict say RESULTS_FOLDER is missing?" -> `sub-skills/nnunet/`
- "Why does PSPNet reject my input shape?" -> `sub-skills/keras/`
- "What pretrained nnU-Net models are available?" -> `sub-skills/nnunet/`
- "Which backbones and weights does the Keras stack support?" ->
  `sub-skills/keras/`

## Cross-cutting references

- [`references/overview.md`](references/overview.md) for the repo split.
- [`references/troubleshooting.md`](references/troubleshooting.md) for shared
  environment and selection issues.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json)
  for managed router placement.

## What this root does not do

- It does not teach the full nnU-Net or Keras APIs inline.
- It does not describe source-checkout-only files.
- It does not bundle installation logs, verification reports, or usability
  cases. Those belong in the review/test artifact tree.

Use the sub-skill that matches the user's stack, then follow its bundled
references and scripts.
