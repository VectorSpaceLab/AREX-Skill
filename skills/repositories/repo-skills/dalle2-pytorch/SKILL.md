---
name: dalle2-pytorch
description: "Use the DALLE2-pytorch package for DALL-E 2 style text-to-image
  model APIs, diffusion prior/decoder training, WebDataset data layouts, and
  tracker/checkpoint workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# DALLE2-pytorch

Use this repo skill when a task involves the `dalle2-pytorch` package, DALL-E 2 style CLIP-latent text-to-image generation, diffusion prior training, cascaded decoder training, DALLE2 checkpoints, WebDataset embedding data, or the package's training/experiment tracking utilities.

## What This Skill Covers

- Public Python APIs for `DALLE2`, `DiffusionPriorNetwork`, `DiffusionPrior`, `Unet`, `Decoder`, CLIP adapters, VQGAN/VAE latent diffusion, inpainting, tokenization, and the `dream` CLI.
- JSON config classes and bundled training launchers for decoder and diffusion-prior training.
- WebDataset and EmbeddingReader data layouts, sidecar embedding folders, shard/index validation, trackers, checkpoint loading, and checkpoint saving.
- Troubleshooting for install/import, CLIP downloads, CPU vs GPU expectations, config validation, data layout, tracker credentials, and checkpoint format mismatches.

## Install And Minimal Check

Install the public package:

```bash
python -m pip install dalle2-pytorch
```

Run the bundled package check from this skill directory:

```bash
python scripts/check_install.py --mode imports
python scripts/check_install.py --mode cli-help
```

For a CPU-only synthetic API smoke test that avoids CLIP downloads and model weights:

```bash
python sub-skills/generation-and-api/scripts/check_dalle2_runtime.py --mode tiny-forward
```

## Choose A Sub-Skill

### `generation-and-api`

Read [sub-skills/generation-and-api/SKILL.md](sub-skills/generation-and-api/SKILL.md) for Python model construction and generation tasks:

- Build or call `DALLE2`, `DiffusionPrior`, `Decoder`, `Unet`, CLIP adapters, or `VQGanVAE`.
- Use `dream`, load generation checkpoints, tokenize prompts, sample images, or perform decoder inpainting.
- Debug checkpoint architecture mismatches, CLIP weight downloads, CPU/GPU limitations, inpaint mask shape, or classifier-free guidance.

### `training-and-configs`

Read [sub-skills/training-and-configs/SKILL.md](sub-skills/training-and-configs/SKILL.md) for training and configuration tasks:

- Author/validate `TrainDecoderConfig` or `TrainDiffusionPriorConfig` JSON.
- Use `DecoderTrainer` or `DiffusionPriorTrainer` directly.
- Build `python` or `accelerate launch` commands, run bundled training wrappers, resume/save trainer checkpoints, or debug `unet_training_mask`, resampling, DeepSpeed fp16, and config errors.

### `data-and-tracking`

Read [sub-skills/data-and-tracking/SKILL.md](sub-skills/data-and-tracking/SKILL.md) for data and experiment-management tasks:

- Validate decoder WebDataset shard names, sample keys, sidecar image/text embedding folders, `shard_width`, or `index_width`.
- Use `ImageEmbeddingDataset`, `create_image_embedding_dataloader`, `get_reader`, `make_splits`, or `PriorEmbeddingDataset`.
- Configure console/W&B logging, local/URL/W&B checkpoint loading, or local/W&B/HuggingFace saving.

## Important Constraints

- Real training and useful image sampling normally need GPU memory and trained checkpoints. CPU is suitable for imports, config parsing, CLI help, and tiny synthetic forward-loss tests.
- CLIP adapters (`OpenAIClipAdapter`, `OpenClipAdapter`) may download weights and require network/cache. Do not instantiate them in offline smoke checks unless weights are already cached.
- Training examples may need datasets, W&B/HuggingFace/S3 credentials, metric assets, and long runtime. Validate configs and data layout before launch.
- The `dream` CLI expects a combined DALLE2 checkpoint with package-expected init/model keys; trainer checkpoints are a different format.
- If `clip-anytorch` fails because `pkg_resources` is missing, install `setuptools<81` and rerun `python -m pip check`.

## Root References

- Repository snapshot and refresh baseline: [references/repo-provenance.md](references/repo-provenance.md).
- Cross-cutting install/import/backend troubleshooting: [references/troubleshooting.md](references/troubleshooting.md).
- Router metadata used by managed import: [references/repo-routing-metadata.json](references/repo-routing-metadata.json).

## Self-Containment Rule

Use the bundled references and scripts in this skill tree. Do not require future agents to open, run, or copy scripts, docs, configs, tests, or examples from an original DALLE2-pytorch checkout. When a user wants to train in a checkout intentionally, treat that checkout as their working project, not as this skill's required evidence source.
