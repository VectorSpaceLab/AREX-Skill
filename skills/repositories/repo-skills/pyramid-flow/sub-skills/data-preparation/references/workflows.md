# Data preparation workflows

This reference explains how Pyramid-Flow moves from JSONL annotations to precomputed text features and VAE latents. The bundled helpers validate command shapes; they do not run long distributed jobs or download checkpoints.

## Workflow overview

1. **Choose the row layout.** Use image-text rows for image training, raw video/image rows for Causal VAE training, and final video rows with `latent` plus `text_fea` for DiT training.
2. **Validate rows early.** Run `scripts/check_dataset_fixtures.py validate-jsonl` with the row kind that matches the stage.
3. **Precompute text features.** Use `scripts/build_precompute_commands.py text-features` to print a `torchrun` command for the text encoder extractor.
4. **Precompute VAE latents.** Use `scripts/build_precompute_commands.py vae-latents` to print a `torchrun` command for the Causal VAE latent extractor.
5. **Validate produced artifacts.** Check `.pt` text-feature dictionaries and latent tensor shapes before training.

## Distilled command-shape evidence

Pyramid-Flow ships two shell launchers for precomputation. They are represented here as safer command builders rather than copied shell scripts.

### Text-feature extraction launcher shape

The source shell launcher sets these effective defaults:

| Setting | Default shape |
| --- | --- |
| GPUs | `8` |
| Model name | `pyramid_flux` or `pyramid_mmdit` |
| Model dtype | `bf16` |
| Batch size | `1` in the shell launcher (`4` in the Python parser default) |
| Annotation file | video-text JSONL with `text` and `text_fea` fields |
| Checkpoint | Full Pyramid-Flow model/checkpoint directory matching `model_name` |

Distilled command shape:

```bash
torchrun --nproc_per_node 8 \
  tools/extract_text_features.py \
  --batch_size 1 \
  --model_dtype bf16 \
  --model_name pyramid_flux \
  --model_path checkpoints/pyramid-flow-miniflux \
  --anno_file annotation/video_text.jsonl
```

Use the bundled builder to validate required arguments before launching:

```bash
python scripts/build_precompute_commands.py text-features \
  --gpus 8 \
  --model-name pyramid_flux \
  --model-path checkpoints/pyramid-flow-miniflux \
  --anno-file annotation/video_text.jsonl \
  --validate-annotations
```

### VAE-latent extraction launcher shape

The source shell launcher sets these effective defaults:

| Setting | Default shape |
| --- | --- |
| GPUs | `8` |
| Model dtype | `bf16` |
| Batch size | `1` in the shell launcher (`4` in the Python parser default) |
| VAE checkpoint | Causal VAE checkpoint directory, usually inside the selected Pyramid-Flow checkpoint |
| Annotation file | JSONL with `video` and `latent` fields |
| Width/height | `640` x `384` for `384p` training latents |
| Raw frames | `121`, matching the `8k + 1` temporal pattern for 16 latent frames |

Distilled command shape:

```bash
torchrun --nproc_per_node 8 \
  tools/extract_video_vae_latents.py \
  --batch_size 1 \
  --model_dtype bf16 \
  --model_path checkpoints/pyramid-flow-miniflux/causal_video_vae \
  --anno_file annotation/video_text.jsonl \
  --width 640 \
  --height 384 \
  --num_frames 121
```

Use the bundled builder to validate resolution and frame alignment before launching:

```bash
python scripts/build_precompute_commands.py vae-latents \
  --gpus 8 \
  --model-path checkpoints/pyramid-flow-miniflux/causal_video_vae \
  --anno-file annotation/video_text.jsonl \
  --width 640 \
  --height 384 \
  --num-frames 121 \
  --validate-annotations
```

## Extractor CLI contracts

### `extract_text_features.py`

Reference-only source contract distilled into the builder:

| Flag | Required for real run | Default in parser | Notes |
| --- | --- | --- | --- |
| `--batch_size` | no | `4` | Shell launcher uses `1`. |
| `--anno_file` | yes | empty string | JSONL rows must include `text` and `text_fea`. |
| `--model_dtype` | no | `bf16` | Source accepts `bf16`, `fp16`, and falls back to fp32 for other values. Use explicit `bf16`, `fp16`, or `fp32`. |
| `--model_name` | yes | `pyramid_flux` | Choices: `pyramid_flux`, `pyramid_mmdit`. Must match checkpoint family. |
| `--model_path` | yes | empty string | Full model/checkpoint directory used to construct the matching text encoder. |

Runtime behavior:

- Initializes distributed mode before building the dataset and model.
- Reads annotation rows with `jsonlines`.
- Uses a `DistributedSampler` without shuffle.
- Calls the selected text encoder on batched prompts.
- Saves one `.pt` dictionary per row at `text_fea` with `prompt_embed`, `prompt_attention_mask`, and `pooled_prompt_embed`.

### `extract_video_vae_latents.py`

Reference-only source contract distilled into the builder:

| Flag | Required for real run | Default in parser | Notes |
| --- | --- | --- | --- |
| `--batch_size` | no | `4` | Shell launcher uses `1`. |
| `--model_path` | yes | empty string | Causal Video VAE checkpoint directory. |
| `--model_dtype` | no | `bf16` | Use `bf16`, `fp16`, or `fp32` explicitly. |
| `--anno_file` | yes | empty string | JSONL rows must include `video` and `latent`; optional `frames` overrides frame indices. |
| `--width` | yes for training alignment | `640` | Use `640` for `384p`, `1280` for `768p`. |
| `--height` | yes for training alignment | `384` | Use `384` for `384p`, `768` for `768p`. |
| `--num_frames` | yes for temporal alignment | `121` | Prefer values where `(num_frames - 1) % 8 == 0`. |
| `--save_memory` | optional | false | Enables VAE tiling before encoding. |

Runtime behavior:

- Initializes distributed mode and builds `CausalVideoVAELossWrapper` in eval mode.
- Reads rows with `jsonlines` and decodes videos through OpenCV.
- When `frames` is omitted, samples raw indices `0..num_frames-1`.
- Resizes/crops to the requested width/height, normalizes to `[-1, 1]`, and encodes with the Causal VAE.
- Saves one latent tensor per row at `latent`.

## Validation workflow without original datasets

Use synthetic smoke fixtures to prove the schema and precompute layout before touching a real dataset:

```bash
python scripts/check_dataset_fixtures.py smoke-fixtures --exercise-loaders
```

Expected signals:

- Image annotation validates and, when loaders are importable, `ImageTextDataset[0]` returns `video`, `text`, and `identifier`.
- Video annotation validates and a tiny latent `.pt` with shape `[1, 16, 2, 48, 80]` is accepted for `384p`.
- Text feature `.pt` validates as a dictionary containing `prompt_embed`, `prompt_attention_mask`, and `pooled_prompt_embed`.

## Hand-off to training

After precomputation, the DiT training annotation should be the final video layout containing `video`, `text`, `latent`, and `text_fea`. Use `../../training-workflows/SKILL.md` for launch flags and distributed invariants, and use this sub-skill again if training fails on JSONL row fields or artifact shapes.
