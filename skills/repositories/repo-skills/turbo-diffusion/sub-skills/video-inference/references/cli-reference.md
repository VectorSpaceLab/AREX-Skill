# CLI reference for one-shot video inference

TurboDiffusion's one-shot inference entry points are argparse scripts. The public source-layout launch pattern is:

```bash
PYTHONPATH=turbodiffusion python turbodiffusion/inference/wan2.1_t2v_infer.py --help
PYTHONPATH=turbodiffusion python turbodiffusion/inference/wan2.2_i2v_infer.py --help
```

The source-layout `PYTHONPATH` is a package quirk, not a private path: it points at the inner source directory that contains helper packages such as `imaginaire`, `rcm`, `serve`, `SLA`, and `ops`.

## Wan2.1 T2V script flags

Entry point: `turbodiffusion/inference/wan2.1_t2v_infer.py`

| Flag | Required | Values/default | Notes |
| --- | --- | --- | --- |
| `--dit_path` | yes | path string | Finetuned TurboDiffusion DiT checkpoint. |
| `--model` | no | `Wan2.1-1.3B` or `Wan2.1-14B`; default `Wan2.1-1.3B` | Must match the DiT checkpoint family. |
| `--num_samples` | no | integer; default `1` | Multiple samples are written into one arranged output by the source saver. |
| `--num_steps` | no | `1`, `2`, `3`, or `4`; default `4` | Timestep-distilled sampling steps. |
| `--sigma_max` | no | float; default `80` | Larger values may improve quality but reduce diversity. |
| `--vae_path` | no | default `checkpoints/Wan2.1_VAE.pth` | Pass explicitly to avoid relying on checkout defaults. |
| `--text_encoder_path` | no | default `checkpoints/models_t5_umt5-xxl-enc-bf16.pth` | umT5 text encoder checkpoint. |
| `--num_frames` | no | integer; default `81` | The repository shell comments may show an older default; parser help/source use 81. |
| `--prompt` | yes for one-shot | text string | Required unless `--serve` is used; this sub-skill routes serving elsewhere. |
| `--resolution` | no | string; default `480p` | README documents `480p` and `720p`. |
| `--aspect_ratio` | no | string; default `16:9` | Used to look up target dimensions. |
| `--seed` | no | integer; default `0` | Reproducibility seed for noise generation. |
| `--save_path` | no | default `output/generated_video.mp4` | Include a video suffix. |
| `--attention_type` | no | `sla`, `sagesla`, or `original`; default `sagesla` | `sagesla` requires optional SpargeAttn support. |
| `--sla_topk` | no | float; default `0.1` | README recommends trying `0.15` for better visual quality. |
| `--quant_linear` | no | boolean flag | Required for quantized DiT checkpoints; omit for unquantized checkpoints. |
| `--default_norm` | no | boolean flag | Keeps original LayerNorm/RMSNorm instead of using faster replacements. |
| `--serve` | no | boolean flag | Interactive server mode; route to `interactive-serving`. |

## Wan2.2 I2V script flags

Entry point: `turbodiffusion/inference/wan2.2_i2v_infer.py`

