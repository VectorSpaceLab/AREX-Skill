# Model and Workflow Overview

## Purpose

Read this when you need the verified model/config choices, resolution limits, and the public knobs that control HunyuanVideo-I2V generation or training.

## Supported Model Choices

The code exposes these transformer configs via `HUNYUAN_VIDEO_CONFIG`:

| Model | Notes |
| --- | --- |
| `HYVideo-T/2` | Main high-capacity I2V model used in the README examples |
| `HYVideo-T/2-cfgdistill` | Same family with `guidance_embed=True` |
| `HYVideo-S/2` | Smaller variant with fewer blocks and narrower hidden size |

## Core Runtime Choices

### Inference / Sampling

- `--i2v-mode` enables image-to-video behavior.
- `--i2v-resolution` accepts `360p`, `540p`, or `720p`.
- `--i2v-condition-type` accepts `token_replace` or `latent_concat`.
- `--i2v-stability` switches the stable motion recipe used in the README examples.
- `--flow-shift` is typically `7.0` for stable motion and `17.0` for more dynamic motion.
- `--video-length` defaults to `129`, and the code requires `video_length - 1` to be a multiple of 4.
- `--use-cpu-offload` is documented for large models or higher resolutions.

### LoRA Training

- The training script uses the same model family plus DeepSpeed.
- `--use-lora` turns on LoRA adaptation.
- `--lora-rank` defaults to `64`.
- `--task-flag` and `--output-dir` are required and drive the experiment directory.

### Latent Extraction

- `sample_n_frames` in `vae.yaml` controls the video window.
- `target_size` should match the bucket size for the desired resolution.
- `enable_multi_aspect_ratio` requires a square `sample_size` seed and generates bucketed aspect ratios.
- `use_stride` selects stride `2` for videos with fps >= 50, otherwise stride `1`.

## Prompt Templates and Encoders

The inspected constants define these prompt template keys:

- `dit-llm-encode`
- `dit-llm-encode-video`
- `dit-llm-encode-i2v`
- `dit-llm-encode-video-i2v`

I2V mode uses the `llm-i2v` text encoder/tokenizer and the CLIP encoder `clipL` as the secondary encoder.

## Constraints Worth Remembering

- The model expects aligned spatial sizes; `sample_image2video.py` aligns height and width to 16.
- The attention path uses flash-attn by default in the inspected code path.
- Multi-GPU xDiT is controlled by `--ulysses-degree` and `--ring-degree`; the product must equal the number of participating GPUs.
- The README documents 60GB GPU memory for 720p generation and 79GB for 360p LoRA training.

## Read This With

- [`references/checkpoints.md`](checkpoints.md) for the asset tree and download commands.
- [`references/troubleshooting.md`](troubleshooting.md) for memory, CUDA, and checkpoint failures.
- `sub-skills/inference/references/cli-reference.md` for the full inference flag set.
- `sub-skills/lora-training/references/cli-reference.md` for training flags and defaults.
