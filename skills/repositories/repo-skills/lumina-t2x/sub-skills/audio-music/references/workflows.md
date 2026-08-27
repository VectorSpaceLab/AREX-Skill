# Audio and Music Workflows

## Purpose

Read this when you need to launch the text-to-audio or text-to-music demos or validate the checkpoint layout first.

## Prerequisites

- The audio and music demo modules import FlashAttention-backed model code, so a compatible `flash-attn` build must be available before you launch the demos.
- Install the audio/music extras and confirm the checkpoint tree before using the Gradio scripts.

## Text-to-audio

### Demo route

- `python -u demo_audio.py --ckpt <audio_generation_ckpt> --vocoder_ckpt <bigvnat_ckpt> --config_path configs/lumina-text2audio.yaml --sample_rate 16000`
- `bash run_audio.sh` after editing the placeholder paths in the script and config.

### Required checkpoint layout

The audio checkpoint root is expected to contain folders or files referenced by the demo config, typically:

- `audio_generation/`
- `maa2/`
- `bigvnat/`
- `CLAP/` assets referenced by the config

### Audio-specific setup

- The demo uses a structure-caption helper so the audio prompt is turned into a time-structured caption before generation.
- The helper is credential / network bound and should be treated as an external dependency, not a core runtime promise.

## Text-to-music

### Demo route

- `python -u demo_music.py --ckpt <music_generation_ckpt> --vocoder_ckpt <bigvnat_ckpt> --config_path configs/lumina-text2music.yaml --sample_rate 16000`
- `bash run_music.sh` after editing the placeholder paths.

### Required checkpoint layout

The music checkpoint root is expected to contain folders or files referenced by the demo config, typically:

- `music_generation/`
- `maa2/`
- `bigvnat/`

## Shared flags and behavior

- `--num_gpus 1` is the supported inference path in the current repo version.
- `--ema` selects the EMA checkpoint variant when it exists.
- `--precision bf16|fp32` is exposed by the audio demo; music uses `bf16` by default and may restrict the choices more narrowly.
- `--sample_rate 16000` is the documented runtime value.

## Workflow notes

- Keep the config file, checkpoint tree, and shell wrapper synchronized.
- If the demo mentions a placeholder path inside `configs/lumina-text2audio.yaml` or `configs/lumina-text2music.yaml`, update it before launching.
- Use the bundled checker to confirm the expected folders and config fields before running a Gradio demo.