| Flag | Required | Values/default | Notes |
| --- | --- | --- | --- |
| `--image_path` | yes for one-shot | path string | Input image opened by PIL and converted to RGB. |
| `--high_noise_model_path` | yes | path string | High-noise DiT checkpoint, loaded first. |
| `--low_noise_model_path` | yes | path string | Low-noise DiT checkpoint, used after the boundary switch. |
| `--boundary` | no | float; default `0.9` | Switch from high-noise to low-noise model when current timestep is below this value. |
| `--model` | no | `Wan2.2-A14B`; default `Wan2.2-A14B` | Only I2V model exposed by the parser. |
| `--num_samples` | no | integer; default `1` | Multiple samples are arranged together in one output. |
| `--num_steps` | no | `1`, `2`, `3`, or `4`; default `4` | Timestep-distilled sampling steps. |
| `--sigma_max` | no | float; default `200` | I2V default differs from T2V. |
| `--vae_path` | no | source default `checkpoints/Wan2.1_VAE.pth` | README describes the VAE as applicable to both Wan2.1 and Wan2.2; pass explicitly. |
| `--text_encoder_path` | no | default `checkpoints/models_t5_umt5-xxl-enc-bf16.pth` | umT5 text encoder checkpoint. |
| `--num_frames` | no | integer; default `81` | Source parser default. |
| `--prompt` | yes for one-shot | text string | Required unless `--serve` is used. |
| `--resolution` | no | string; default `720p` | Target area for adaptive resolution; fixed size otherwise. |
| `--aspect_ratio` | no | string; default `16:9` | Fixed output ratio, or target-area ratio for adaptive mode. |
| `--adaptive_resolution` | no | boolean flag | Adapts output dimensions to input image aspect ratio while matching target area. |
| `--ode` | no | boolean flag | ODE sampling; sharper but less robust than SDE according to source help. |
| `--seed` | no | integer; default `0` | Reproducibility seed. |
| `--save_path` | no | default `output/generated_video.mp4` | Include a video suffix. |
| `--attention_type` | no | `sla`, `sagesla`, or `original`; default `sagesla` | `sagesla` requires optional SpargeAttn support. |
| `--sla_topk` | no | float; default `0.1` | README recommends trying `0.15` for better quality. |
| `--quant_linear` | no | boolean flag | Required when high/low checkpoints are quantized. |
| `--default_norm` | no | boolean flag | Keeps original norms. |
| `--serve` | no | boolean flag | Interactive server mode; route to `interactive-serving`. |

## Bundled T2V command-builder options

Script: [`../scripts/build_t2v_command.py`](../scripts/build_t2v_command.py)

Important options:

| Builder option | Maps to source flag | Behavior |
| --- | --- | --- |
| `--dit-path` | `--dit_path` | Required non-empty checkpoint path. |
| `--vae-path` | `--vae_path` | Required by the builder so missing assets are explicit. |
| `--text-encoder-path` | `--text_encoder_path` | Required by the builder so missing assets are explicit. |
| `--prompt` / `--prompt-file` | `--prompt` | Exactly one is required; `--prompt-file` avoids fragile shell quoting. |
| `--quant-linear` | `--quant_linear` | Must be provided if the checkpoint basename looks quantized. |
| `--allow-flag-mismatch` | none | Suppresses heuristic quantized/unquantized mismatch errors. |
| `--check-files` | none | Verifies referenced paths exist before rendering; off by default. |
| `--one-line` | none | Prints a one-line shell command instead of a multiline command. |
| `--no-pythonpath` | none | Omits the source-layout `PYTHONPATH` assignment. |

The builder validates that numeric counts are positive, `--num_steps` is 1-4, the output suffix is video-like, the prompt is non-empty, and the checkpoint/`--quant_linear` relationship is not obviously wrong.

## Bundled I2V command-builder options

Script: [`../scripts/build_i2v_command.py`](../scripts/build_i2v_command.py)

Important options:

| Builder option | Maps to source flag | Behavior |
| --- | --- | --- |
| `--high-noise-model-path` | `--high_noise_model_path` | Required non-empty high-noise checkpoint path. |
| `--low-noise-model-path` | `--low_noise_model_path` | Required non-empty low-noise checkpoint path. |
| `--image-path` | `--image_path` | Required non-empty input image path; suffix is checked heuristically. |
| `--vae-path` | `--vae_path` | Required by the builder. |
| `--text-encoder-path` | `--text_encoder_path` | Required by the builder. |
| `--prompt` / `--prompt-file` | `--prompt` | Exactly one is required. |
| `--adaptive-resolution` | `--adaptive_resolution` | Enables adaptive image-aspect resizing in the rendered command. |
| `--ode` | `--ode` | Enables ODE sampling in the rendered command. |
| `--quant-linear` | `--quant_linear` | Required if either high/low checkpoint basename looks quantized. |
| `--allow-flag-mismatch` | none | Suppresses heuristic quantization and high/low name checks. |
| `--check-files` | none | Verifies referenced paths exist before rendering; off by default. |

The I2V builder additionally catches high/low path swaps by looking for `high` or `low` markers in checkpoint basenames, warns when checkpoint resolution markers appear inconsistent with `--resolution`, and catches mixed quantized/unquantized high/low checkpoint pairs.
