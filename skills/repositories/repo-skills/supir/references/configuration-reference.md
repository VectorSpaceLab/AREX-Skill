# Configuration Reference

This reference distills the SUPIR YAML variants, shared prompt/settings defaults,
and workflow flags. For checkpoint path validation, use
[scripts/check_supir_assets.py](../scripts/check_supir_assets.py).

## Model assembly flow

`create_SUPIR_model(config_path, SUPIR_sign=None, load_default_setting=False)`:

1. Loads an OmegaConf YAML config.
2. Instantiates `config.model.target` (`SUPIR.models.SUPIR_model.SUPIRModel`).
3. Loads `SDXL_CKPT` when set.
4. Loads `SUPIR_CKPT` when set.
5. Loads `SUPIR_CKPT_F` or `SUPIR_CKPT_Q` when `SUPIR_sign` is `F` or `Q`.
6. Returns either the model or `(model, default_setting)` when `load_default_setting=True`.

`SUPIRModel` then calls the SDXL/SGM conditioner, control model, sampler, and
autoencoder components defined in YAML.

## Common YAML sections

| Section | Meaning |
| --- | --- |
| `model.target` | Always the SUPIR model class in the public configs. |
| `model.params.ae_dtype` | Autoencoder dtype; `fp16` is explicitly rejected in `SUPIRModel.__init__` because it can cause NaNs. |
| `model.params.diffusion_dtype` | Diffusion model dtype, usually `fp16`. |
| `model.params.control_stage_config` | GLV control network (`SUPIR.modules.SUPIR_v0.GLVControl`). |
| `model.params.network_config` | LightGLV UNet used for restoration. |
| `model.params.conditioner_config` | Text/time/size conditioning stack, including CLIP/OpenCLIP embedders. |
| `model.params.first_stage_config` | Autoencoder wrapper. |
| `model.params.sampler_config` | Sampler target and sampling defaults. |
| `model.params.p_p` / `n_p` | Default positive and negative prompt suffixes. |
| `default_setting` | UI reset presets for quality/fidelity and EDM step count. |

## Config variants

| Variant | Key difference | Use when |
| --- | --- | --- |
| Default | `RestoreEDMSampler`, SDXL base checkpoint, default `edm_steps: 50` | General batch/API/demo restoration. |
| Tiled | `TiledRestoreEDMSampler`; other major model fields match default | Large images, local prompt mode, or memory-limited VAE operations. |
| Juggernaut Lightning | `RestoreDPMPP2MSampler` and a Juggernaut Lightning checkpoint | Fast photorealistic demo path when matching external checkpoint exists. |

## Important runtime parameters

| Parameter | Source surface | Notes |
| --- | --- | --- |
| `SUPIR_sign` / model select | batch CLI, demo radio | `Q`/`v0-Q` is default quality/general; `F`/`v0-F` favors fidelity for light degradation. |
| `edm_steps` | batch + demos | More steps cost more time; default is 50 in public presets. |
| `s_stage1` | batch + demos | Stage1 restoration control; negative values are treated as disabled/invalid in user-facing docs. |
| `s_stage2` / `control_scale` | `batchify_sample` | Higher values favor fidelity/control; README suggests `1.0` for fidelity and `0.93` for visual quality. |
| `s_cfg` / `cfg_scale` | text guidance | README quality mode raises this to about 6+ while fidelity mode uses about 4. |
| `linear_CFG` / `spt_linear_CFG` | batch + demos | When enabled, CFG linearly changes over the sigma schedule. |
| `color_fix_type` | batch + demos + API | Must be `Wavelet`, `AdaIn`, or `None`; `Wavelet` is the default CLI/demo setting. |
| `ae_dtype` | batch + demos + API | Valid CLI values are `fp32` and `bf16`; internal constructor rejects `fp16` for AE. |
| `diff_dtype` | batch + demos + API | `fp16` is common for diffusion; `fp32` and `bf16` are also accepted. |
| `num_samples` | batch + demos + API | `SUPIRModel.batchify_sample` asserts batch size is one when generating multiple samples. |
| `use_tile_vae` | batch + demos | Installs tiled hooks on VAE encoder/decoder to reduce memory pressure. |
| `load_8bit_llava` | batch + demos | Reduces LLaVA memory, but caption quality and dependency compatibility should be checked. |

## Local prompt and face variants

- Tiled/local prompt mode lets prompt content vary by tile and routes list-style
  prompt inputs through `SUPIRModel.prepare_condition`; the model asserts batch
  size one for local-prompt lists.
- Face mode detects/aligns faces, restores face crops, optionally restores the
  background, and pastes restored faces back through inverse affine transforms.

## Validation guidance

- Confirm config files use checkpoint paths that exist or are intentionally
  `None` for allowed downloads.
- Ensure the selected YAML and launcher mode match: do not use tiled-mode UI
  guidance with the non-tiled YAML unless deliberately comparing memory use.
- Record prompt and seed values when comparing quality/fidelity runs; sampling
  is stochastic when seed is `-1`.
