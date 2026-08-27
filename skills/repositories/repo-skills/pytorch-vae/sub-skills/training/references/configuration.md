# Configuration

## Purpose

Use this when you need to edit or validate a training YAML file.

## Canonical schema

| Section | Required keys | Meaning |
| --- | --- | --- |
| `model_params` | `name`, plus the model-specific kwargs | Selects the class from `models.vae_models`. |
| `data_params` | `data_path`, `train_batch_size`, `val_batch_size`, `patch_size`, `num_workers` | Feeds `VAEDataset`. |
| `exp_params` | `LR`, `weight_decay`, `scheduler_gamma`, `kld_weight`, `manual_seed` | Experiment hyperparameters and seed. |
| `trainer_params` | `gpus`, `max_epochs` | Lightning trainer arguments. |
| `logging_params` | `save_dir`, `name` | TensorBoard and checkpoint naming. |

## Common model-specific keys

| Model | Extra keys |
| --- | --- |
| `BetaVAE` | `beta`, `gamma`, `max_capacity`, `Capacity_max_iter`, `loss_type` |
| `BetaTCVAE` | `anneal_steps`, `alpha`, `beta`, `gamma` |
| `ConditionalVAE` | `num_classes`, `img_size` |
| `DFCVAE` | `alpha`, `beta` |
| `DIPVAE` | `lambda_diag`, `lambda_offdiag` |
| `FactorVAE` | `gamma`, plus `exp_params.submodel`, `exp_params.LR_2`, `exp_params.scheduler_gamma_2` |
| `GammaVAE` | `gamma_shape`, `prior_shape`, `prior_rate` |
| `HVAE` | `latent1_dim`, `latent2_dim` |
| `InfoVAE` | `reg_weight`, `kernel_type`, `alpha`, `beta` |
| `IWAE` / `MIWAE` | `num_samples`, and for MIWAE also `num_estimates` |
| `JointVAE` | discrete/continuous capacity and annealing fields |
| `LVAE` | `latent_dims`, `hidden_dims` |
| `MSSIMVAE` | `window_size`, `size_average` |
| `SWAE` | `reg_weight`, `wasserstein_deg`, `num_projections`, `projection_dist` |
| `VampVAE` | `num_components` in the model, plus legacy experiment fields in the old config |
| `VQVAE` | `embedding_dim`, `num_embeddings`, `beta` |

## Legacy layout to know about

`configs/vampvae.yaml` does not follow the same `data_params` / `trainer_params.gpus` shape as the generic runner configs.
The bundled training wrapper recognizes the old `exp_params.data_path`, `exp_params.batch_size`, and `trainer_params.max_nb_epochs` fields and normalizes them.
The newer configs often use a one-element GPU list such as `[1]`, while the legacy VampVAE config uses a scalar `gpus: 1`; the bundled helper accepts both forms.

## Safe validation rule

Before a full fit, run the bundled training wrapper without `--fit` so the config, model registry, and data path are checked without starting a long run.
