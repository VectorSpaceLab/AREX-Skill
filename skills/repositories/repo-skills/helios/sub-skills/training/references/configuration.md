# Training configuration reference

Helios training YAMLs merge into a structured `Args` object with these groups:

- `output_dir`
- `seed`
- `report_to`
- `data_config`
- `model_config`
- `validation_config`
- `training_config`
- `logging_dir`

## High-value config invariants

| Rule | Why it matters |
| --- | --- |
| `data_config.use_stage1_dataset` and `training_config.offload` cannot both be true | Stage-1 dataset loading already offloads VAE/text work differently |
| `data_config.single_res` requires `data_config.force_rebuild` | The loader must rebuild cache metadata for the selected resolution |
| `model_config.lora_layers` requires an empty `lora_target_modules` list | The code treats these as mutually exclusive target-selection modes |
| `training_config.restrict_lora` requires `restrict_self_attn` | Restricted LoRA is only valid with restricted self-attention |
| `training_config.is_train_restrict_lora` requires `restrict_lora` | The training flag assumes the restricted LoRA modules exist |
| `validation_config.use_kv_cache` requires `restrict_self_attn` | The KV-cache path is tied to restricted self-attention |
| `validation_config.validation_latent_window_size` and `validation_config.validation_stream_chunk_size` must each be single-item lists | The validator only accepts one value for each validation axis |
| `training_config.use_ema_validation` requires `use_ema` | Validation cannot use EMA state that is not created |
| `training_config.efficient_sample` requires `pyramid_sample_mode: full` | Efficient sampling assumes the full pyramid sample mode |
| Multi-term memory patch/zero-history options require `has_multi_term_memory_patch` and `is_enable_stage1` | Clean patch embedding only works in the stage-1-enabled path |
| Full and LoRA variants of the same patch-training mode cannot both be enabled | The train script treats them as mutually exclusive parameterizations |
| `use_error_recycling` cannot combine with `corrupt_history` or `corrupt_model_input` | These augmentation paths conflict |
| `is_multi_pyramid_stage_backward_simulated` requires `is_enable_stage2` | Multi-stage simulated backward only exists in the stage-2 path |
| `is_use_reward_model` requires a positive reward weight | A reward model with zero VQ/MQ weights is invalid |
| `is_use_gan` requires DMD plus GAN hooks or GAN final mode | GAN training is a DMD variant and needs one discriminator hook path |
| `stage_cold_start_step` must be `<= cold_start_step` | Stage cold start cannot begin after the global cold-start boundary |
| Decoupled DMD CA start/end steps must be `>= generator_dynamic_step` | Decoupled cross-attention gating starts after the generator dynamic phase |
| Stage-3 datasets require at least one GAN, ODE, or text data root | Empty stage-3 data roots lead to invalid dataset construction |

## Stage-specific notes

- Stage 1 data normally uses prepared feature/latent folders, not raw videos.
- Stage 2 adds pyramid settings such as `stage2_num_stages`,
  `stage2_sample_ratios`, `stage2_stage_range`, and `stage2_timestep_shift`.
- Stage 3 introduces DMD, ODE, GAN, self-forcing, reward-model, and
  low-VRAM-specific toggles.
- The correction config family records train/inference consistency and
  anti-drifting adjustments.

## Useful helpers

- `scripts/validate_train_config.py` checks the common invariants above.
- `scripts/compare_configs.py` compares two YAML files and reports missing keys
  or differing values.
