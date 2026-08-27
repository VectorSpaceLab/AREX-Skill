---
name: image-translation
description: "Use Keras-GAN CycleGAN, DiscoGAN, and Pix2Pix image-to-image
  translation workflows safely: model APIs, dataset layout checks, adaptation
  guidance, and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Image Translation: CycleGAN, DiscoGAN, Pix2Pix

Use this sub-skill when a task involves Keras-GAN image-to-image translation with
CycleGAN, DiscoGAN, or Pix2Pix. Treat the upstream project as a stale collection
of standalone educational scripts, not an importable package or maintained
training framework.

## Route here for

- Unpaired two-domain translation such as `apple2orange`, `summer2winter_yosemite`,
  `horse2zebra`, or other `A`/`B` domain folders.
- Paired side-by-side conditional translation such as `facades` or
  `edges2shoes`.
- Inspecting or adapting the class APIs `CycleGAN`, `DiscoGAN`, and `Pix2Pix`,
  their `DataLoader` helpers, PatchGAN output shapes, sample-image behavior, or
  stale Keras/TensorFlow runtime assumptions.
- Safe dataset-layout validation before any constructor smoke test or training
  attempt.

## Route elsewhere

- MNIST or latent-vector generators such as GAN, DCGAN, CGAN, AC-GAN, InfoGAN,
  BiGAN, CoGAN, LSGAN, WGAN, or WGAN-GP.
- Specialized restoration/domain-adaptation workflows such as Context Encoder,
  SRGAN, or PixelDA.
- Network dataset acquisition or long training jobs unless the user explicitly
  authorizes them; the original download scripts are reference-only.

## Start with these bundled resources

1. Choose the workflow and API surface in
   [references/model-api-reference.md](references/model-api-reference.md).
2. Validate local data with the safe helper before running any model code:

   ```bash
   python sub-skills/image-translation/scripts/check_dataset_layout.py \
     --dataset-root datasets/apple2orange \
     --workflow cyclegan \
     --min-files 1 \
     --check-images
   ```

   Replace `datasets/apple2orange` with the dataset directory visible to the
   caller. The helper performs no network access, imports no Keras models, and
   does not train.
3. Use [references/data-formats.md](references/data-formats.md) for expected
   folder layouts, split names, side-by-side image conventions, and preprocessing
   assumptions.
4. Use [references/workflows.md](references/workflows.md) for bounded adaptation,
   constructor-smoke, dataset-name, image-resolution, and sample-output workflows.
5. Use [references/troubleshooting.md](references/troubleshooting.md) when imports,
   SciPy image utilities, empty batches, PatchGAN labels, or paired/unpaired data
   conventions fail.

## Safety defaults

- Do not run the original network download scripts automatically.
- Do not run full training as a verification step; prefer dataset checks and
  constructor/import smoke checks in a pinned legacy environment.
- Keep generated outputs in caller-controlled directories such as
  `images/<dataset_name>/<epoch>_<batch>.png`; note that the educational scripts
  create `saved_model/` directories in the checkout but do not save weights by
  default.
- If adapting code, preserve the `disc_patch = (img_rows / 2**4, img_rows /
  2**4, 1)` pattern and update it whenever image resolution changes.
