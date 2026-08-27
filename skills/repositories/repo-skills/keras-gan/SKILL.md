---
name: keras-gan
description: "Use Keras-GAN legacy Keras/TensorFlow GAN scripts for image
  generation, image-to-image translation, inpainting, PixelDA, and SRGAN
  workflows with safe inspection and troubleshooting."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Keras-GAN Repo Skill

Use this repo skill when a task involves the Keras-GAN repository: a stale but useful collection of standalone educational Keras implementations of generative adversarial networks. The repository is not an installable Python package; treat each model directory as a standalone script family and use the bundled helpers here to inspect, validate, or adapt it safely.

Do **not** launch the original scripts' `__main__` defaults as routine checks. Many defaults run thousands of epochs, may download Keras datasets or external archives, and write relative `images/` or `saved_model/` outputs.

## First steps

1. Read [references/compatibility-and-install.md](references/compatibility-and-install.md) before running any Keras code. The scripts target legacy standalone Keras 2.x with TensorFlow 1.x behavior.
2. Run the bundled runtime checker when diagnosing an environment:

   ```bash
   python scripts/check_legacy_runtime.py
   python scripts/check_legacy_runtime.py --json
   ```

3. Use [references/model-catalog.md](references/model-catalog.md) to choose the right model family.
4. Route to the smallest focused sub-skill below.
5. Use [references/troubleshooting.md](references/troubleshooting.md) for cross-cutting install/import, stale dependency, output-path, data-download, and long-training failures.
6. Read [references/repo-provenance.md](references/repo-provenance.md) before deciding whether this skill is current for a checkout.

## Route by task

| User task or signal | Use |
| --- | --- |
| Vanilla GAN, DCGAN, CGAN, AC-GAN, SGAN, InfoGAN, LSGAN, BGAN, BiGAN, Adversarial Autoencoder, CoGAN, DualGAN, WGAN, or WGAN-GP on MNIST-style arrays | [sub-skills/mnist-generators/SKILL.md](sub-skills/mnist-generators/SKILL.md) |
| Compare GAN variants, inspect class APIs, run static inventory, or smoke-test representative model constructors without training | [sub-skills/mnist-generators/SKILL.md](sub-skills/mnist-generators/SKILL.md) |
| CycleGAN, DiscoGAN, Pix2Pix, `apple2orange`, `edges2shoes`, `facades`, unpaired A/B domains, paired side-by-side image translation, PatchGAN label shapes | [sub-skills/image-translation/SKILL.md](sub-skills/image-translation/SKILL.md) |
| Validate image-translation dataset folders before training or adapting code | [sub-skills/image-translation/scripts/check_dataset_layout.py](sub-skills/image-translation/scripts/check_dataset_layout.py) via the image-translation sub-skill |
| CCGAN, ContextEncoder, context inpainting, CIFAR cats/dogs missing patches, PixelDA MNIST-to-MNIST-M adaptation, SRGAN 4x super-resolution, CelebA/VGG19 risk | [sub-skills/domain-and-restoration/SKILL.md](sub-skills/domain-and-restoration/SKILL.md) |
| Validate PixelDA cache files, SRGAN image directory, or restoration workflow output directories without importing Keras | [sub-skills/domain-and-restoration/scripts/check_restoration_layout.py](sub-skills/domain-and-restoration/scripts/check_restoration_layout.py) via the domain-and-restoration sub-skill |

## Operating constraints

- Use a legacy runtime for faithful execution: Python 3.7-era, TensorFlow 1.15.x, Keras 2.2.x, keras-contrib 2.0.x, NumPy 1.18.x, SciPy 1.2.x, Matplotlib, Pillow, scikit-image, h5py, and protobuf below 3.21 are the verified compatibility family.
- Modern Keras 3 or TensorFlow 2 errors are usually dependency-staleness issues, not evidence that the original GAN idea is invalid.
- Treat GPU as optional acceleration. The selected safe verification scope is CPU-compatible; full training can use GPUs only after the user accepts runtime, data, and output side effects.
- Original dataset download scripts and Keras dataset loaders can perform network access. Ask before running them when network is not already authorized.
- Keep all generated outputs in caller-controlled run directories. The source scripts write relative paths such as `images/`, `images/<dataset_name>/`, and `saved_model/`.

## Safe verification patterns

- Static source inventory is preferred before Keras imports.
- Constructor smoke checks are acceptable only in a legacy-compatible runtime and should never call `train(...)`.
- Dataset layout helpers are safe: they do not import Keras, download data, train models, or mutate datasets.
- Full native training loops are skip-expensive by default. Use one-epoch wrappers with synthetic or already-cached data only after the user accepts short compute and file writes.

## When not to use this skill

- The user needs a maintained GAN framework, modern `tf.keras`, PyTorch GAN implementations, or production-grade training infrastructure rather than Keras-GAN's educational scripts.
- The task is Stable Diffusion, Diffusers, LoRA, ComfyUI, or modern image-generation pipelines unrelated to this repository.
- The task is repository maintenance unrelated to using/adapting the GAN scripts; use a Python repository-maintenance workflow instead.
