---
name: training-and-data
description: "Guides FastVideo dataset layouts, latent preprocessing, modular YAML training, legacy recipe boundaries, and resource-safe training setup."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Training and data

Use for raw video/caption organization, precomputed latent datasets,
preprocessing, fine-tuning, and the new modular trainer.

## Data first

FastVideo commonly precomputes text embeddings and VAE latents to reduce
training memory. T2V records need text embeddings and video latents. I2V records
may additionally need first-frame latents and CLIP features. A merged dataset
uses a `videos/` directory and `videos2caption.json`; an HF dataset uses video
and caption columns. Read [data formats](references/data-formats.md) and run
the bundled [manifest validator](scripts/validate_manifest.py) before GPU work.

## Preprocessing

The preprocessing entry point accepts `--mode preprocess`, workload type,
dataset type (`hf` or `merged`), dataset paths/output, video loader, target
height/width/frame count/FPS, batching, and worker controls. Output is a
combined Parquet dataset containing serialized latent/embedding bytes and shape,
dtype, and sample metadata. Downloading data and encoding it are expensive;
start with a tiny validated sample.

## Training stack choice

New work uses `fastvideo.train`: YAML config, `Trainer = Method × Model ×
Callbacks × Config`, and `python -m fastvideo.train.entrypoint.train --config
CONFIG [--dry-run]`. Methods own losses/optimization, models own forward and
trainable parameters, callbacks own lifecycle hooks. Existing shipped recipes
may use the independent legacy `fastvideo.training` stack; never cross-import
those stacks. Read [training workflow](references/training-workflows.md) and
[training troubleshooting](references/troubleshooting.md).
