---
name: generative-models
description: "Routes Papers-in-100-Lines GAN, VAE, flow, diffusion, DreamBooth,
  Stable Diffusion, and image-translation implementation tasks."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Generative Models

Use this sub-skill when the user asks about generative implementations in
Papers-in-100-Lines: GAN variants, VAEs, normalizing flows, diffusion samplers,
DreamBooth, Stable Diffusion, image translation, SNL/AALR, or related toy
density/image generation examples.

## Read these bundled files

- [Model family guide](references/model-family-guide.md) maps the bundled
  catalog entries to model families, key classes/functions, data assumptions,
  and safe adaptation recipes.
- [Troubleshooting](references/troubleshooting.md) covers dataset downloads,
  old dependency pins, CUDA hardcodes, missing Stable Diffusion weights,
  output-image side effects, and shape/loss failures.
- [Implementation index](../../references/implementation-index.md) lists all
  entries; use it when the user gives only a paper title or acronym.
- [Dependency and backend guide](../../references/dependency-and-backend-guide.md)
  explains why each paper should normally get its own environment.
- [summarize_generative_entries.py](scripts/summarize_generative_entries.py)
  summarizes this family's catalog entries without importing torch, Keras, or
  Diffusers.

## Trigger routes

- **GAN or image translation**: original GAN, CGAN, DCGAN, LSGAN, WGAN,
  WGAN-GP, Improved GAN, ALI/AFL, pix2pix, CycleGAN.
- **VAE, flow, or density estimation**: Auto-Encoding Variational Bayes,
  NICE, Real NVP, MAF, planar flows, SNL, AALR-MCMC, Gromov-Wasserstein.
- **Diffusion and text-to-image**: nonequilibrium thermodynamics, DDPM, DDIM,
  PNDM, DPM-Solver, rectified flow, Stable Diffusion v1-5, DreamBooth.
- **Safety triage**: detect when the requested action would download MNIST,
  tokenizers, model weights, or run a long GPU training loop.

## Workflow for a future agent

1. If the paper is not explicit, query the catalog first:

   ```bash
   python ../../scripts/query_implementation_index.py --group generative-models --query "diffusion"
   ```

2. Read [Model family guide](references/model-family-guide.md) for the selected
   family and identify the reusable pattern: generator/discriminator, encoder
   and latent distribution, invertible transform, score/noise predictor, or
   sampler schedule.
3. Decide whether the user needs full reproduction or a small adaptation. For
   small adaptation, create a new tiny script with explicit `device`, data, and
   output arguments rather than importing a file that may download data at
   import time.
4. Use per-entry requirements from the catalog. Do not merge all generative
   requirements into one environment.
5. Validate with a bounded shape or loss check before training: generator output
   shape, flow log-prob shape, diffusion sample tensor shape, or text-to-image
   weight/tokenizer presence.

## Boundaries

Route NeRF, implicit representation, splatting, camera/ray, and 3D
reconstruction tasks to [neural-rendering-3d](../neural-rendering-3d/SKILL.md).
Route optimizers, activations, meta-learning, hypergradients, Deep Image Prior,
and Atari RL tasks to [optimization-meta-rl](../optimization-meta-rl/SKILL.md).
Use [paper-catalog-and-execution](../paper-catalog-and-execution/SKILL.md) for
lookup and first-run safety planning.
