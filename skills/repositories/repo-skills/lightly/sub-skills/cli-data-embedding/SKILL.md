---
name: cli-data-embedding
description: "Use LightlySSL CLIs, Hydra overrides, data layouts, YOLO crops,
  embeddings, lightly.core, and embedding APIs safely."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# cli-data-embedding

Use this sub-skill when a task needs LightlySSL console commands, safe command construction, input-folder checks, YOLO crop fixtures, embedding artifacts, or the high-level `lightly.core` / `lightly.embedding` APIs.

For a fresh public environment, start with `pip install lightly`. Add `lightly[timm]` only for TIMM / MAE / ViT-style optional modules, and `lightly[video]` only for direct video-file datasets requiring PyAV support.

## Route here for

- `lightly-version`, `lightly-ssl-train`, `lightly-embed`, `lightly-magic`, and `lightly-crop` command planning.
- Hydra override spelling, default CLI config keys, checkpoint and embedding output paths, and `LIGHTLY_LAST_CHECKPOINT_PATH` / `LIGHTLY_LAST_EMBEDDING_PATH` behavior.
- Image or video folder layout decisions before a CLI or `LightlyDataset` workflow.
- YOLO label format for `lightly-crop`, label-name YAML files, and tiny synthetic crop fixtures.
- Practical use of `lightly.core`, `lightly.embedding`, and Lightly-compatible embedding CSV files.

## Route elsewhere

- Custom PyTorch or PyTorch Lightning SSL loops, method recipes, or distributed training plans: use `training-workflows`.
- Low-level losses, transforms, datasets, collate functions, model heads, and tensor-shape debugging: use `ssl-building-blocks`.
- KNN / linear evaluation, benchmarking, tests, docs, notebooks, and maintainer workflows: use `evaluation-maintenance`.

## First actions

1. Identify the intended surface: CLI command, input data layout, crop labels, embedding CSV, or high-level Python API.
2. Read the relevant bundled reference rather than relying on source-repo docs:
   - [CLI reference](references/cli-reference.md)
   - [Data formats](references/data-formats.md)
   - [API reference](references/api-reference.md)
   - [Troubleshooting](references/troubleshooting.md)
3. Use bundled helpers for safe dry-run planning and validation:
   - `python scripts/build_cli_command.py --help`
   - `python scripts/validate_lightly_image_folder.py --help`
   - `python scripts/create_tiny_yolo_crop_fixture.py --help`
4. Treat train, embed, magic, and crop commands as artifact-writing operations. Build or validate the command first; execute only when the user has selected the input/output paths and runtime budget.

## Common safe patterns

- Start with `lightly-version` to confirm the console entry points are installed.
- For command construction, prefer `scripts/build_cli_command.py` so high-frequency Hydra keys such as `input_dir`, `loader.batch_size`, `trainer.max_epochs`, `collate.input_size`, `checkpoint`, `label_dir`, and `crop_padding` are spelled consistently.
- For data issues, run `scripts/validate_lightly_image_folder.py <dataset-dir>` before invoking a training, embedding, magic, or crop command.
- For crop command tests, generate a tiny self-contained fixture with `scripts/create_tiny_yolo_crop_fixture.py <out-dir>` and then inspect the printed `lightly-crop` command.
