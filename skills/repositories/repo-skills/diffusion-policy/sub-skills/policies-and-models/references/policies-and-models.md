# Policies and Models

This reference helps future agents choose a policy family, verify its input/output contract, and decide which constructor knobs matter before they touch a workspace or checkpoint.

## What this sub-skill owns
- Policy family selection by observation structure and training style
- `predict_action` shape expectations for low-dim and image policies
- Diffusion backbone choices: UNet vs Transformer
- Normalization and checkpoint-loading expectations
- Optional dependency boundaries for Robomimic, torchvision, diffusers, and related image encoders

## Family selection guide

| Family | Choose it when | Core inputs | Key knobs | Representative config targets |
|---|---|---|---|---|
| Low-dim diffusion | Observations are vector features and you want diffusion sampling | `obs` tensors shaped `(B, To, Do)` and action tensors shaped `(B, T, Da)` | `obs_as_local_cond`, `obs_as_global_cond`, `pred_action_steps_only`, `oa_step_convention`, `num_inference_steps` | `train_diffusion_unet_lowdim_workspace.yaml`, `train_diffusion_transformer_lowdim_workspace.yaml`, `train_diffusion_unet_ddim_lowdim_workspace.yaml`, `train_diffusion_transformer_lowdim_pusht_workspace.yaml`, `train_diffusion_transformer_lowdim_kitchen_workspace.yaml` |
| Image diffusion | RGB observations are the main input and you want a lightweight vision encoder | `shape_meta` with RGB keys plus optional low-dim keys | `obs_as_global_cond`, `crop_shape`, `resize_shape`, `random_crop`, `use_group_norm`, `share_rgb_model`, `imagenet_norm` | `train_diffusion_unet_image_workspace.yaml`, `train_diffusion_unet_image_pretrained_workspace.yaml`, `train_diffusion_unet_real_image_workspace.yaml` |
| Hybrid diffusion | You want mixed image + low-dim inputs with Robomimic-style vision backbones | `shape_meta` plus Robomimic observation modalities | `obs_as_global_cond` or `obs_as_cond`, `obs_encoder_group_norm`, `eval_fixed_crop`, `crop_shape` | `train_diffusion_unet_hybrid_workspace.yaml`, `train_diffusion_transformer_hybrid_workspace.yaml`, `train_diffusion_unet_real_hybrid_workspace.yaml`, `train_diffusion_transformer_real_hybrid_workspace.yaml` |
| Robomimic wrapper | You want the Robomimic BC-RNN baseline or an exact Robomimic-style policy wrapper | `obs` for low-dim or `shape_meta` for image | `algo_name`, `obs_type`, `task_name`, `dataset_type`, `crop_shape` | `train_robomimic_lowdim_workspace.yaml`, `train_robomimic_image_workspace.yaml`, `train_robomimic_real_image_workspace.yaml` |
| BET baseline | You want discrete latent action modeling with a k-means action codebook | `action_ae`, `obs_encoding_net`, `state_prior`, `horizon`, `n_obs_steps`, `n_action_steps` | `train_n_neg`, `pred_n_iter`, `pred_n_samples`, `kevin_inference`, `andy_train` | `train_bet_lowdim_workspace.yaml` |
| IBC/DFO baseline | You want candidate scoring over sampled action sequences instead of diffusion sampling | Vector obs or encoded image obs plus sampled action candidates | `train_n_neg`, `pred_n_iter`, `pred_n_samples`, `kevin_inference`, `andy_train` | `train_ibc_dfo_lowdim_workspace.yaml`, `train_ibc_dfo_hybrid_workspace.yaml`, `train_ibc_dfo_real_hybrid_workspace.yaml` |
| Video diffusion | You need a multi-frame visual encoder plus low-dim aggregation | Image sequence inputs plus low-dim features | `lowdim_as_global_cond`, `channel_mults`, `n_blocks_per_level`, `ta_kernel_size`, `ta_n_groups` | `train_diffusion_unet_video_workspace.yaml` |

## Core selection rules

### 1) Match the observation layout first
- If the batch contains only vector state, use a low-dim policy family.
- If the batch contains RGB keys, use an image or hybrid family.
- If you need a Robomimic-style encoder and crop pipeline, use a hybrid or Robomimic wrapper.
- If you need candidate ranking rather than denoising, use IBC or BET.

### 2) Treat `shape_meta` as the source of truth
- `shape_meta['action']['shape']` should be one-dimensional.
- Low-dim policies expect a single `obs` tensor in the observation dict.
- Image and hybrid policies expect observation keys that match `shape_meta['obs']`.
- Image shapes should already be compatible with the configured encoder layout; do not guess channel order.

