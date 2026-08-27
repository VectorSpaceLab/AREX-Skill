# API Reference

This reference captures the representative class signatures and the shape contracts that matter most when wiring a policy, backbone, or checkpoint.

## Core policy interfaces

### `BaseLowdimPolicy`
Signature: `()`

Methods:
- `predict_action(self, obs_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]`
- `set_normalizer(self, normalizer: LinearNormalizer)`
- `reset(self)`

Contract:
- Input observation dict uses the `obs` key.
- The policy returns an action dict, usually with `action` and often `action_pred`.
- `set_normalizer()` must be called before inference or training-side sampling.

### `BaseImagePolicy`
Signature: `()`

Methods:
- `predict_action(self, obs_dict: Dict[str, torch.Tensor]) -> Dict[str, torch.Tensor]`
- `set_normalizer(self, normalizer: LinearNormalizer)`
- `reset(self)`

Contract:
- Input observation dict keys must match the policy's `shape_meta`.
- Image policies often encode multiple keys and then predict an action sequence.

### `LinearNormalizer`
Representative methods:
- `fit(self, data, last_n_dims=1, dtype=torch.float32, mode='limits', output_max=1., output_min=-1., range_eps=1e-4, fit_offset=True)`
- `normalize(self, x)`
- `unnormalize(self, x)`
- `get_input_stats(self)`
- `get_output_stats(self)`

### `SingleFieldLinearNormalizer`
Representative methods:
- `fit(self, data, last_n_dims=1, dtype=torch.float32, mode='limits', output_max=1., output_min=-1., range_eps=1e-4, fit_offset=True)`
- `create_fit(cls, data, **kwargs)`
- `create_manual(cls, scale, offset, input_stats_dict)`
- `create_identity(cls, dtype=torch.float32)`
- `normalize(self, x)`
- `unnormalize(self, x)`
- `get_input_stats(self)`
- `get_output_stats(self)`

## Diffusion backbones

### `ConditionalUnet1D`
Signature: `(input_dim, local_cond_dim=None, global_cond_dim=None, diffusion_step_embed_dim=256, down_dims=[256, 512, 1024], kernel_size=3, n_groups=8, cond_predict_scale=False)`

Methods of interest:
- `forward(self, sample: torch.Tensor, timestep: Union[torch.Tensor, float, int], local_cond=None, global_cond=None, **kwargs)`

Contract:
- `sample` is shaped `(B, T, D)` on entry.
- The model returns the same shape.
- `local_cond` is shaped `(B, T, local_cond_dim)` when used.
- `global_cond` is shaped `(B, global_cond_dim)` when used.
- `cond_predict_scale=True` uses scale-and-bias FiLM-style conditioning in residual blocks.

### `TransformerForDiffusion`
Signature: `(input_dim: int, output_dim: int, horizon: int, n_obs_steps: int = None, cond_dim: int = 0, n_layer: int = 12, n_head: int = 12, n_emb: int = 768, p_drop_emb: float = 0.1, p_drop_attn: float = 0.1, causal_attn: bool = False, time_as_cond: bool = True, obs_as_cond: bool = False, n_cond_layers: int = 0) -> None`

Methods of interest:
- `get_optim_groups(self, weight_decay: float=1e-3)`
- `configure_optimizers(self, learning_rate: float=1e-4, weight_decay: float=1e-3, betas: Tuple[float, float]=(0.9, 0.95))`
- `forward(self, sample: torch.Tensor, timestep: Union[torch.Tensor, float, int], cond: Optional[torch.Tensor]=None, **kwargs)`

Contract:
- `sample` is shaped `(B, T, input_dim)`.
- `cond` is shaped `(B, T', cond_dim)` when `obs_as_cond=True`.
- `time_as_cond=False` switches to an encoder-only style path with a time token.
- `obs_as_cond=True` requires `time_as_cond=True` and `cond_dim > 0`.
- `causal_attn=True` enables a causal mask on the main sequence.

## Policy family signatures

