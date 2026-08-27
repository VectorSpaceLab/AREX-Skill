# API Reference

This reference summarizes the ControlNet 1.0 model and checkpoint APIs that future agents most often need for architecture inspection, safe checkpoint loading, and sampling integration.

## Checkpoint Helpers

| API | Verified signature | Responsibility | Notes |
| --- | --- | --- | --- |
| `cldm.model.get_state_dict` | `get_state_dict(d)` | Return `d["state_dict"]` when present, otherwise return `d`. | Used twice by `load_state_dict`, so nested checkpoint containers are normalized to the state dictionary expected by model loading. |
| `cldm.model.load_state_dict` | `load_state_dict(ckpt_path, location="cpu")` | Load a checkpoint state dict from `.ckpt`, `.pth`, or `.safetensors`. | `.safetensors` imports `safetensors.torch.load_file(ckpt_path, device=location)`; other extensions use `torch.load(ckpt_path, map_location=torch.device(location))`, then normalize through `get_state_dict`. |
| `cldm.model.create_model` | `create_model(config_path)` | Load an OmegaConf YAML config, instantiate `config.model`, move it to CPU, and return the model. | The config must expose a `model` node with a valid `target` import path and `params`. It does not load a checkpoint by itself. |

Safe inspection pattern:

```python
from cldm.model import create_model, load_state_dict

model = create_model("models/cldm_v15.yaml")
state_dict = load_state_dict("models/control_sd15_ini.ckpt", location="cpu")
missing, unexpected = model.load_state_dict(state_dict, strict=False)
```

Use `location="cpu"` for diagnostics unless the user explicitly needs GPU loading and the environment has CUDA available.

## Architecture Classes

| Class or method | Verified signature | Responsibility | Key behavior |
| --- | --- | --- | --- |
| `cldm.cldm.ControlNet.__init__` | `(self, image_size, in_channels, model_channels, hint_channels, num_res_blocks, attention_resolutions, dropout=0, channel_mult=(1, 2, 4, 8), conv_resample=True, dims=2, use_checkpoint=False, use_fp16=False, num_heads=-1, num_head_channels=-1, num_heads_upsample=-1, use_scale_shift_norm=False, resblock_updown=False, use_new_attention_order=False, use_spatial_transformer=False, transformer_depth=1, context_dim=None, n_embed=None, legacy=True, disable_self_attentions=None, num_attention_blocks=None, disable_middle_self_attn=False, use_linear_in_transformer=False)` | Build the trainable ControlNet branch, including the hint encoder, copied SD-like input/middle blocks, and zero-convolution outputs. | Requires `context_dim` when `use_spatial_transformer=True`. Requires either `num_heads` or `num_head_channels`. Produces control tensors consumed by `ControlledUnetModel`. |
| `cldm.cldm.ControlNet.forward` | `(self, x, hint, timesteps, context, **kwargs)` | Encode the hint image/control map, run the control branch, and return a list of zero-conv control outputs. | The first block receives the guided hint once. Every input block and middle block contributes one control output. |
| `cldm.cldm.ControlledUnetModel.forward` | `(self, x, timesteps=None, context=None, control=None, only_mid_control=False, **kwargs)` | Run the locked diffusion UNet and inject control tensors into decoder skip connections. | Input/middle computation runs under `torch.no_grad()`. If `only_mid_control` is true, only the middle control is added; otherwise output-block skip features receive control tensors too. |
| `cldm.cldm.ControlLDM.__init__` | `(self, control_stage_config, control_key, only_mid_control, *args, **kwargs)` | Wrap Stable Diffusion latent diffusion with a ControlNet stage. | Instantiates `control_model`, stores `control_key`, initializes `control_scales` as 13 values, and records `only_mid_control`. |
| `cldm.cldm.ControlLDM.get_input` | `(self, batch, k, bs=None, *args, **kwargs)` | Prepare latent input plus conditioning dict from batch data. | Reads the control map from `batch[control_key]`, rearranges `b h w c` to `b c h w`, and returns `dict(c_crossattn=[c], c_concat=[control])`. |
| `cldm.cldm.ControlLDM.apply_model` | `(self, x_noisy, t, cond, *args, **kwargs)` | Apply text conditioning and optional ControlNet conditioning during denoising. | Requires `cond` as a dict. If `c_concat` is absent, calls the diffusion model without control. Otherwise computes control tensors, applies `control_scales`, and injects them into the controlled UNet. |
| `cldm.cldm.ControlLDM.log_images` | `(self, batch, N=4, n_row=2, sample=False, ddim_steps=50, ddim_eta=0.0, return_keys=None, quantize_denoised=True, inpaint=True, plot_denoise_rows=False, plot_progressive_rows=True, plot_diffusion_rows=False, unconditional_guidance_scale=9.0, unconditional_guidance_label=None, use_ema_scope=True, **kwargs)` | Produce reconstruction, control, conditioning, and optional sample images for logging/training diagnostics. | Uses `DDIMSampler` through `sample_log` when sampling is requested. Route full app/image generation usage to the Gradio sub-skill. |
| `cldm.cldm.ControlLDM.low_vram_shift` | `(self, is_diffusing)` | Move heavy submodules between CPU and CUDA around diffusion steps. | When diffusing, the diffusion/control models move to CUDA and first/condition stages move to CPU; otherwise the reverse. Requires CUDA to be available. |

## DDIM Sampler

| API | Verified signature | Responsibility | Notes |
| --- | --- | --- | --- |
| `cldm.ddim_hacked.DDIMSampler.__init__` | `(self, model, schedule="linear", **kwargs)` | Store the diffusion model and DDPM schedule metadata. | The hacked sampler is used by Gradio apps and `ControlLDM.sample_log`. |
| `cldm.ddim_hacked.DDIMSampler.sample` | `(self, S, batch_size, shape, conditioning=None, callback=None, normals_sequence=None, img_callback=None, quantize_x0=False, eta=0.0, mask=None, x0=None, temperature=1.0, noise_dropout=0.0, score_corrector=None, corrector_kwargs=None, verbose=True, x_T=None, log_every_t=100, unconditional_guidance_scale=1.0, unconditional_conditioning=None, dynamic_threshold=None, ucg_schedule=None, **kwargs)` | Create the DDIM schedule, allocate latent noise, and run denoising. | `shape` is `(C, H, W)`, and the actual latent batch shape is `(batch_size, C, H, W)`. It warns when conditioning batch size differs from `batch_size`. |

## Optional Attention Hooks

- `share.py` always calls `disable_verbosity()` to reduce transformers logging.
- If `config.save_memory` is true, `share.py` calls `enable_sliced_attention()`, which monkey-patches `ldm.modules.attention.CrossAttention.forward` with a sliced attention implementation.
- The repository also contains optional xformers attention paths in latent-diffusion modules. Importing without xformers can print `No module 'xformers'. Proceeding without it.`; that warning is usually non-fatal unless the selected config or custom patch requires xformers-specific attention.
