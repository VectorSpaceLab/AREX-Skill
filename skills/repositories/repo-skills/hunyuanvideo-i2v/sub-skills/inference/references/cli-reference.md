# Inference CLI Reference

## Purpose

Use this for the verified inference flags and their main defaults. The values come from `hyvideo/config.py` and `HunyuanVideoSampler.predict()`.

## Main Flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--model` | `HYVideo-T/2-cfgdistill` | Model family choice; README examples often use `HYVideo-T/2` for I2V |
| `--i2v-mode` | off | Enables image-to-video behavior |
| `--i2v-image-path` | `./assets/demo/i2v/imgs/0.png` | Reference image |
| `--i2v-resolution` | `720p` | One of `360p`, `540p`, `720p` |
| `--i2v-stability` | off | Stable-motion recipe |
| `--flow-shift` | `17.0` | README recommends `7.0` for stable, `17.0` for dynamic |
| `--video-length` | `129` | Must satisfy `(video_length - 1) % 4 == 0` |
| `--use-cpu-offload` | off | Helpful for large models or lower-VRAM hosts |
| `--use-lora` | off | Enables LoRA weights at inference time |
| `--lora-path` | `""` | Path to a `.safetensors` LoRA weight |
| `--lora-scale` | `1.0` | LoRA fusion strength |
| `--ulysses-degree` | `1` | xDiT sequence-parallel degree |
| `--ring-degree` | `1` | xDiT sequence-parallel degree |
| `--model-base` | `ckpts` | Root of the checkpoint tree |
| `--i2v-dit-weight` | `ckpts/hunyuan-video-i2v-720p/transformers/mp_rank_00_model_states.pt` | I2V transformer weight path |
| `--vae` | `884-16c-hy` | The only checked VAE name |
| `--prompt-template` | `dit-llm-encode-i2v` in I2V mode | Used by the decoder-only text encoder |

## Sample Output Contract

`HunyuanVideoSampler.predict()` returns a dictionary with at least:

- `samples`: generated video tensors/images
- `seeds`: the concrete seed list used
- `prompts`: the prompt list used
- `size`: `(height, width, video_length)` after alignment

## Notes

- `parse_args()` accepts `mode="eval"` by default and also supports the training path.
- The inference code imports `xfuser` only for multi-GPU support; that path is optional.
- The code aligns height and width to 16 before sampling.
