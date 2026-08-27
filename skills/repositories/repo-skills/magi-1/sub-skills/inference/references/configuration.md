# Configuration guide

Provenance: distilled from README.md sections 3 and 5, all six JSON files under example/4.5B/ and example/24B/, inference/common/config.py, inference/common/common_utils.py, inference/infra/distributed/dist_utils.py, inference/infra/checkpoint/checkpointing.py, inference/model/dit/dit_model.py, and comments in inference/infra/parallelism/context_parallel.py.

## Validate before editing

Use the bundled no-load validator whenever a config is copied or edited:

```bash
python3 scripts/magi_config_check.py example/4.5B/4.5B_base_config.json
python3 scripts/magi_config_check.py example/24B/24B_base_config.json --world-size 8
python3 scripts/magi_config_check.py my_config.json --check-paths --repo-root <magi-source-root>
```

The helper checks the dataclass-shaped JSON fields and MAGI-specific invariants without importing MAGI or loading model weights.

## Top-level schema

Every MAGI config has exactly three object sections:

```text
model_config
runtime_config
engine_config
```

The source `MagiConfig` dataclass requires every dataclass field to be present in the JSON, even fields that have defaults in Python. Missing fields raise a `ValueError` before inference begins.

### `model_config`

Core fields from the example configs:

| Field | Purpose / safe-edit note |
| --- | --- |
| `model_name` | Source examples use `videodit_ardf`; keep unchanged unless matching a known source implementation. |
| `num_layers`, `hidden_size`, `ffn_hidden_size`, `num_attention_heads`, `num_query_groups`, `kv_channels` | Architecture dimensions; must match the DiT checkpoint. Do not edit for memory savings. |
| `half_channel_vae`, `in_channels`, `out_channels` | Must match the VAE/DiT checkpoint family. 24B examples use half-channel VAE and 32 channels; 4.5B examples use 16 channels. |
| `params_dtype` | JSON string decoded by MAGI as a torch dtype. Examples use `torch.bfloat16`. |
| `patch_size`, `t_patch_size` | DiT latent patching; keep aligned with checkpoints. |
| `caption_channels`, `caption_max_length` | T5 embedding width and token cap; examples use 4096 and 800. |
| Other boolean/ratio fields | Architecture behavior; treat as checkpoint-coupled unless a trusted MAGI release notes otherwise. |

### `runtime_config`

Fields future agents most often edit:

| Field | Purpose / safe-edit note |
| --- | --- |
| `cfg_number` | Must be `3` for base configs and `1` when `engine_config.distill` or `engine_config.fp8_quant` is true. The source asserts this during config parsing. |
| `seed` | Random seed for Python, NumPy, PyTorch, and CUDA. |
| `num_frames` | Output video duration control. README notes 4 video frames correspond to 1 latent frame; source uses `temporal_downsample_factor` when calculating latent chunks. |
| `video_size_h`, `video_size_w` | Output/input processing size. Prefer multiples of 8 so VAE latent dimensions are integral; keep aspect ratio and memory budget in mind. |
| `num_steps` | Diffusion step count. Base examples use more steps than distill examples; lowering can reduce runtime but changes quality. |
| `window_size` | Chunk denoising window. README notes 4.5B distill+fp8 can use `window_size: 1` to fit GPUs with lower VRAM. |
| `fps` | MP4 output FPS and media-prefix sampling FPS. |
| `chunk_width` | Latent chunk width used by autoregressive generation. Keep with release configs unless you know the model schedule implications. |
| `load` | Directory containing the MAGI DiT checkpoint family. The loader appends `inference_weight`, `inference_weight.distill`, or `inference_weight.fp8` depending on engine flags. |
| `t5_pretrained` | Local T5 path/cache used for prompt embeddings. |
| `t5_device` | Examples use `cpu` for 4.5B and `cuda` for 24B. CPU saves GPU memory but can be slower. |
| `vae_pretrained` | Local VAE path used for i2v/v2v prefix encoding and final decoding. |
| `scale_factor`, `temporal_downsample_factor` | VAE scaling/sampling constants; keep with checkpoint family. |

Other CFG/KV fields (`cfg_t_range`, `prev_chunk_scales`, `text_scales`, `noise2clean_kvrange`, `clean_chunk_kvrange`, `clean_t`) are schedule controls. They are copied across release configs; edit only with model-specific justification.

