# Model Overview

## Purpose

Read this when you need a quick map from a user request to the relevant MMGeneration model family, config folder, and likely workflow.

## Family map

| Family | Representative configs | Typical task | Notes |
| --- | --- | --- | --- |
| Unconditional GANs | `configs/dcgan/`, `configs/lsgan/`, `configs/wgan-gp/`, `configs/pggan/`, `configs/styleganv1/`, `configs/styleganv2/`, `configs/styleganv3/`, `configs/ada/`, `configs/positional_encoding_in_gans/` | Sample new images or train from a dataset root | These are the main GAN sampling and training routes. StyleGAN-family configs also power interpolation, projection, and editing applications. |
| Conditional GANs | `configs/sngan_proj/`, `configs/sagan/`, `configs/biggan/` | Class-conditional synthesis | Use `sample_conditional_model` or a conditional demo helper. |
| Image translation | `configs/pix2pix/`, `configs/cyclegan/` | Paired or unpaired image-to-image translation | Input data layout matters; the paired vs unpaired dataset classes differ. |
| Internal learning | `configs/singan/`, `configs/positional_encoding_in_gans/` | Single-image synthesis or scale-aware generation | Requires SinGAN-style dataset handling. |
| Diffusion | `configs/improved_ddpm/` | Denoising diffusion sampling and training | Use `sample_ddpm_model` and DDPM-specific config fields. |

## Public model classes that anchor the repo

- `StaticUnconditionalGAN`
- `ProgressiveGrowingGAN`
- `BasicConditionalGAN`
- `SinGAN`
- `MSPIEStyleGAN2`
- `StaticTranslationGAN`
- `Pix2Pix`
- `CycleGAN`
- `BasicGaussianDiffusion`

See `api-reference.md` for verified constructor signatures.

## How to choose a family

- If the user wants a pretrained image sample, start with the matching unconditional or conditional family and a demo/sampling path.
- If the user wants to edit a specific image or latent space, start with StyleGAN-family configs and the applications sub-skill.
- If the user wants paired or unpaired image translation, route to Pix2Pix or CycleGAN and the paired/unpaired dataset formats.
- If the user wants a single-image generative process, route to SinGAN.
- If the user wants diffusion sampling, route to `improved_ddpm`.

## Associated config and docs evidence

- `README.md` model zoo section
- `docs/en/get_started.md`
- `docs/en/quick_run.md`
- `docs/en/tutorials/applications.md`
- `docs/en/tutorials/config.md`
- `configs/*/README.md` and `configs/*/metafile.yml`
