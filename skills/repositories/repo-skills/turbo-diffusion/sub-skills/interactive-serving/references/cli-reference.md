# TUI CLI reference

The interactive server is exposed as `turbodiffusion-serve` and as the module `python -m turbodiffusion.serve`. Help was verified for both forms with the source-layout import prefix.

```bash
PYTHONPATH=turbodiffusion turbodiffusion-serve --help
PYTHONPATH=turbodiffusion python -m turbodiffusion.serve --help
```

Use the bundled dry-run renderer to construct a command without launching models:

```bash
python scripts/build_serve_command.py --mode t2v --dit-path checkpoints/t2v.pth --allow-missing
python scripts/build_serve_command.py --mode i2v \
  --high-noise-model-path checkpoints/i2v-high.pth \
  --low-noise-model-path checkpoints/i2v-low.pth \
  --allow-missing
```

The renderer emits CLI flags with TurboDiffusion's underscore spelling, matching the server parser.

## Launch selectors

| CLI flag | Values / default | Applies to | Meaning |
| --- | --- | --- | --- |
| `--mode` | `t2v` or `i2v`; default `t2v` | both | Select text-to-video or image-to-video serving. |
| `--model` | `Wan2.1-1.3B`, `Wan2.1-14B`, `Wan2.2-A14B`; mode-derived if omitted | both | Model architecture. If omitted, T2V uses `Wan2.1-1.3B`; I2V uses `Wan2.2-A14B`. |

## Required model paths by mode

| CLI flag | Required when | Meaning |
| --- | --- | --- |
| `--dit_path PATH` | `--mode t2v` | DiT checkpoint for text-to-video generation. |
| `--high_noise_model_path PATH` | `--mode i2v` | I2V high-noise DiT checkpoint used before the boundary switch. |
| `--low_noise_model_path PATH` | `--mode i2v` | I2V low-noise DiT checkpoint used after the boundary switch. |

The server exits during validation if the required path argument for the selected mode is missing. It does not require the unused mode's paths.

## Shared asset paths

| CLI flag | Source default | Meaning |
| --- | --- | --- |
| `--vae_path PATH` | `checkpoints/Wan2.1_VAE.pth` | Wan VAE/tokenizer checkpoint loaded once at startup. |
| `--text_encoder_path PATH` | `checkpoints/models_t5_umt5-xxl-enc-bf16.pth` | umT5 text encoder checkpoint used to embed each prompt. |

These paths are not downloaded by the server. Provide local files or keep the defaults only when those relative files exist in the working directory used to launch the command.

## Resolution and aspect ratio

| CLI flag | Defaults | Validation |
| --- | --- | --- |
| `--resolution VALUE` | `480p` for T2V, `720p` for I2V | Must be one of the resolution keys known to TurboDiffusion. |
| `--aspect_ratio W:H` | `16:9` | Must be one of the aspect-ratio keys available under the selected resolution. |
| `--adaptive_resolution` | off | I2V-only behavior that adapts output size to the input image aspect ratio while preserving the selected resolution area budget. |

Known resolution keys from the source validation map are `480p`, `720p`, `480`, `512`, and `720`. Each supports `1:1`, `4:3`, `3:4`, `16:9`, and `9:16`.

## Acceleration and model-construction flags

| CLI flag | Values / default | Meaning |
| --- | --- | --- |
| `--attention_type {sla,sagesla,original}` | default `sagesla` | Select attention implementation. `sagesla` additionally requires the optional SpargeAttn/SageSLA stack; backend failures should be routed to acceleration-backends. |
| `--sla_topk FLOAT` | default `0.1` | Top-k ratio used by SLA/SageSLA attention. Project examples often keep `0.1` and note `0.15` as a quality-oriented alternative. |
| `--quant_linear` | off | Construct quantized linear layers. Use with quantized checkpoints; omit for unquantized checkpoints. |
| `--default_norm` | off | Use default LayerNorm/RMSNorm instead of optimized custom normalization. |

These are launch-only settings. They are not accepted by the TUI `/set` command.

## Sampling and runtime defaults

| CLI flag | Source default | Runtime `/set` support | Meaning |
| --- | --- | --- | --- |
| `--num_steps {1,2,3,4}` | `4` | yes | Number of sampling steps. |
| `--num_samples INT` | `1` | yes | Number of videos per generation. |
| `--num_frames INT` | `81` | yes | Number of frames to generate. |
| `--sigma_max FLOAT` | `80` for T2V, `200` for I2V | yes | Initial sigma. |
| `--seed INT` | `0` | no | Random seed used for per-generation noise. |

Runtime-adjustable parameters are still initialized by CLI values. `/reset` returns them to those launch-time values, not necessarily to the source defaults.

## I2V-only generation behavior

| CLI flag | Source default | Meaning |
| --- | --- | --- |
| `--boundary FLOAT` | `0.9` | Timestep threshold for switching from high-noise to low-noise model. |
| `--ode` | off | Use ODE sampling, described by the source as sharper but less robust. |
| `--adaptive_resolution` | off | Derive generation width/height from the entered image aspect ratio under the selected resolution area. |

The TUI asks for an input image path after the text prompt; there is no `--image_path` launch argument for the serving CLI. Direct one-shot I2V commands with `--image_path` belong to the video-inference sub-skill.

## Source-layout import prefix

The package's installed entry point may still require a source-layout import path because serving imports top-level modules such as `imaginaire`, `rcm`, and `modify_model`. When those modules are not importable, use a launch like:

```bash
PYTHONPATH=turbodiffusion turbodiffusion-serve --mode t2v --dit_path checkpoints/t2v.pth
```

Do not bake a machine-specific checkout path into reusable instructions. Use the public source-layout directory name for source checkouts, or document the environment-specific equivalent outside runtime skill files.