### `engine_config`

| Field | Purpose / safe-edit note |
| --- | --- |
| `distributed_backend` | Examples use `nccl`. Source still asserts CUDA availability, so `gloo` is not a meaningful CPU fallback for generation. |
| `distributed_timeout_minutes` | Increase if slow checkpoint loading or startup causes group initialization timeouts. |
| `pp_size` | Pipeline parallel size. Product with `cp_size` must equal launched `WORLD_SIZE`. |
| `cp_size` | Context parallel size. Product with `pp_size` must equal launched `WORLD_SIZE`. |
| `cp_strategy` | `none` requires `cp_size: 1`; comments describe `cp_ulysses` for Hopper/newer GPUs and `cp_shuffle_overlap` for RTX 4090/older. |
| `ulysses_overlap_degree` | Used by `cp_ulysses`; keep example value unless tuning. |
| `fp8_quant` | Selects fp8 quantized DiT weights and requires the matching backend wheel/runtime. Source examples pair it with `distill: true`. |
| `distill` | Selects distill behavior and checkpoint subdirectory. Requires `cfg_number: 1`. |
| `shortcut_mode`, `distill_nearly_clean_chunk_threshold` | Distill/schedule controls; keep release values. |
| `kv_offload` | Example configs enable KV offload to reduce memory pressure. |
| `enable_cuda_graph` | Disabled in examples; enable only after stable fixed-shape runs. |

## Released example families

| Family | Config variants | Example process layout | Notable settings |
| --- | --- | --- | --- |
| 4.5B | base, distill, distill+fp8 | `pp_size: 1`, `cp_size: 1` | 34 layers, 3072 hidden, 720x720 default, T5 on CPU, README says at least 24 GB GPU memory; distill+fp8 can lower `window_size` to 1 for smaller memory. |
| 24B | base, distill, distill+fp8 | `pp_size: 1`, `cp_size: 8` in examples | 48 layers, 6144 hidden, 720x1280 default, T5 on CUDA, H100/H800 x8 recommended for base/distill; README notes RTX 4090 x8 should use `pp_size: 2`, `cp_size: 4`. |

Base configs set `distill: false`, `fp8_quant: false`, and `cfg_number: 3`.
Distill configs set `distill: true`, `fp8_quant: false`, and `cfg_number: 1`.
Distill+quant configs set `distill: true`, `fp8_quant: true`, and `cfg_number: 1`.

## Checkpoint path semantics

The three runtime checkpoint fields are independent:

```json
"load": "./downloads/4.5B_base",
"t5_pretrained": "./downloads/t5_pretrained",
"vae_pretrained": "./downloads/vae"
```

For DiT weights, the source loader appends a subdirectory below `load`:

| Engine flags | Required DiT subdirectory below `load` |
| --- | --- |
| `distill: false`, `fp8_quant: false` | `inference_weight` |
| `distill: true`, `fp8_quant: false` | `inference_weight.distill` |
| `fp8_quant: true` | `inference_weight.fp8` |

The loader expects a non-empty directory containing safetensors weights or a safetensors index. It may also read `.zst` compressed shards and therefore needs the decompression tool available when such files are present.

Do not report a config as generation-ready merely because JSON validation passes. Full generation still requires downloaded MAGI DiT, T5, VAE, and special-token assets at the resolved paths.

## Safe editing workflow

1. Copy a release config to a new file; never mutate a known-good release config in place.
2. Change only task-level fields first: `load`, `t5_pretrained`, `vae_pretrained`, `seed`, `video_size_h`, `video_size_w`, `num_frames`, `num_steps`, `fps`, and output path in the command.
3. If changing model family, copy the matching whole config instead of editing architecture dimensions.
4. If changing distill/fp8 flags, update `cfg_number` and verify the checkpoint subdirectory exists.
5. If changing `pp_size` or `cp_size`, update the launch world size at the same time.
6. Run `scripts/magi_config_check.py` after each edit.
7. Treat successful validation as a preflight only; real generation requires the backend and checkpoint assets.

## Backend validation boundary

The bundled config helper can validate schema, release-family invariants, path shape, and process-count expectations without loading MAGI weights. Run the root runtime preflight in the user's environment for dependency and CUDA checks. Neither helper replaces a real checkpoint-backed generation test that loads DiT, T5, VAE, special tokens, and writes a playable output video.