| Class | Signature | Main return shape or behavior |
|---|---|---|
| `DiffusionUnetLowdimPolicy` | `(model: ConditionalUnet1D, noise_scheduler: DDPMScheduler, horizon, obs_dim, action_dim, n_action_steps, n_obs_steps, num_inference_steps=None, obs_as_local_cond=False, obs_as_global_cond=False, pred_action_steps_only=False, oa_step_convention=False, **kwargs)` | `predict_action()` returns `action` and `action_pred`; may also return `obs_pred` and `action_obs_pred` when not conditioning purely through local/global paths. `compute_loss()` uses the scheduler's `prediction_type`. |
| `DiffusionTransformerLowdimPolicy` | `(model: TransformerForDiffusion, noise_scheduler: DDPMScheduler, horizon, obs_dim, action_dim, n_action_steps, n_obs_steps, num_inference_steps=None, obs_as_cond=False, pred_action_steps_only=False, **kwargs)` | Same action-sequence contract as the low-dim UNet policy, but with a transformer backbone. |
| `DiffusionUnetImagePolicy` | `(shape_meta: dict, noise_scheduler: DDPMScheduler, obs_encoder: MultiImageObsEncoder, horizon, n_action_steps, n_obs_steps, num_inference_steps=None, obs_as_global_cond=True, diffusion_step_embed_dim=256, down_dims=(256, 512, 1024), kernel_size=5, n_groups=8, cond_predict_scale=True, **kwargs)` | Uses encoded image observations and returns `action` plus `action_pred`. |
| `DiffusionUnetHybridImagePolicy` | `(shape_meta: dict, noise_scheduler: DDPMScheduler, horizon, n_action_steps, n_obs_steps, num_inference_steps=None, obs_as_global_cond=True, crop_shape=(76, 76), diffusion_step_embed_dim=256, down_dims=(256, 512, 1024), kernel_size=5, n_groups=8, cond_predict_scale=True, obs_encoder_group_norm=False, eval_fixed_crop=False, **kwargs)` | Robomimic-style image encoder plus low-dim handling; returns `action` and `action_pred`. |
| `DiffusionTransformerHybridImagePolicy` | `(shape_meta: dict, noise_scheduler: DDPMScheduler, horizon, n_action_steps, n_obs_steps, num_inference_steps=None, crop_shape=(76, 76), obs_encoder_group_norm=False, eval_fixed_crop=False, n_layer=8, n_cond_layers=0, n_head=4, n_emb=256, p_drop_emb=0.0, p_drop_attn=0.3, causal_attn=True, time_as_cond=True, obs_as_cond=True, pred_action_steps_only=False, **kwargs)` | Robomimic-style image encoder plus transformer diffusion backbone; returns `action` and `action_pred`. |
| `RobomimicLowdimPolicy` | `(action_dim, obs_dim, algo_name='bc_rnn', obs_type='low_dim', task_name='square', dataset_type='ph')` | One-step `action` output shaped `(B, 1, Da)`; training uses `train_on_batch()`. |
| `RobomimicImagePolicy` | `(shape_meta: dict, algo_name='bc_rnn', obs_type='image', task_name='square', dataset_type='ph', crop_shape=(76, 76))` | One-step `action` output shaped `(B, 1, Da)`; training uses `train_on_batch()` and `on_epoch_end()`. |
| `BETLowdimPolicy` | `(action_ae: KMeansDiscretizer, obs_encoding_net: nn.Module, state_prior: MinGPT, horizon, n_action_steps, n_obs_steps)` | `compute_loss()` returns `(loss, loss_components)`; `fit_action_ae()` must be called before training. |
| `IbcDfoLowdimPolicy` | `(horizon, obs_dim, action_dim, n_action_steps, n_obs_steps, dropout=0.1, train_n_neg=128, pred_n_iter=5, pred_n_samples=16384, kevin_inference=False, andy_train=False)` | Candidate scoring over sampled actions; `predict_action()` returns a selected action sequence. |
| `IbcDfoHybridImagePolicy` | `(shape_meta: dict, horizon, n_action_steps, n_obs_steps, dropout=0.1, train_n_neg=128, pred_n_iter=5, pred_n_samples=16384, kevin_inference=False, andy_train=False, obs_encoder_group_norm=True, eval_fixed_crop=True, crop_shape=(76, 76))` | Candidate scoring over sampled actions with image features. |

## Representative config targets

| Config file | Policy target | Backbone or encoder target |
|---|---|---|
| `train_diffusion_unet_lowdim_workspace.yaml` | `diffusion_policy.policy.diffusion_unet_lowdim_policy.DiffusionUnetLowdimPolicy` | `diffusion_policy.model.diffusion.conditional_unet1d.ConditionalUnet1D` |
| `train_diffusion_transformer_lowdim_workspace.yaml` | `diffusion_policy.policy.diffusion_transformer_lowdim_policy.DiffusionTransformerLowdimPolicy` | `diffusion_policy.model.diffusion.transformer_for_diffusion.TransformerForDiffusion` |
| `train_diffusion_unet_image_workspace.yaml` | `diffusion_policy.policy.diffusion_unet_image_policy.DiffusionUnetImagePolicy` | `diffusion_policy.model.vision.multi_image_obs_encoder.MultiImageObsEncoder` + `ConditionalUnet1D` |
| `train_diffusion_unet_hybrid_workspace.yaml` | `diffusion_policy.policy.diffusion_unet_hybrid_image_policy.DiffusionUnetHybridImagePolicy` | Robomimic encoder + `ConditionalUnet1D` |
| `train_diffusion_transformer_hybrid_workspace.yaml` | `diffusion_policy.policy.diffusion_transformer_hybrid_image_policy.DiffusionTransformerHybridImagePolicy` | Robomimic encoder + `TransformerForDiffusion` |
| `train_bet_lowdim_workspace.yaml` | `diffusion_policy.policy.bet_lowdim_policy.BETLowdimPolicy` | `KMeansDiscretizer` + `MinGPT` |
| `train_ibc_dfo_lowdim_workspace.yaml` | `diffusion_policy.policy.ibc_dfo_lowdim_policy.IbcDfoLowdimPolicy` | Candidate scorer MLP |
| `train_robomimic_lowdim_workspace.yaml` | `diffusion_policy.policy.robomimic_lowdim_policy.RobomimicLowdimPolicy` | Robomimic BC-RNN policy |
| `train_robomimic_image_workspace.yaml` | `diffusion_policy.policy.robomimic_image_policy.RobomimicImagePolicy` | Robomimic BC-RNN policy + image encoder |

## Validation moves
- Print signatures with `scripts/inspect_policy_interfaces.py`.
- Compare the printed constructor to the intended `policy._target_` in your workspace config.
- Check that the chosen family's `predict_action()` return shape matches the downstream runner or metric.
- Confirm that the scheduler, encoder, and policy live on the same device before real inference.
