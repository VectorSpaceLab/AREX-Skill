# Model and asset selection for video inference

TurboDiffusion one-shot inference does not fetch assets by itself. A user must provision the model files, base Wan assets, and input image before running rendered commands.

## README model catalog

| Model name | Workflow | Best resolution | DiT checkpoint role |
| --- | --- | --- | --- |
| `TurboWan2.2-I2V-A14B-720P` | Wan2.2 image-to-video | 720p | Two DiT checkpoints: high-noise and low-noise. |
| `TurboWan2.1-T2V-1.3B-480P` | Wan2.1 text-to-video | 480p | One DiT checkpoint for `--model Wan2.1-1.3B`. |
| `TurboWan2.1-T2V-14B-480P` | Wan2.1 text-to-video | 480p | One DiT checkpoint for `--model Wan2.1-14B`. |
| `TurboWan2.1-T2V-14B-720P` | Wan2.1 text-to-video | 720p | One DiT checkpoint for `--model Wan2.1-14B`. |

The README states that all listed checkpoints support 480p or 720p generation; the best-resolution column is a quality recommendation, not a hard parser constraint.

## Common base assets

| Asset | Used by | Typical filename | CLI flag |
| --- | --- | --- | --- |
| Wan VAE | T2V and I2V | `Wan2.1_VAE.pth` | `--vae_path` |
| umT5 text encoder | T2V and I2V | `models_t5_umt5-xxl-enc-bf16.pth` | `--text_encoder_path` |
| T2V DiT checkpoint | T2V | `TurboWan2.1-T2V-...(.pth)` or `...-quant.pth` | `--dit_path` |
| I2V high-noise DiT checkpoint | I2V | `TurboWan2.2-I2V-A14B-high-720P(.pth)` or `...-quant.pth` | `--high_noise_model_path` |
| I2V low-noise DiT checkpoint | I2V | `TurboWan2.2-I2V-A14B-low-720P(.pth)` or `...-quant.pth` | `--low_noise_model_path` |
| Input image | I2V only | `.jpg`, `.jpeg`, `.png`, or `.webp` | `--image_path` |

The I2V parser's default VAE path is named `Wan2.1_VAE.pth` even though README prose refers to Wan2.2 I2V; pass an explicit VAE path in generated commands to avoid ambiguity.

## Quantized vs unquantized checkpoints

The README guidance is:

- GPUs with more than about 40 GB VRAM, such as H100-class systems, should use unquantized checkpoints and omit `--quant_linear`.
- RTX 5090, RTX 4090, or similar VRAM-limited GPUs should use quantized checkpoints whose filenames usually include `-quant` and add `--quant_linear`.

Practical rules:

1. If the checkpoint basename contains `quant`, include `--quant_linear` unless you have renamed files and know the checkpoint format.
2. If using unquantized checkpoints, omit `--quant_linear`; using the quantized Linear replacement with an unquantized state dict can cause state-dict/load mismatches.
3. I2V high and low checkpoints should be the same quantization family. A mixed pair is usually a mistake.
4. Match the model family: `Wan2.1-1.3B` for 1.3B checkpoints, `Wan2.1-14B` for 14B checkpoints, and `Wan2.2-A14B` for I2V high/low checkpoints.

## Attention backend selection

| `--attention_type` | What it means | Asset/dependency implications |
| --- | --- | --- |
| `sagesla` | SageSLA-backed sparse attention; default in public examples. | Requires optional SpargeAttn/SageAttention-compatible support in addition to base TurboDiffusion. Route install/build failures to `acceleration-backends`. |
| `sla` | TurboDiffusion sparse-linear attention path. | Requires the package's CUDA/backend pieces; validate on the target environment. |
| `original` | Original attention path. | Useful when isolating SLA/SageSLA dependency failures; slower and may exceed memory with large models. |

`--sla_topk` controls the sparse top-k ratio for `sla` and `sagesla`. Public examples use `0.1`; README suggests `0.15` may improve quality in some settings.

## T2V asset checklist

For a one-shot T2V command, collect:

- `--dit_path`: one T2V DiT checkpoint matching `--model`.
- `--vae_path`: Wan VAE file.
- `--text_encoder_path`: umT5 text encoder file.
- `--prompt`: long English prompt.
- `--save_path`: output filename with suffix.

Optional but common:

- `--quant_linear` if using `-quant` checkpoint.
- `--attention_type sagesla --sla_topk 0.1` for the README-style accelerated path.
- `--resolution 480p` for 1.3B 480P checkpoints unless quality testing calls for 720p.

## I2V asset checklist

For a one-shot I2V command, collect:

- `--high_noise_model_path`: I2V high-noise DiT checkpoint.
- `--low_noise_model_path`: I2V low-noise DiT checkpoint.
- `--vae_path`: Wan VAE file.
- `--text_encoder_path`: umT5 text encoder file.
- `--image_path`: input image file.
- `--prompt`: long English motion/scene prompt grounded in the input image.
- `--save_path`: output filename with suffix.

Optional but common:

- `--adaptive_resolution` to preserve the input image's aspect ratio while using the selected target area.
- `--ode` for sharper but less robust sampling.
- `--quant_linear` if both high and low checkpoints are quantized.
- `--resolution 720p` for the A14B 720P model's best-resolution setting.

## No-download policy for runtime use

Do not place downloader commands, credentials, tokens, or private cache paths in runtime instructions. If assets are missing, tell the user which role is missing and where it plugs into the CLI; let the user obtain files through their approved model-access process.
