# Interactive TUI server

TurboDiffusion's TUI server is for repeated video generations in one terminal process. It parses a launch configuration once, loads shared assets, then loops over prompts until the user exits. This is the right interface when startup/model-load cost dominates and the user wants to try multiple prompts or outputs interactively.

## What stays loaded

- The VAE/tokenizer is loaded during startup from `--vae_path`.
- In T2V mode, the DiT checkpoint from `--dit_path` is created, moved to CUDA, and kept in the process for subsequent prompts.
- In I2V mode, the high-noise and low-noise DiT checkpoints are created once and retained in the process. During each generation the server moves the active high/low model between CPU and CUDA around the timestep boundary instead of re-reading checkpoints from disk.
- Text embeddings are recomputed per prompt using `--text_encoder_path`; the server intentionally does not clear all model state between prompts.

Full generation still requires a CUDA-capable TurboDiffusion runtime, compatible checkpoint files, VAE/text-encoder assets, and enough VRAM. This sub-skill only constructs and explains safe launch flows; it does not download assets or run generation.

## Launch methods

The same parser backs both public launches:

```bash
PYTHONPATH=turbodiffusion turbodiffusion-serve [server arguments]
PYTHONPATH=turbodiffusion python -m turbodiffusion.serve [server arguments]
```

Use the console entry point after the package is installed. Use the Python-module form when the entry point is unavailable or when debugging the Python interpreter that will import the package.

The source-layout `PYTHONPATH` prefix is a public package quirk: several runtime modules import `imaginaire`, `rcm`, `serve`, and `modify_model` as top-level modules. In a source checkout, `PYTHONPATH=turbodiffusion` exposes those modules. In another packaging layout, set the equivalent directory or omit the prefix only if those top-level modules are already importable.

## Minimal mode-specific launches

### T2V

```bash
PYTHONPATH=turbodiffusion turbodiffusion-serve \
  --mode t2v \
  --dit_path checkpoints/TurboWan2.1-T2V-1.3B-480P.pth
```

T2V requires exactly one DiT checkpoint path via `--dit_path`. If `--model`, `--resolution`, or `--sigma_max` are omitted, the server fills mode defaults: `Wan2.1-1.3B`, `480p`, and `80`.

### I2V

```bash
PYTHONPATH=turbodiffusion turbodiffusion-serve \
  --mode i2v \
  --high_noise_model_path checkpoints/TurboWan2.2-I2V-A14B-high-720P.pth \
  --low_noise_model_path checkpoints/TurboWan2.2-I2V-A14B-low-720P.pth
```

I2V requires both high-noise and low-noise model paths at launch. The input image is not a CLI launch option for the TUI; it is requested interactively after each text prompt. If `--model`, `--resolution`, or `--sigma_max` are omitted, the server fills mode defaults: `Wan2.2-A14B`, `720p`, and `200`.

## Prompt and output flow

After startup:

1. Enter a text prompt at `> `. End a line with `\` to continue the prompt on the next line.
2. In I2V mode, the server asks for `image`. The path must point to an existing image file. Pressing enter with no previous image, EOF, or interrupt cancels that generation but keeps the server running.
3. The server asks for `output`. Press enter to reuse the default or the last output path. If the entered output does not end with `.mp4`, the server appends `.mp4`.
4. The server generates the video and saves it. On success, the last output path becomes the default for the next prompt.
5. Use slash commands between generations to inspect or adjust runtime parameters.

## Slash commands

| Command | Effect |
| --- | --- |
| `/help` | Show TUI commands and runtime-settable parameters. |
| `/show` | Print immutable launch configuration plus current runtime parameter values. Changed runtime values are marked. |
| `/set <param> <value>` | Update one runtime-adjustable parameter. The value is type-checked and range/choice-checked. |
| `/reset` | Restore runtime-adjustable parameters to their launch-time defaults. |
| `/quit` | Exit the server process. |

Unknown slash commands are rejected and the server remains active.

## Runtime-adjustable parameters

Only these parameters can be changed with `/set` after model loading:

| Parameter | Type / validation | Notes |
| --- | --- | --- |
| `num_steps` | integer choice `1`, `2`, `3`, or `4` | Sampling step count. |
| `num_samples` | integer `>= 1` | Number of samples per generation. More samples increase memory and output grid size. |
| `num_frames` | integer `>= 1` | Video frame count. Higher values increase latent size and generation cost. |
| `sigma_max` | float `>= 0.1` | Initial sigma. Source defaults are `80` for T2V and `200` for I2V. |

Launch-only values such as `mode`, model paths, `resolution`, `aspect_ratio`, `attention_type`, `quant_linear`, `adaptive_resolution`, `ode`, and `seed` are not accepted by `/set`. Restart the server to change them.

## Keeping the server useful

- Prefer one server process per mode/checkpoint family. Changing from T2V to I2V, switching checkpoint files, or changing launch-only acceleration flags requires a restart.
- Validate file paths before launch; a missing model path wastes startup time and fails before the TUI loop.
- Match `--quant_linear` to quantized checkpoints. The flag changes model construction and cannot be toggled interactively.
- Keep backend installation and custom-op diagnostics separate from serving. If launch reaches an acceleration import/build error, route to the acceleration backend guidance instead of changing TUI parameters.
