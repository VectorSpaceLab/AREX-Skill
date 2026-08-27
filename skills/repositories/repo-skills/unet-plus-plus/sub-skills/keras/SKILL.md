---
name: keras
description: "Guides the legacy Keras segmentation-models stack for UNet++,
  Nestnet, Xnet, FPN, PSPNet, backbone selection, and BRATS2013 usage."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# Keras

Use this sub-skill for the repository's legacy 2D Keras stack. It covers the
`segmentation_models` package, the original helper functions, and the
BRATS2013 application script.

## Route here when the user asks about

- `Unet`, `Nestnet`, `Xnet`, `FPN`, `PSPNet`, or `segmentation_models`.
- Backbone names such as `vgg16`, `resnet50`, `densenet121`, `inceptionv3`, or
  `inceptionresnetv2`.
- `BRATS2013_application.py`, `plot_model`, `pydot`, or legacy TensorFlow 1.x /
  Keras 2.2.2 setup.
- Input-shape issues, backbone weight availability, or PSPNet size guards.

## What this sub-skill does

- Explains how to instantiate the segmentation models with safe defaults.
- Summarizes available backbones and preprocessing choices.
- Helps diagnose legacy dependency problems and input-shape restrictions.
- Gives a safe runtime smoke script for building tiny models without training.

## What to read first

- [`references/legacy-stack.md`](references/legacy-stack.md) for the version and
  environment assumptions.
- [`references/backbones.md`](references/backbones.md) for the backbone catalog
  and preprocessing behavior.
- [`references/api-reference.md`](references/api-reference.md) for builder
  signatures and helper functions.
- [`references/workflows.md`](references/workflows.md) for custom-data and
  BRATS2013 workflows.
- [`references/troubleshooting.md`](references/troubleshooting.md) for common
  shape, download, and dependency problems.

## Recommended workflow order

1. Check whether the user really needs the legacy Keras stack.
2. Confirm the TensorFlow / Keras / Python compatibility assumptions.
3. Pick the architecture and backbone.
4. Verify input-shape constraints before compiling or fitting.
5. Use the bundled smoke script for a tiny build check.

## Important guardrails

- This stack is separate from nnU-Net. Do not mix it with the modern PyTorch
  environment.
- The inspected snapshot used Python 3.6 plus TensorFlow 1.4.1 and Keras
  2.2.2 for the legacy route.
- `BRATS2013_application.py` is a data-bound workflow with many assumptions; it
  is not a cheap smoke test.
- `classification_models` pretrained weights and test code can require the
  network, so treat them as reference-only unless the user explicitly wants a
  download path.
- The model builders should be exercised with `encoder_weights=None` first when
  you only need structure and shape validation.

## Bundled runtime helper

- [`scripts/check-segmentation-models.py`](scripts/check-segmentation-models.py)
  builds tiny `Unet`, `Nestnet`, `Xnet`, `FPN`, and `PSPNet` models as a safe
  runtime smoke.

## Common questions this sub-skill answers

- Which backbones are available, and which preprocessing function goes with
  each one?
- Why does a model reject my input size?
- What are the public builder signatures for Unet, Nestnet, Xnet, FPN, and
  PSPNet?
- How do I interpret the BRATS2013 application arguments and data layout?
- Why is `plot_model` or `pydot` failing in this environment?
- What should I do when pretrained weights cannot be downloaded?

## Where to go next

- Use [`references/workflows.md`](references/workflows.md) for the concrete
  recipes.
- Use [`references/troubleshooting.md`](references/troubleshooting.md) when the
  failure is about shape guards, legacy package pins, or optional dependencies.
- Use the root [`../../SKILL.md`](../../SKILL.md) only if the user has not yet
  chosen between the Keras and nnU-Net stacks.
