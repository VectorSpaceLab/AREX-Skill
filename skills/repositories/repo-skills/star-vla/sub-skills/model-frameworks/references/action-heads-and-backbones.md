# Action heads, backbones, and dimension contracts

Evidence basis: `starVLA/model/modules/vlm/__init__.py`, `starVLA/model/modules/world_model/__init__.py`, action modules under `starVLA/model/modules/action_model/`, and selected framework files under `starVLA/model/framework/{VLM4A,VM4A,WM4A}/`.

## Backbone dispatch

### VLM dispatch

VLM4A frameworks call `get_vlm_model(config)`, which chooses a wrapper from `framework.qwenvl.base_vlm` substrings:

| Backbone signal in `base_vlm` | Wrapper family | Notes |
| --- | --- | --- |
| `Qwen2.5-VL` or `nora` | Qwen2.5-VL | Supports requested `flash_attention_2` only when `torch_npu` or `flash_attn` is importable; otherwise falls back to SDPA. |
| `Qwen3-VL` | Qwen3-VL | Source currently forces SDPA before the flash fallback branch. |
| `Qwen3.5` | Qwen3.5-VL | Qwen-family VLM swap. |
| `gemma-4` or `gemma4` | Gemma 4 | Used by `Gemma4PI` and `Gemma4GR00T`; hidden-size alignment is asserted. |
| `minicpm-v` or `minicpmv` | MiniCPM-V | Used by `MiniCPMPI` and `MiniCPMGR00T`; source expects hidden size 1024. |
| `florence` | Florence-2 | Uses a remote-code-capable causal LM path; inspect before production use. |
| `molmo2` | Molmo2 | Falls back from flash attention to SDPA if needed. |
| `cosmos-reason2` | Cosmos-Reason2 VLM | Architecturally Qwen3-VL-like, used by `CosmosGR00T`. |
| `egovla`, `ego_vla`, or `vila` | EgoVLA/VILA | SigLIP/Qwen-style VILA route. |

If none of these signals match, VLM construction raises `NotImplementedError`.

### World-model dispatch

WM4A frameworks call `get_world_model(config)`, preferring `framework.world_model.base_wm` and falling back to `framework.qwenvl.base_vlm` for backward compatibility:

| Backbone signal | Wrapper | Notes |
| --- | --- | --- |
| `cosmos-predict2` | Cosmos-Predict2 | Video-generation DiT with T5/VAE/Transformer features; docs list 2B, 28 layers, hidden dim 2048. |
| `wan2` or `ti2v` | Wan2.2-TI2V | Diffusers Wan route; docs list 5B, 30 layers, hidden dim 3072. |
| `cosmos-reason2` | Cosmos-Reason2 | VLM-like fallback through the CosmosReason2 interface. |

### VM4A backbone path

`ACT` and `DiffusionPolicy` do not use VLM/world-model dispatch. Both consume camera views and proprioceptive state directly through ResNet-18 visual encoders by default. ACT wraps LeRobot `ACTPolicy`; DiffusionPolicy wraps a vendored non-hybrid image-policy subset and DDPM scheduler.

## Action-head families

