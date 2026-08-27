---
name: mnist-generators
description: "Use, inspect, adapt, and troubleshoot Keras-GAN standalone
  MNIST-style generator scripts that do not require paired image-domain
  directories."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# MNIST Generators

Use this sub-skill for Keras-GAN's standalone educational scripts that load Keras MNIST-like arrays directly instead of requiring paired image-domain folders. It covers GAN, DCGAN, CGAN, ACGAN, SGAN, InfoGAN, LSGAN, BGAN, BiGAN, Adversarial Autoencoder, CoGAN, DualGAN, WGAN, and WGAN-GP.

Do not start a full training run from a script's `if __name__ == "__main__"` defaults unless the user explicitly accepts long CPU/GPU training, dataset download/cache behavior, and generated file writes.

## Route elsewhere

- CycleGAN, DiscoGAN, and Pix2Pix need image-domain or paired-image datasets: use the image-translation sub-skill.
- CCGAN, context encoder, PixelDA, and SRGAN need inpainting, domain-adaptation, restoration, super-resolution, or image-directory handling: use the domain-and-restoration sub-skill.
- Cross-cutting installation issues belong in the root Keras-GAN compatibility and troubleshooting references; this sub-skill records only the MNIST-generator-specific symptoms.

## Fast workflow

1. Choose the script/class from [references/model-api-reference.md](references/model-api-reference.md). Check the train signature, default `__main__` epoch count, output path, and special loss methods before adapting.
2. From this generated skill's root directory, run static inspection without importing Keras:

   ```bash
   python sub-skills/mnist-generators/scripts/model_inventory.py --repo-root /path/to/a/Keras-GAN-checkout
   python sub-skills/mnist-generators/scripts/model_inventory.py --repo-root /path/to/a/Keras-GAN-checkout --json
   ```

3. For dependency or constructor smoke checks, default to import-only and add `--construct` only after confirming a legacy Keras/TensorFlow runtime:

   ```bash
   python sub-skills/mnist-generators/scripts/dry_run_model.py --repo-root /path/to/a/Keras-GAN-checkout --model gan
   python sub-skills/mnist-generators/scripts/dry_run_model.py --repo-root /path/to/a/Keras-GAN-checkout --model dcgan --construct
   python sub-skills/mnist-generators/scripts/dry_run_model.py --repo-root /path/to/a/Keras-GAN-checkout --model wgan-gp
   ```

4. Follow [references/workflows.md](references/workflows.md) for safe adaptation, short smoke runs, output-directory handling, and model comparison.
5. Use [references/troubleshooting.md](references/troubleshooting.md) when imports fail, WGAN-GP cannot find `_Merge`, `images/` or `saved_model/` is missing, Keras dataset downloads are blocked, or a run is taking too long.

## Safety rules

- The bundled inventory script is static and safe: no Keras import, no network, no training, and no writes except optional shell redirection by the caller.
- The bundled dry-run script imports a selected source file and constructs a model only when `--construct` is supplied; it never calls `train(...)`.
- The original scripts hard-code `images/...` and sometimes `saved_model/...` relative to the current working directory. Create those directories in a temporary run directory before any training smoke.
- WGAN-GP's `RandomWeightedAverage` uses a legacy private Keras `_Merge` API and a fixed batch dimension of 32; treat modern-Keras failures as compatibility diagnostics, not model-quality failures.
