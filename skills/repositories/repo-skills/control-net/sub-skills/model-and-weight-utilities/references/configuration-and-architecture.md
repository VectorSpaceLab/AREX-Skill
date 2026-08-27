# Configuration and Architecture

ControlNet 1.0 is a source-checkout research/demo codebase. Its configs instantiate Python classes directly and its checkpoint tools expect external Stable Diffusion checkpoints supplied by the user.

## Shared Config Structure

Both `cldm_v15` and `cldm_v21` instantiate `cldm.cldm.ControlLDM` with these important top-level keys:

| Config key | Meaning | Practical effect |
| --- | --- | --- |
| `first_stage_key: "jpg"` | Batch image key consumed by the autoencoder/latent diffusion path. | Training or logging batches need an image tensor under `jpg`. |
| `cond_stage_key: "txt"` | Batch text prompt key consumed by the CLIP/OpenCLIP text encoder. | Text conditioning comes from `txt`. |
| `control_key: "hint"` | Batch control-map key consumed by `ControlLDM.get_input`. | Control maps are expected in image layout `b h w c` and are rearranged to `b c h w`. |
| `image_size: 64`, `channels: 4` | Latent-space sampling shape metadata. | 512-pixel image controls usually map to latent height/width divided by 8. |
| `conditioning_key: crossattn` | Text conditioning mode. | `ControlLDM.apply_model` passes concatenated cross-attention context to the diffusion model. |
| `only_mid_control: False` | Whether to inject control only at the middle block. | When false, ControlNet outputs are injected into decoder skip connections as well. |
| `scale_factor: 0.18215` | Stable Diffusion latent scale. | Must match SD-family expectations. |
| `use_ema: False` | EMA model behavior. | The demo/training configs do not rely on EMA weights for ControlLDM. |

Both configs use:

- `control_stage_config.target: cldm.cldm.ControlNet`
- `unet_config.target: cldm.cldm.ControlledUnetModel`
- `first_stage_config.target: ldm.models.autoencoder.AutoencoderKL`
- `control_stage_config.params.hint_channels: 3`
- `model_channels: 320`, `channel_mult: [1, 2, 4, 4]`, `num_res_blocks: 2`, and attention resolutions `[4, 2, 1]`

## `cldm_v15` vs `cldm_v21`

| Area | `cldm_v15` | `cldm_v21` | Why it matters |
| --- | --- | --- | --- |
| Stable Diffusion family | SD1.x / SD1.5 | SD2.1 base | Pair checkpoints with the matching config and add-control tool. |
| Text encoder target | `ldm.modules.encoders.modules.FrozenCLIPEmbedder` | `ldm.modules.encoders.modules.FrozenOpenCLIPEmbedder` with `freeze: True`, `layer: "penultimate"` | SD2.1 uses OpenCLIP and different text-conditioning width. |
| Cross-attention `context_dim` | `768` | `1024` | A common mismatch symptom is tensor shape errors in cross-attention or text context projection. |
| Attention heads | `num_heads: 8` | `num_head_channels: 64` | SD2.1 config computes heads from channel count/head channels and is marked as a flash-attn-related fix in the source comments. |
| Linear transformer | Not set, defaults false | `use_linear_in_transformer: True` | SD2.1 uses linear projections in transformer blocks. |
| Autoencoder attention comment | No xformers hint | Has commented `attn_type: "vanilla-xformers"` | xformers is optional but may be relevant when users customize SD2.1 memory behavior. |
| Initialization tool | SD1.5 add-control mapping | SD2.1 add-control mapping | The mapping rule is the same, but the scratch model/config and checkpoint family differ. |

If a user has an SD2.1 checkpoint but selected `cldm_v15`, catch the `context_dim`/encoder mismatch early and switch them to the SD2.1 config and tool. The inverse also applies: SD1.5 checkpoints should not be paired with `cldm_v21`.

## ControlNet Architecture Concepts

ControlNet adds a trainable branch to a locked Stable Diffusion backbone:

1. The locked `ControlledUnetModel` preserves the original SD denoising path.
2. The trainable `ControlNet` branch mirrors SD-style encoder/middle blocks and receives the external control hint.
3. The `input_hint_block` transforms the control map into the model-channel space.
4. Zero-convolution modules produce control residuals. Initially these output zeros, so a newly attached ControlNet does not distort the base model before training.
5. During `ControlLDM.apply_model`, the control residual list is scaled by `control_scales` and passed into the controlled UNet.

The README describes this as a "locked" copy and a "trainable" copy. The trainable branch learns the condition; the locked branch preserves the production-ready diffusion model. This is the reason small paired datasets can fine-tune control behavior without immediately destroying the base model.

## Zero Convolution FAQ

A zero convolution is a 1x1 convolution initialized with both weight and bias as zeros. The source FAQ addresses the misconception that zero weights imply zero learning.

For a simple scalar layer `y = w x + b`:

- `dy/dw = x`
- `dy/dx = w`
- `dy/db = 1`

When `w = 0` and `x != 0`, the gradient with respect to `w` and `b` is still non-zero. One gradient step can make `w` non-zero; after that, gradients can propagate through `x` as well. In ControlNet, zero convolutions therefore start as no-op residual connections but can progressively become ordinary learned convolution layers during training.

## Low-VRAM and Attention Hooks

There are two memory-related mechanisms:

| Mechanism | Where it appears | Behavior | Caveat |
| --- | --- | --- | --- |
| `config.save_memory = True` | Source config flag read by `share.py` and Gradio scripts | Enables sliced attention and makes app scripts call `model.low_vram_shift(...)` around diffusion. | Requires CUDA for the shift calls; not all cards are guaranteed to succeed. |
| `ControlLDM.low_vram_shift(is_diffusing)` | Model method | During diffusion, moves diffusion/control models to CUDA and first/condition stages to CPU; outside diffusion, reverses that. | Do not call with CUDA unavailable. |
| xformers attention | Latent-diffusion attention modules and optional config comments | Uses memory-efficient attention when installed and selected. | Missing xformers often prints a warning and proceeds without it. |
| Sliced attention | `cldm.hack.enable_sliced_attention()` | Monkey-patches cross-attention to process attention chunks. | Slower than full attention but can reduce memory pressure. |

For full app operation with `save_memory`, route to [gradio-inference-apps](../../gradio-inference-apps/SKILL.md). For training memory knobs such as batch size, gradient accumulation, `sd_locked`, and `only_mid_control`, route to [training-and-datasets](../../training-and-datasets/SKILL.md).
