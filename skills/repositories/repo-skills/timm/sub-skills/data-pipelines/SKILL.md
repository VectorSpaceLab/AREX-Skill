---
name: data-pipelines
description: "Build timm data configs, datasets, transforms, loaders, ImageNet
  metadata, mixup/random erasing, and NaFlex data pipelines for train, eval, and
  inference."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# timm Data Pipelines

Use this sub-skill when a task needs timm data input handling rather than model discovery or optimizer/training-loop design. It covers `create_dataset`, `ImageDataset`, `IterableImageDataset`, `resolve_data_config`, `create_transform`, `create_loader`, ImageNet metadata helpers, mixup/random erasing, prefetcher/device/dtype choices, and NaFlex loader settings.

## Route by Task

- **Model-aligned inference/eval transforms**: start with `resolve_data_config(model=model)` or `resolve_data_config(pretrained_cfg=...)`, then pass the result into `create_transform`. See `references/data-api.md` and `references/transform-loader-recipes.md`.
- **Folder, tar, TorchVision, HF, TFDS, or WebDataset inputs**: use `create_dataset` with a reader-style `name`, `root`, `split`, `search_split`, and optional `class_map`. See `references/data-api.md`.
- **Training and validation loaders**: use `create_loader` to attach transforms to a dataset and create a PyTorch `DataLoader` or `PrefetchLoader`. Set `device=torch.device('cpu')` or `use_prefetcher=False` on CPU-only systems. See `references/transform-loader-recipes.md`.
- **Augmentation policy choices**: configure train-time `create_transform`/`create_loader` args such as `scale`, `ratio`, `hflip`, `color_jitter`, `auto_augment`, `re_prob`, `re_mode`, and `re_count`. Use `Mixup` or `FastCollateMixup` when labels need soft targets.
- **NaFlex variable-resolution pipelines**: use `create_transform(..., naflex=True, patch_size=..., max_seq_len=..., patchify=...)` for transform-only work or `create_naflex_loader` for loader-managed patchified batches. See `references/transform-loader-recipes.md`.
- **Class names and ImageNet subsets**: use `ImageNetInfo` and `infer_imagenet_subset` when mapping ImageNet indices, synsets, or model class counts to labels. See `references/data-api.md`.

## Common Workflow

1. Create or inspect the model in the model-library sub-skill when model selection is in scope.
2. Resolve data settings with `resolve_data_config(args=overrides, model=model)`.
3. Build an eval/inference transform with `create_transform(**data_config)` or a training transform with `create_transform(is_training=True, **data_config, ...)`.
4. Create the dataset with `create_dataset(...)` only when files or dataset services are needed.
5. Create the loader with `create_loader(dataset, **data_config, batch_size=..., is_training=...)`, explicitly deciding `device`, `img_dtype`, and `use_prefetcher`.

## Bundled Probe

Run `scripts/data_config_probe.py` to inspect a model's resolved data config and summarize eval/train transform objects without requiring a dataset. The script prints JSON-safe output and is useful before wiring loaders.

## Cross-Links

- Use the model-library sub-skill for selecting model names, pretrained configs, and NaFlex-compatible model creation.
- Use the training-workflows sub-skill for optimizer, loss, AMP, distributed training, and how mixup labels affect losses.
- Use the cli-workflows sub-skill for full `train.py`, `validate.py`, or `inference.py` command construction.

## Troubleshooting First Stops

- CPU-only loader fails: set `device=torch.device('cpu')` when `use_prefetcher=True`, or disable the prefetcher.
- Accuracy is unexpectedly poor: re-check `input_size`, `interpolation`, `mean`, `std`, `crop_pct`, and `crop_mode` from the model's pretrained config.
- Dataset cannot find classes or split: check `root`, `split`, `search_split`, folder names, and `class_map` file format.
- NaFlex fails shape assertions: confirm both model and loader/transform are NaFlex-compatible and agree on `patch_size`, `max_seq_len`, and `patchify_channels_last`.

See `references/troubleshooting.md` for detailed failure modes.
