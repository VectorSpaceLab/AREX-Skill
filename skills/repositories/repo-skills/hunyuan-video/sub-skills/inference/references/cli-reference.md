# CLI Reference

Read this when building or reviewing HunyuanVideo sampling commands. The original repository exposes these flags through its parser; this skill bundles `scripts/run_sample_video.py` as a self-contained runner with equivalent high-value options and an explicit `--repo-root`.

## High-value flags

| Flag | Default | Notes |
| --- | --- | --- |
| `--repo-root` | `.` in bundled runner | HunyuanVideo checkout/source root containing the `hyvideo` package. |
| `--model-base` | `ckpts` | Root directory containing HunyuanVideo checkpoints and text encoders. |
| `--dit-weight` | `ckpts/hunyuan-video-t2v-720p/transformers/mp_rank_00_model_states.pt` | File or directory containing DIT weights. FP8 uses a different explicit file. |
| `--model` | `HYVideo-T/2-cfgdistill` | Choices: `HYVideo-T/2`, `HYVideo-T/2-cfgdistill`. |
| `--vae` | `884-16c-hy` | Implies 16 latent channels and `4n+1` frame rule. |
| `--precision` | `bf16` | Transformer dtype. |
| `--vae-precision` | `fp16` | VAE dtype. |
| `--prompt` | required in bundled runner | Runtime `predict()` requires a string prompt. |
| `--video-size` | `544 960` in bundled runner, `720 1280` in source parser | Height then width. |
| `--video-length` | `129` | For default VAE, use `1` or `(length - 1) % 4 == 0`. |
| `--infer-steps` | `50` | Number of denoising steps. |
| `--seed` | `None` | `None` produces random seeds; integer seed expands across multiple videos. |
| `--cfg-scale` | `1.0` | If exactly 1.0, negative prompt is cleared. |
| `--embedded-cfg-scale` | `6.0` | Embedded guidance scale used by examples. |
| `--flow-shift` | `7.0` | Examples use 7.0. |
| `--flow-reverse` | false unless flag present | Examples pass this flag. |
| `--use-cpu-offload` | false unless flag present | Single-GPU memory mitigation; incompatible with distributed xDiT. |
| `--num-videos` | `1` | Number of videos per prompt. |
| `--save-path` | `./results` | Output directory for generated MP4s. |
| `--use-fp8` | false unless flag present | Requires FP8 DIT weight and companion map; see optimization sub-skill. |

## Supported public resolutions from docs

The documentation highlights 540p and 720p aspect-ratio presets:

| Class | 9:16 | 16:9 | 4:3 | 3:4 | 1:1 |
| --- | --- | --- | --- | --- | --- |
| 540p | `544 960` | `960 544` | `624 832` | `832 624` | `720 720` |
| 720p | `720 1280` | `1280 720` | `1104 832` | `832 1104` | `960 960` |

Pass these as `--video-size HEIGHT WIDTH`.

## Builder helper

Use the bundled helper to avoid common frame-count or quoting mistakes:

```bash
python sub-skills/inference/scripts/build_sample_command.py --prompt "A cinematic shot of waves" --height 544 --width 960 --video-length 129 --seed 123 --use-cpu-offload
```
