---
name: domain-and-restoration
description: "Operate Keras-GAN CCGAN, ContextEncoder, PixelDA, and SRGAN
  workflows for inpainting, domain adaptation, and super-resolution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Domain Adaptation and Restoration Workflows

Use this sub-skill when the task involves Keras-GAN's specialized image restoration or domain-adaptation examples:

- context-conditional MNIST inpainting with `CCGAN`
- CIFAR-10 cat/dog context encoding with `ContextEncoder`
- MNIST to MNIST-M pixel-level domain adaptation with `PixelDA`
- CelebA-style 4x super-resolution with `SRGAN`

Do not use this sub-skill for CycleGAN, DiscoGAN, or Pix2Pix image translation, and do not use it for baseline MNIST/Wasserstein generators. Route those requests to the sibling image-translation or mnist-generators sub-skills instead.

## Fast routing

1. Identify the workflow and data risk:
   - `CCGAN`: MNIST, grayscale 32x32, 10x10 random zero mask, can request a Keras MNIST download if the dataset cache is absent.
   - `ContextEncoder`: CIFAR-10 cats/dogs, RGB 32x32, 8x8 random zero mask, can request a Keras CIFAR-10 download if the dataset cache is absent.
   - `PixelDA`: MNIST domain A and MNIST-M domain B, RGB 32x32 cached arrays, may try to fetch or rebuild MNIST-M artifacts if cache files are incomplete.
   - `SRGAN`: image directory named `img_align_celeba`, derived 64x64 low-resolution and 256x256 high-resolution pairs, constructor can request VGG19 ImageNet weights.
2. Before training or adapting code, read the reference that matches the issue:
   - [Model/API reference](references/model-api-reference.md) for class names, method signatures, shapes, losses, and outputs.
   - [Workflow playbook](references/workflows.md) for safe dry runs, short-run setup, and adaptation steps.
   - [Data formats](references/data-formats.md) for expected dataset/cache layouts and normalization.
   - [Troubleshooting](references/troubleshooting.md) for legacy Keras/TensorFlow, SciPy image APIs, PixelDA cache/network, and SRGAN VGG19 failures.
3. Use the bundled safe checker instead of importing Keras or running full training when validating local files:

```bash
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --help
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow srgan --data-root ./datasets --dataset-name img_align_celeba --min-images 8
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow pixelda --data-root ./datasets --json
python sub-skills/domain-and-restoration/scripts/check_restoration_layout.py --workflow ccgan --check-output-dirs --output-root .
```

The checker only uses the Python standard library. It never downloads data, imports Keras, mutates datasets, or launches training.

## Operating constraints

- Treat this repository as a stale educational script collection, not as an installable Python package.
- Use a legacy-compatible runtime for actual model construction or training: the scripts were verified around Python 3.7-era, TensorFlow 1.15.x, Keras 2.2.x, keras-contrib 2.0.x, NumPy 1.18.x, SciPy 1.2.x, Matplotlib, Pillow, and scikit-image.
- Avoid network access unless the user explicitly permits dataset or VGG19 weight downloads.
- Avoid full default training loops: the upstream defaults are tens of thousands of epochs.
- Create or validate output directories before short runs; several scripts save figures or model JSON/weights into relative `images/` and `saved_model/` paths.
- For SRGAN dry runs, do not instantiate `SRGAN()` unless VGG19 ImageNet weights are already cached or the user accepts the download risk.

## Expected deliverables for common tasks

- Dataset-readiness diagnosis: run `scripts/check_restoration_layout.py`, report missing files/directories, and cite the relevant [data format](references/data-formats.md) section.
- Adaptation plan: identify the model class, expected input/label shapes, data-loader behavior, output paths, and the smallest safe smoke test from [workflows](references/workflows.md).
- Troubleshooting answer: map the error to the closest symptom in [troubleshooting](references/troubleshooting.md), then give a bounded fix that does not require reopening the original repository.
