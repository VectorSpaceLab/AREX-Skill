# Model and Asset Catalog

## Purpose

Read this when choosing TurboDiffusion checkpoints, Wan model flags, VAE/text encoder assets, input prompts/images, or TurboT2AV paths. This reference distills public README evidence into a self-contained planning table; it does not download weights.

## Core TurboDiffusion models

| Public model/checkpoint family | Script mode | Model flag | Best documented resolution | Checkpoint role |
| --- | --- | --- | --- | --- |
| `TurboWan2.1-T2V-1.3B-480P` | T2V | `Wan2.1-1.3B` | 480p | single `--dit_path` checkpoint; quantized and unquantized variants exist |
| `TurboWan2.1-T2V-14B-480P` | T2V | `Wan2.1-14B` | 480p | single `--dit_path` checkpoint; quantized and unquantized variants exist |
| `TurboWan2.1-T2V-14B-720P` | T2V | `Wan2.1-14B` | 720p | single `--dit_path` checkpoint; quantized and unquantized variants exist |
| `TurboWan2.2-I2V-A14B-720P` | I2V | `Wan2.2-A14B` | 720p | two checkpoints: `--high_noise_model_path` and `--low_noise_model_path`; quantized and unquantized variants exist |

All public checkpoints support 480p or 720p, but the best-resolution column tells future agents what the README claims as best quality.

## Shared assets

Core T2V/I2V workflows normally need:

- Wan VAE checkpoint, usually passed as `--vae_path`.
- umT5 text encoder checkpoint, usually passed as `--text_encoder_path`.
- TurboDiffusion DiT checkpoint(s): one for T2V, high/low pair for I2V.
- A long English prompt. The README warns current models are trained on long English prompts; short, non-English, or underspecified prompts may need augmentation.
- For I2V, an RGB input image passed as `--image_path`.
- A writable video output path, usually an `.mp4`.

## Quantized versus unquantized commands

| Situation | Recommended flag behavior |
| --- | --- |
| Quantized checkpoint filename or user confirms quantized checkpoint | add `--quant_linear` |
| Unquantized checkpoint on H100-class or other large-memory GPU | omit `--quant_linear` |
| RTX 5090/4090 or similar memory-constrained run with quantized checkpoint | add `--quant_linear` |
| Unsure whether checkpoint is quantized | ask or inspect checkpoint naming/metadata before rendering the command |

The `--default_norm` flag means "use original LayerNorm/RMSNorm"; leaving it off allows TurboDiffusion to replace supported norms with faster implementations.

## Attention options

| `--attention_type` | Meaning | Extra dependencies |
| --- | --- | --- |
| `sagesla` | Default README fast path using SageSLA | Requires SpargeAttn installed separately |
| `sla` | Sparse-linear attention path without the SpargeAttn Sage kernels | Uses CUDA/Triton/custom package paths; validate on target GPU |
| `original` | Original dense attention path | Slowest but useful for fallback/debug comparison |

Default examples often use `--attention_type sagesla --sla_topk 0.1`; the README recommends `--sla_topk 0.15` for better video quality in some cases.

## T2V command essentials

Minimum T2V command inputs:

- `--model` one of `Wan2.1-1.3B` or `Wan2.1-14B`.
- `--dit_path` to a matching TurboWan2.1 T2V checkpoint.
- `--prompt` with a long English prompt.
- `--resolution` (`480p` or `720p`) and `--aspect_ratio` (`16:9` in README examples).
- Optional but common: `--num_steps 4`, `--num_samples 1`, `--seed`, `--save_path`, `--quant_linear`, `--attention_type`, `--sla_topk`.

Use [video inference](../sub-skills/video-inference/SKILL.md) for command construction.

## I2V command essentials

Minimum I2V command inputs:

- `--model Wan2.2-A14B`.
- `--high_noise_model_path` and `--low_noise_model_path` for the matching TurboWan2.2 I2V pair.
- `--image_path` pointing to the input image.
- `--prompt` with a long English prompt.
- `--resolution`, often `720p`.
- Optional but common: `--adaptive_resolution`, `--ode`, `--boundary 0.9`, `--quant_linear`, `--attention_type sagesla`, `--sla_topk 0.1`.

Validate high/low checkpoint names before rendering. Swapping them can produce a syntactically valid but semantically wrong command.

## TurboT2AV assets

TurboT2AV is separate from core Wan video generation. It uses the LTX-2 environment and normally needs:

- LTX-2 base checkpoint such as `ltx-2-19b-dev.safetensors`.
- Gemma-3 directory; Gemma is gated and requires Hugging Face access approval/token before download.
- TurboT2AV student checkpoint directory containing the student model.
- Prompt file (`.txt` one prompt per line or `.csv` with `prompt` column).
- Output directory.
- Config path for the LTX distillation pipeline.

Use [turbot2av-extension](../sub-skills/turbot2av-extension/SKILL.md) for command rendering and dependency separation.