### 3) Keep time windows consistent
- `horizon` is the full prediction window.
- `n_obs_steps` is the observed prefix.
- `n_action_steps` is the action slice you want to execute or compare.
- Some configs also define `dataset_obs_steps`; it may be larger than `n_obs_steps` in image or real-data setups.
- If `pred_action_steps_only` is enabled, the policy predicts only the action slice instead of the full horizon.

### 4) Load the normalizer before inference
- Diffusion, BET, IBC, and Robomimic policies all rely on a `LinearNormalizer` or compatible stats object.
- `set_normalizer()` copies the dataset statistics into the policy.
- The normalizer is part of the policy module state and travels with checkpoints.

### 5) Keep evaluation mode consistent
- Diffusion workspaces may maintain both a raw model and an EMA copy.
- When a checkpoint was trained with `training.use_ema: true`, `eval.py` uses the EMA copy.
- Compare EMA-to-EMA or raw-to-raw; do not mix them when checking rollout metrics.

## Model family notes

### Diffusion UNet low-dim
- `DiffusionUnetLowdimPolicy` supports `obs_as_local_cond`, `obs_as_global_cond`, and pure inpainting.
- `ConditionalUnet1D` is the backbone.
- `DDPMScheduler` controls inference timesteps and the `prediction_type` target.
- `oa_step_convention=True` shifts the action slice to start at `n_obs_steps - 1`.

### Diffusion Transformer low-dim
- `DiffusionTransformerLowdimPolicy` wraps `TransformerForDiffusion` plus a `DDPMScheduler`.
- Use this when a transformer backbone is preferred over a UNet.
- `obs_as_cond=True` means the transformer receives observation conditioning tokens.
- `causal_attn=True` enables an autoregressive-style mask; `n_cond_layers>0` uses a transformer encoder for the condition path.

### Image diffusion
- `DiffusionUnetImagePolicy` uses `MultiImageObsEncoder` to turn one or more RGB keys into features.
- The observation encoder can crop, resize, randomize crops, share RGB backbones, or apply ImageNet normalization.
- `obs_as_global_cond=True` is the common path; the alternative is inpainting over action plus encoded observation features.

### Hybrid diffusion
- `DiffusionUnetHybridImagePolicy` and `DiffusionTransformerHybridImagePolicy` translate `shape_meta` into a Robomimic-style observation config.
- `obs_encoder_group_norm=True` replaces BatchNorm with GroupNorm in the image backbone.
- `eval_fixed_crop=True` swaps random cropping for a deterministic evaluation crop.
- These constructors are the right place to inspect if a Robomimic-style visual policy works in your task.

### Robomimic wrappers
- `RobomimicLowdimPolicy` and `RobomimicImagePolicy` are thin adapters around `robomimic.algo.algo_factory`.
- They expose `train_on_batch()` rather than diffusion-style `compute_loss()`.
- Their `predict_action()` returns a one-step action with shape `(B, 1, Da)`.
- Use them when you want a baseline that mirrors the Robomimic training stack.

### BET baseline
- `BETLowdimPolicy` pairs a `KMeansDiscretizer`, an observation encoder, and a `MinGPT` prior.
- Before training, call `fit_action_ae()` so the action codebook exists.
- Its `compute_loss()` returns both the scalar loss and loss components.
- The action decoder reconstructs actions from discrete latent bins and optional offsets.

### IBC/DFO baseline
- `IbcDfoLowdimPolicy` and `IbcDfoHybridImagePolicy` score sampled action candidates with a feedforward network.
- They are useful when you want energy-based candidate ranking instead of diffusion denoising.
- The candidate pool size is driven by `train_n_neg`, `pred_n_iter`, and `pred_n_samples`.

### Video diffusion
- `DiffusionUnetVideoPolicy` exists as a multi-frame image-plus-low-dim variant.
- It depends on extra video encoder helpers beyond the core `model/vision` stack.
- Treat it as optional until its import succeeds in the current runtime.

## Validation checklist
- The family matches the observation structure.
- The constructor signature matches the intended config target.
- The policy can load a normalizer before inference.
- The policy can move to the same device as the batch and scheduler.
- The `predict_action()` return shape matches the metric or environment runner you plan to use.

## Useful internal checks
- Run `scripts/inspect_policy_interfaces.py`.
- Compare the printed signatures with the intended `train_*_workspace.yaml` target.
- If an import fails, decide whether the missing module is optional or whether the selected policy family should change.
