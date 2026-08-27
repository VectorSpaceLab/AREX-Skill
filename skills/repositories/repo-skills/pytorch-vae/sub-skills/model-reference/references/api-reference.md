# API Reference

## Purpose

Use this file when you need exact constructor kwargs, registry names, or special forward/loss/sample behavior.
The signatures below were verified from the installed checkout in a Python 3.10 CUDA environment.

## Registry and aliases

`models.vae_models` exposes the public model names used by the configs:

`BetaTCVAE`, `BetaVAE`, `CategoricalVAE`, `ConditionalVAE`, `DFCVAE`, `DIPVAE`, `FactorVAE`, `GammaVAE`, `HVAE`, `IWAE`, `InfoVAE`, `JointVAE`, `LVAE`, `LogCoshVAE`, `MIWAE`, `MSSIMVAE`, `SWAE`, `VQVAE`, `VampVAE`, `VanillaVAE`, and `WAE_MMD`.

Aliases also exist for `VAE`/`GaussianVAE` -> `VanillaVAE`, `CVAE` -> `ConditionalVAE`, and `GumbelVAE` -> `CategoricalVAE`.

## Constructor signatures

| Model | Verified constructor shape | Notable notes |
| --- | --- | --- |
| `VanillaVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, **kwargs)` | Baseline conv VAE. |
| `BetaVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, beta: int = 4, gamma: float = 1000.0, max_capacity: int = 25, Capacity_max_iter: int = 1e5, loss_type: str = 'B', **kwargs)` | `loss_type='H'` or `'B'`. |
| `ConditionalVAE` | `(in_channels: int, num_classes: int, latent_dim: int, hidden_dims: List = None, img_size: int = 64, **kwargs)` | Expects label vectors in `forward()` and `sample()`. |
| `WAE_MMD` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, reg_weight: int = 100, kernel_type: str = 'imq', latent_var: float = 2.0, **kwargs)` | `kernel_type` is `imq` or `rbf`. |
| `BetaTCVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, anneal_steps: int = 200, alpha: float = 1.0, beta: float = 6.0, gamma: float = 1.0, **kwargs)` | Loss uses annealing and a TC decomposition. |
| `DIPVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, lambda_diag: float = 10.0, lambda_offdiag: float = 5.0, **kwargs)` | Covariance-penalty VAE. |
| `FactorVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, gamma: float = 40.0, **kwargs)` | Has an internal discriminator and dual-optimizer loss. |
| `GammaVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, gamma_shape: float = 8.0, prior_shape: float = 2.0, prior_rate: float = 1.0, **kwargs)` | Gamma prior variant. |
| `HVAE` | `(in_channels: int, latent1_dim: int, latent2_dim: int, hidden_dims: List = None, img_size: int = 64, pseudo_input_size: int = 128, **kwargs)` | Two latent levels. |
| `IWAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, num_samples: int = 5, **kwargs)` | Importance-weighted objective. |
| `InfoVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, alpha: float = -0.5, beta: float = 5.0, reg_weight: int = 100, kernel_type: str = 'imq', latent_var: float = 2.0, **kwargs)` | MMD-style regularization. |
| `JointVAE` | `(in_channels: int, latent_dim: int, categorical_dim: int, latent_min_capacity: float = 0.0, latent_max_capacity: float = 25.0, latent_gamma: float = 30.0, latent_num_iter: int = 25000, categorical_min_capacity: float = 0.0, categorical_max_capacity: float = 25.0, categorical_gamma: float = 30.0, categorical_num_iter: int = 25000, hidden_dims: List = None, temperature: float = 0.5, anneal_rate: float = 3e-05, anneal_interval: int = 100, alpha: float = 30.0, **kwargs)` | Mixed continuous/discrete latents. |
| `LVAE` | `(in_channels: int, latent_dims: List, hidden_dims: List, **kwargs)` | Hierarchical latent stack. |
| `LogCoshVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, alpha: float = 100.0, beta: float = 10.0, **kwargs)` | Log-cosh reconstruction objective. |
| `MIWAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, num_samples: int = 5, num_estimates: int = 5, **kwargs)` | Multiple importance estimates. |
| `MSSIMVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, window_size: int = 11, size_average: bool = True, **kwargs)` | Uses SSIM-based reconstruction. |
| `SWAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, reg_weight: int = 100, wasserstein_deg: float = 2.0, num_projections: int = 50, projection_dist: str = 'normal', **kwargs)` | Sliced Wasserstein variant. |
| `VQVAE` | `(in_channels: int, embedding_dim: int, num_embeddings: int, hidden_dims: List = None, beta: float = 0.25, img_size: int = 64, **kwargs)` | Vector-quantized latent grid. |
| `VampVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, num_components: int = 50, **kwargs)` | Uses pseudo-inputs for the prior. |
| `CategoricalVAE` | `(in_channels: int, latent_dim: int, categorical_dim: int = 40, hidden_dims: List = None, temperature: float = 0.5, anneal_rate: float = 3e-05, anneal_interval: int = 100, alpha: float = 30.0, **kwargs)` | Gumbel-categorical model. |
| `DFCVAE` | `(in_channels: int, latent_dim: int, hidden_dims: List = None, alpha: float = 1, beta: float = 0.5, **kwargs)` | Uses a frozen VGG19-BN feature extractor. |

## Shared output patterns

- Most models return `[recons, input, ...]` from `forward()` and a metrics dict from `loss_function()`.
- `ConditionalVAE.forward()` and `ConditionalVAE.sample()` need `labels=...`.
- `FactorVAE.loss_function()` also needs `optimizer_idx` and `batch_idx` so the discriminator and VAE branches can be separated.
- `DFCVAE.forward()` returns reconstruction, input, feature lists, and latent stats.
- `VQVAE.sample()` raises a `Warning` because sampling is not implemented.
- `VampVAE.sample()` uses CUDA-specific code and expects a CUDA device index.

## Bridge objects

| Object | Signature | Why it matters |
| --- | --- | --- |
| `VAEXperiment` | `(vae_model: models.base.BaseVAE, params: dict)` | Lightning module wrapper used by the training route. |
| `VAEDataset` | `(data_path: str, train_batch_size: int = 8, val_batch_size: int = 8, patch_size: Union[int, Sequence[int]] = (256, 256), num_workers: int = 0, pin_memory: bool = False, **kwargs)` | Datamodule used by the training route. |
| `MyCelebA` | torchvision `CelebA` subclass | Bypasses integrity checks for the documented CelebA extraction workaround. |
| `OxfordPets` | `(data_path: str, split: str, transform: Callable, **kwargs)` | Alternate dataset adapter kept in source for manual adaptation. |
