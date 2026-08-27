---
name: training
description: "Configure and run DeblurGAN training, checkpoints, and loss selection."
metadata:
  disco-role: operating
disable-model-invocation: true
license: NOASSERTION
---

# training

Use this sub-skill when the task is to configure, start, resume, or smoke-test DeblurGAN training.

## What this route covers

- The training loop, optimizer setup, checkpoint saving, and learning-rate decay.
- Generator, discriminator, and loss-selection choices.
- Residual learning and the paper-style perceptual-loss path.
- Safe smoke-mode execution for verification or troubleshooting.
- The portable wrapper that replaces the source script's hardcoded local overrides.

## Read this when the user asks for

- A command to train on a new paired dataset.
- Help choosing `content_gan`, `pix2pix`, `gan`, `lsgan`, or `wgan-gp` settings.
- Advice on checkpoint names, resume behavior, or output locations.
- A minimal training smoke run that does not depend on the source repository's hardcoded data path.

## Primary files

- `scripts/run_training.py` — portable wrapper around the repository's training loop.
- `references/workflows.md` — recommended training flags, checkpoint layout, and smoke mode.
- `references/troubleshooting.md` — CUDA, VGG19, visdom, and checkpoint failures.

## Workflow summary

1. Confirm that the paired training data is ready.
2. Choose the loss/model combination:
   - `model=content_gan` uses perceptual loss on VGG19 features.
   - `model=pix2pix` uses an L1 content loss.
   - `gan_type` selects the discriminator loss family.
3. Use the bundled wrapper instead of the source `train.py` so the run is not tied to a hardcoded local dataroot.
4. Keep the checkpoint directory writable and create it before the run begins.
5. For quick validation, use the wrapper's smoke options to cap the number of optimization steps.

## Decision points

- If the task is only about preparing the dataset, route back to the data-preparation sub-skill.
- If the task is only about restoring a single image, route to inference.
- If the caller wants the paper-style setup, prefer the CUDA path and the perceptual-loss route.
- If the caller wants a lightweight sanity run, prefer the wrapper's headless smoke mode and a tiny step cap.

## Important reminders

- The source `train.py` hardcodes a local dataroot and several option overrides. Do not preserve those values in the reusable wrapper.
- The perceptual-loss path requires CUDA because the implementation moves the VGG19 feature extractor to GPU.
- Live plotting is optional; do not block training guidance on visdom unless the user explicitly wants interactive plots.

## Cross-links

- Read the root installation reference before training if torch or CUDA is missing.
- Read the root troubleshooting reference for the paper-vs-source `gan_type` mismatch.
- Read the data-preparation sub-skill before launching the training loop.
