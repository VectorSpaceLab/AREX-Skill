# Model overview

## Purpose

Read this when you need to understand which model family the policy-training sub-skill is routing to, how the wrappers relate to the DETR subpackage, and what each checkpoint family contains.

## ACT

- Wrapper: `policy.ACTPolicy`
- Builder: `detr.main.build_ACT_model_and_optimizer`
- Core model: `detr.models.detr_vae.DETRVAE`
- Typical loss terms: `l1`, optional `kl`, optional `vq_discrepancy`
- Output: action chunk and padding prediction (`is_pad_hat`) during training; action chunk only during inference

### Structural notes

- Image backbone is one ResNet18 per camera.
- The decoder uses query embeddings and a transformer.
- The encoder can be disabled with `--no_encoder`.
- `--use_vq` switches to a vector-quantized latent path, and `--vq_class` / `--vq_dim` parameterize that latent space.

## CNNMLP

- Wrapper: `policy.CNNMLPPolicy`
- Core model: `detr.models.detr_vae.CNNMLP`
- Loss: MSE against the target action
- Output: single action vector during inference

### Caveat

The source CNNMLP implementation contains an `action_dim` reference that should be checked before relying on it in new runs. Treat that path as needing a quick import or shape sanity check.

## Diffusion Policy

- Wrapper: `policy.DiffusionPolicy`
- Visual backbone: robomimic ResNet18Conv + SpatialSoftmax per camera
- Noise predictor: `ConditionalUnet1D`
- Scheduler: DDIM in the current repository code path
- EMA is enabled in the current wrapper

### What to remember

- Diffusion policy uses action min/max normalization rather than mean/std normalization.
- `observation_horizon`, `action_horizon`, and `prediction_horizon` are separate quantities in the policy config, even if some examples set them to the same chunk size.
- Inference starts from Gaussian noise and iteratively denoises a horizon-length action sequence.

## Latent model

- Class: `detr.models.latent_model.Latent_Model_Transformer`
- Training script: `train_latent_model.py`
- Purpose: predict the latent VQ codes produced by a trained ACT policy

## Why this matters for routing

If a user asks about training curves, checkpoint contents, policy class selection, or why a rollout looks jerky, this is the reference that tells you which family and loss path they are actually talking about before you send them deeper into the training workflow.