| Action head | Used by | Core contract | Compatibility notes |
| --- | --- | --- | --- |
| MLP/L1 regression (`MLP_ActionHeader`) | `QwenOFT`, `CosmoPredict2OFT`, `WanOFT` | Takes per-action query hidden states and predicts `[B, action_horizon, action_dim]`; training uses L1 loss. | `action_hidden_dim` is often overwritten from the loaded backbone hidden size. Simple and fast, but less expressive than flow/diffusion heads. |
| FAST action tokenizer (`fast_ActionHeader`) | `QwenFast` | Encodes continuous action chunks into FAST pseudo-language tokens and decodes generated tokens back to actions. | Requires the FAST processor/tokenizer and an action-token-capable VLM. Tokenizer loading may require local cache or explicit download approval. |
| GR00T flow matching (`GR00T_ActionHeader`) | `QwenGR00T`, `CosmosGR00T`, `MiniCPMGR00T`, `Gemma4GR00T`, and related variants | DiT-B/L flow-matching head conditioned on VLM hidden states; predicts a continuous normalized action chunk by Euler-style denoising. | The framework must set `diffusion_model_cfg.cross_attention_dim` to the actual VLM hidden size before building the head. `action_model_type` selects base DiT shape. |
| Layer-wise flow matching (`LayerwiseFM_ActionHeader`) | `QwenPI`, `QwenFM`, `QwenPI_v3`, `MiniCPMPI`, `Gemma4PI`, `CosmoPredict2PI`, `WanPI` | Consumes a list of layer-wise hidden states, one per DiT layer, and predicts continuous action chunks. | The framework populates DiT shape fields (`num_layers`, `input_embedding_dim`, `cross_attention_dim`, `num_attention_heads`) before head construction. `QwenPI_v3` can project VLM hidden states down via `action_dit_hidden_dim`. |
| Layer-wise discrete diffusion | `QwenDiscreteDiffusion` | MaskGIT-style discrete diffusion over action bins/tokens. | Keep separate from FAST; it is a diffusion action head, not autoregressive VLM action-token generation. |
| OpenPI-style action heads | `PI0`, `PI05` | OpenPI-compatible PaliGemma/Gemma action experts. | Requires the vendored OpenPI-compatible modules and matching model components. Verify before recommending for a released checkpoint. |
| ACT policy | `ACT` | Transformer action chunk from images/state. | Optional LeRobot dependency; StarVLA sets identity normalizers to avoid double normalization. |
| Diffusion Policy | `DiffusionPolicy` | DDPM/1D U-Net action generation from multi-image observations and state. | Uses a vendored subset, identity normalizers, and explicit EMA state-dict persistence. |

## Dimension and config contracts

Check these before model instantiation or checkpoint loading:

- `framework.name`: exact case-sensitive registry key. Examples: `QwenFast`, not `QwenFAST`; `QwenPI_v3`, not `QwenPI-V3`.
- `framework.action_model.action_horizon`: canonical chunk length. Legacy `future_action_window_size` should equal `action_horizon - 1` after compatibility normalization.
- `framework.action_model.action_dim`: last dimension of both training actions and predicted `normalized_actions`.
- `framework.action_model.state_dim`: expected proprioceptive state dimension when the framework uses state.
- `framework.image_keys` or equivalent VM4A keys: ordered camera names must match the dataset/bridge convention and the order of `example["image"]`.
- `framework.qwenvl.base_vlm` or `framework.world_model.base_wm`: must point to a local path or approved model id that is compatible with the framework key.
- `diffusion_model_cfg.cross_attention_dim`: must equal the actual backbone hidden size for cross-attention heads.
- `diffusion_model_cfg.num_layers`: for layer-wise PI heads, must match the number of selected backbone layers consumed by the action head.
- `diffusion_model_cfg.action_dit_hidden_dim`: `QwenPI_v3`-style compression hint; it is not a DiT constructor kwarg and is stripped before head construction.
- `diffusion_model_cfg.interleave_self_attention` / `use_canonical_forward`: forward-mode compatibility switch for layer-wise DiT checkpoints.

## Safe model-level smoke planning

Recommended smoke ladder:

1. **Registry-only:** run `scripts/inspect_framework_registry.py` to confirm the installed package can import the registry and that `framework.name` is registered.
2. **Config-only:** inspect the YAML for `framework.name`, action/state dimensions, action horizon, `base_vlm` or `base_wm`, and attention implementation. No model construction.
3. **Dependency-only:** import the relevant framework module and optional backend packages. Do not call `build_framework` yet if weights may be missing or downloads are not approved.
4. **Instantiation smoke:** only after confirming weights/backends, instantiate on the intended device and run a tiny synthetic `forward` or `predict_action` sample with correct image/state/action shapes.
5. **Checkpoint smoke:** for an existing checkpoint, use `from_pretrained` with minimal `config_overrides`; confirm `config.yaml`, `dataset_statistics.json`, and strict state-dict compatibility.

Source framework files include `if __name__ == "__main__"` demos for rapid debugging. They are useful evidence, but they are intentionally not bundled as runtime scripts here because they instantiate large models, may require local pretrained weights, may trigger downloads, and often assume GPU/accelerator availability. The bundled registry script is the safe default.
