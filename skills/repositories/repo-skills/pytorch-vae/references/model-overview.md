# Model Overview

## Purpose

Use this file when you need a quick map from user intent to one of the available VAE variants.

## Shared shape

Most models in this repo use 64x64 RGB images, convolutional encoder/decoder blocks, and a `loss_function(*results, M_N=...)` pattern.
The shared registry lives in `models.vae_models` and exposes the names used by the configs.

## Model families

| Family | Models | Notes |
| --- | --- | --- |
| Baseline / regularized VAEs | `VanillaVAE`, `BetaVAE`, `FactorVAE`, `BetaTCVAE`, `DIPVAE`, `InfoVAE`, `WAE_MMD`, `SWAE`, `LogCoshVAE`, `GammaVAE`, `MSSIMVAE` | Mostly standard conv VAEs with different reconstruction or latent regularizers. |
| Conditional / discrete latent variants | `ConditionalVAE`, `CategoricalVAE`, `JointVAE`, `VQVAE` | Expect label or categorical-specific inputs, or vector quantization. |
| Multi-sample / hierarchical models | `IWAE`, `MIWAE`, `HVAE`, `LVAE`, `VampVAE` | Use multiple latent levels, pseudo-inputs, or importance-weighted objectives. |
| Perceptual / feature-aware models | `DFCVAE` | Uses a frozen VGG19-BN feature network and may download pretrained weights. |

## Config map

| Config | Model | Distinguishing kwargs |
| --- | --- | --- |
| `configs/vae.yaml` | `VanillaVAE` | `latent_dim` only. |
| `configs/bbvae.yaml`, `configs/bhvae.yaml` | `BetaVAE` | `loss_type`, `beta` or `gamma`, `max_capacity`, `Capacity_max_iter`. |
| `configs/wae_mmd_imq.yaml`, `configs/wae_mmd_rbf.yaml` | `WAE_MMD` | `reg_weight`, `kernel_type`, `latent_var`. |
| `configs/cvae.yaml` | `ConditionalVAE` | `num_classes`, `latent_dim`, label-aware forward/sample. |
| `configs/hvae.yaml` | `HVAE` | `latent1_dim`, `latent2_dim`, `pseudo_input_size`. |
| `configs/lvae.yaml` | `LVAE` | `latent_dims`, `hidden_dims`. |
| `configs/vampvae.yaml` | `VampVAE` | Legacy layout; see training troubleshooting. |
| `configs/iwae.yaml` | `IWAE` | `num_samples`. |
| `configs/dfc_vae.yaml` | `DFCVAE` | `alpha`, `beta`, perceptual features. |
| `configs/mssim_vae.yaml` | `MSSIMVAE` | `window_size`, `size_average`. |
| `configs/factorvae.yaml` | `FactorVAE` | `gamma` plus dual-optimizer trainer settings. |
| `configs/betatc_vae.yaml` | `BetaTCVAE` | `anneal_steps`, `alpha`, `beta`, `gamma`. |
| `configs/dip_vae.yaml` | `DIPVAE` | `lambda_diag`, `lambda_offdiag`. |
| `configs/infovae.yaml` | `InfoVAE` | `reg_weight`, `kernel_type`, `alpha`, `beta`. |
| `configs/logcosh_vae.yaml` | `LogCoshVAE` | `alpha`, `beta`. |
| `configs/swae.yaml` | `SWAE` | `reg_weight`, `num_projections`, `projection_dist`, `wasserstein_deg`. |
| `configs/miwae.yaml` | `MIWAE` | `num_samples`, `num_estimates`. |
| `configs/vq_vae.yaml` | `VQVAE` | `embedding_dim`, `num_embeddings`, `beta`. |
| `configs/gammavae.yaml` | `GammaVAE` | `gamma_shape`, `prior_shape`, `prior_rate`. |
| `configs/cat_vae.yaml` | `CategoricalVAE` | `categorical_dim`, `temperature`, annealing settings. |
| `configs/joint_vae.yaml` | `JointVAE` | Mixed discrete/continuous capacities and annealing. |

## Routing hint

- If you need a full experiment, use the training sub-skill.
- If you need exact signatures or sample/generate caveats, use the model-reference sub-skill.
- If you only need to choose among a few variants, this file is often enough to narrow the route before opening deeper references.
