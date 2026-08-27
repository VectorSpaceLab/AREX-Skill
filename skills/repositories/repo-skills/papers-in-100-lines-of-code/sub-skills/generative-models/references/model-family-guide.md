# Generative Model Family Guide

Use this reference after catalog lookup identifies a generative entry. The repo
implements compact educational scripts; use their distilled structure and
failure modes rather than assuming production training pipelines.

## Family map

| Family | Catalog entries | Common objects and patterns | Typical outputs | First validation |
|---|---|---|---|---|
| Basic and conditional GANs | Generative Adversarial Networks, Conditional GAN, DCGAN, LSGAN, WGAN, WGAN-GP, Improved GAN | `Generator`, `Discriminator`, `sample_noise`, `get_minibatch`, `train`; BCE, Wasserstein, gradient penalty or label conditioning | generated image grids or loss curves | instantiate generator/discriminator with tiny noise and assert output shape |
| Bidirectional/adversarial inference | ALI, Adversarial Feature Learning | encoder/generator/discriminator triads such as `GeneratorZ`, `GeneratorX`, `G`, `E`, `D`, `Ali` | latent/image reconstruction or adversarial feature plots | check encoder and generator dimensions before training |
| Image translation | pix2pix, CycleGAN | U-Net or ResNet generators, PatchGAN/N-layer discriminators, paired/unpaired datasets, replay buffer | translated images | validate paired/unpaired image tensor layout and output directory |
| VAEs and flows | Auto-Encoding Variational Bayes, NICE, Real NVP, MAF, planar flows | encoder/decoder, reparameterization, coupling layers, masks, batch norm, log-determinants | samples, latent density plots, log-likelihood curves | assert latent/sample/log-prob tensor shapes and finite log dets |
| Likelihood-free inference | SNL, AALR-MCMC | priors, simulators, MLP ratio estimators, MCMC/transition distributions | posterior samples and diagnostic plots | run a tiny simulator/ratio-estimator shape check |
| Diffusion and ODE samplers | nonequilibrium thermodynamics, DDPM, DDIM, PNDM, DPM-Solver, rectified flow | `DiffusionModel`, `UNet`, beta/alpha schedules, `training`, `sampling`, ODE/PNDM/DPM update rules | image or 2D distribution samples | reduce `T`, image size, and batch size; assert sample tensor shape |
| Text-to-image and fine-tuning | Stable Diffusion v1-5, DreamBooth | CLIP tokenizer/text encoder, VAE, U-Net noise predictor, EMA, dataset of instance/class images | generated sample image or fine-tuned subject outputs | verify local weights/tokenizer availability before allocating GPU |

## Adaptation recipes

### GAN-style scripts

- Pull out model classes and noise/data helpers into a new guarded script.
- Replace global `device` references with an explicit argument.
- Start with `batch_size=2`, one discriminator step, and synthetic data when the
  user is debugging shapes rather than results.
- For WGAN variants, keep optimizer, clipping/gradient penalty, and discriminator
  update count aligned with the entry's loss; do not swap BCE and Wasserstein
  losses casually.

### Flow and VAE scripts

- Preserve transform direction: normalizing flows usually return both transformed
  samples and log-determinant terms. Validate sign conventions before comparing
  likelihoods.
- Masks and squeeze/unsqueeze operations are shape-sensitive; use tiny tensors
  with known dimensions before training on images.
- Top-level dataset loading may happen at import time. Copy only class/function
  definitions into a clean module when doing offline smoke checks.

### Diffusion samplers

- Separate schedule construction from model definition. For a tiny smoke, use
  a small `T` and a small image size; do not run 1,000-step ancestral sampling
  unless the user requested realistic sampling.
- `DDPM`, `DDIM`, `PNDM`, and `DPM-Solver` entries differ mainly in the reverse
  update, not in the need for a trained noise predictor.
- U-Net helper files are shared in several diffusion directories; check which
  implementation version the catalog entry names before copying shapes.

### Stable Diffusion and DreamBooth

- Treat these as weight-bound workflows. The minimal Stable Diffusion entry
  expects a local safetensors checkpoint and a CLIP tokenizer; DreamBooth uses
  Diffusers/Transformers and paired instance/class images.
- Do not let a quick diagnostic download model weights implicitly. Ask for the
  weight path or cache policy first.
- Validate prompt tokenization, latent shape, and checkpoint key compatibility
  before running a full 512x512 sampling loop.

## Dependency posture

The generative entries span old and new stacks: `torch==1.7.1` through
`torch==2.7.0`, `keras==2.4.3` through `keras==3.10.0`, multiple Torchvision
versions, and optional `diffusers`, `transformers`, `safetensors`, `UMNN`, and
`scipy`. Use one environment per paper or per compatible subset.

Do not install every generative requirements file into one environment. The
catalog captures which requirements belong to each entry.

## Validation signals

- Model constructors return modules without allocating huge tensors.
- A tiny forward pass returns the expected image, latent, or log-prob shape.
- Loss values are finite after one small update.
- Sampling writes to a scratch output directory only after the user approves
  side effects.
- Missing weights/datasets are reported as prerequisites, not worked around by
  silent downloads.
