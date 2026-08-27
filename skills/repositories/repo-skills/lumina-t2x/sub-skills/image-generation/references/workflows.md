# Image Generation Workflows

## Purpose

Read this when you need the exact commands, checkpoint layout, or option names for Lumina image inference and conversion tasks.

## Lumina-T2I

### Console route

- `lumina infer -c <config_path> <caption_here> <output_dir>`
- `lumina convert <weight_path> <output_dir>`

### Demo route

- `python -u demo.py --ckpt <ckpt_dir> [--precision fp32] [--ema]`

### Checkpoint layout

The checkpoint directory should contain:

- `model_args.pth`
- `consolidated*.pth` or `consolidated*.safetensors`

The inference config can supply `ckpt`, `ckpt_lm`, and `token`, or those can be passed on the CLI.

### High-value flags

- `--precision bf16|fp32` controls the model dtype.
- `--num_gpus 1` is the supported inference path.
- `--ema` loads the EMA checkpoint variant when available.
- `--token` is required for gated LLM access.
- The config controls `transport`, `ode`, and `infer` values such as `resolution`, `num_sampling_steps`, `cfg_scale`, `solver`, and `t_shift`.

## Lumina-Next-T2I

### Console route

- `lumina_next infer -c <config_path> <caption_here> <output_dir>`
- `lumina_next convert <weight_path> <output_dir>`

### Direct sampling route

- `python -u sample.py --ckpt <ckpt_dir> --image_save_path <out_dir> --caption_path <prompts.txt> --resolution <res> --time_shifting_factor <t> --cfg_scale <scale>`
- `python -u demo.py --ckpt <ckpt_dir> [--precision fp32] [--ema]`

### Checkpoint layout

- `model_args.pth`
- `consolidated*.pth` or `consolidated*.safetensors`
- A compatible Gemma checkpoint for the text encoder when the config does not hard-code `ckpt_lm`.

### High-value flags

- `--solver euler|midpoint|...` depends on the sample/demo script.
- `--proportional_attn` and `--scaling_method` affect extrapolated resolutions.
- `--num_gpus 1` is the supported inference path.
- `--ema` and `--precision bf16|fp32` mirror the Lumina-T2I route.

## Mini, img2img, compositional, and SD3 image generation

### Mini sampling

- `bash scripts/sample.sh`
- `bash scripts/sample_img2img.sh`
- `bash scripts/sample_sd3.sh`

### Mini direct routes

- `python -u sample.py --ckpt <ckpt_dir> --image_save_path <out_dir> --caption_path <prompts.txt> --resolution <res> --time_shifting_factor <t>`
- `python -u sample_img2img.py --ckpt <ckpt_dir> --image <input_image> --strength <0-1> ...`
- `python -u sample_sd3.py --ckpt <ckpt_dir> --caption_path <prompts.txt> ...`
- `python -u demo.py --ckpt <ckpt_dir> [--precision fp32] [--ema] [--use_flash_attn False]`

### Compositional generation

The compositional branch reuses the Lumina-Next-T2I style checkpoint layout and changes the prompt-to-region attention behavior.
Read the compositional workflow notes when the user needs multiple captions mapped to different image regions.

### Checkpoint/layout notes

- Mini inference still expects a compatible checkpoint directory with `model_args.pth` and `consolidated*.pth`.
- `--use_flash_attn False` is a runtime model flag, not a substitute for installing a working `flash-attn` package when the module import itself requires it.

## Common recovery steps

- Recheck the checkpoint tree if the script cannot find `model_args.pth` or a `consolidated*` file.
- Verify that the image config points at the right checkpoint and text-encoder path.
- Use a single-GPU inference launch first; these inference paths do not support multi-GPU sampling.
