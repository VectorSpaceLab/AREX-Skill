# Data API Reference

## Core Factory Map

| API | Use it for | Key inputs | Output / side effect |
| --- | --- | --- | --- |
| `resolve_data_config(args=None, pretrained_cfg=None, model=None, use_test_size=False, verbose=False)` | Resolve model-aligned image size and normalization | CLI-style `args` dict, `model.pretrained_cfg`, or explicit `pretrained_cfg` | Dict with `input_size`, `interpolation`, `mean`, `std`, `crop_pct`, and `crop_mode` |
| `create_transform(input_size=224, is_training=False, ...)` | Build train/eval/inference preprocessing | Data config plus augmentation, random erasing, prefetcher, and NaFlex options | TorchVision-style transform pipeline or separated train transform tuple |
| `create_dataset(name, root=None, split='validation', search_split=True, ...)` | Create folder, tar, TorchVision, HF, TFDS, or WebDataset-backed datasets | Reader-style `name`, `root`, `split`, `class_map`, iterable hints | `ImageDataset`, `IterableImageDataset`, TorchVision dataset, or ImageFolder |
| `create_loader(dataset, input_size, batch_size, is_training=False, ...)` | Attach transforms and create a dataloader | Dataset, data config, augmentation, worker, prefetcher, device, dtype choices | PyTorch `DataLoader`, `MultiEpochsDataLoader`, or `PrefetchLoader` |
| `create_naflex_loader(dataset, patch_size=None, train_seq_lens=..., max_seq_len=..., ...)` | Variable sequence length NaFlex training/eval | Map-style dataset, NaFlex model patch settings, sequence lengths | Loader producing patch dict batches, optionally prefetched |

## `resolve_data_config` Precedence

`resolve_data_config` requires at least one of `args`, `pretrained_cfg`, or `model`.

- `args['input_size']` overrides everything and must be a 3-item tuple/list `(channels, height, width)`.
- `args['img_size']` creates square `(channels, img_size, img_size)` input if `input_size` is not set.
- `args['in_chans']` or `args['chans']` controls channel count unless `input_size` already specifies it.
- `pretrained_cfg['input_size']`, `interpolation`, `mean`, `std`, `crop_pct`, and `crop_mode` are used when args do not override them.
- `use_test_size=True` prefers `test_input_size` and `test_crop_pct` when a pretrained config provides them.
- A single-value `mean` or `std` override is repeated to match channel count; otherwise the tuple length must match channels.

Prefer `resolve_data_config(args=overrides, model=model)` when adapting a pretrained model to a non-default size, because explicit overrides remain visible and model defaults still fill missing values.

## Dataset Names and Reader Families

`create_dataset` lowercases `name` and dispatches by prefix:

| Name pattern | Dataset type | Notes |
| --- | --- | --- |
| `''`, `folder`, tar/image reader names | timm `ImageDataset` | Default path for folder/tar readers; supports `class_map`, `load_bytes`, `input_img_mode` |
| `torch/cifar10`, `torch/cifar100`, `torch/mnist`, etc. | TorchVision dataset | Uses `download` when supported and maps train/eval split synonyms |
| `torch/image_folder` or `torch/folder` | TorchVision `ImageFolder` | Useful when the TorchVision implementation is specifically needed |
| `torch/imagenet` | TorchVision `ImageNet` | Maps eval synonyms to `val`; does not pass `download` |
| `hfds/...` | timm `ImageDataset` with Hugging Face Datasets reader | Random-access HF dataset path; `trust_remote_code` is explicit |
| `hfids/...` | timm `IterableImageDataset` with streaming HF reader | Supports `download`, `batch_size`, `num_samples`, `seed`, and `repeats` |
| `tfds/...` | timm `IterableImageDataset` via TensorFlow Datasets | Supports iterable training shuffle/repeat behavior |
| `wds/...` | timm `IterableImageDataset` via WebDataset | Use iterable-aware loader assumptions |

## Split Search Behavior

For folder-style datasets, `search_split=True` lets a user pass a dataset root and split separately. If `root/split` exists, timm uses that child directory. Split synonyms are also searched:

- Train-like: `train`, `training`
- Eval-like: `val`, `valid`, `validation`, `eval`, `evaluation`

Disable `search_split` when `root` already points at the exact image directory or when a reader interprets split strings itself.

## Dataset Wrappers

### `ImageDataset`

`ImageDataset` wraps a reader that returns image handles and targets. It opens images with PIL unless `load_bytes=True`, converts image mode with `input_img_mode` such as `RGB` or `L`, applies `transform`, then applies `target_transform`. Missing targets become `-1`. It retries consecutive image IO failures before raising a runtime error.

### `IterableImageDataset`

`IterableImageDataset` is used for TFDS, WDS, and streaming HF-style readers. It forwards `is_training`, `batch_size`, `num_samples`, `seed`, `repeats`, `download`, and optional input/target key names to the reader. `create_loader` calls `set_loader_cfg(num_workers=...)` before worker processes start so sample estimates remain consistent.

## Class Maps

Use `class_map` when class directory names or dataset labels need a fixed index mapping.

- A dict maps class name to integer index directly.
- A `.txt` file maps one class name per line, with line number as the index.
- A `.pkl` file must unpickle to a plain dict; unsupported globals are blocked by a restricted unpickler.
- Relative class map paths are resolved under the dataset root if not found from the current process.

Common failure signals are `Cannot locate specified class map file`, `Unsupported class map file extension`, or labels missing from the map.

## ImageNet Metadata

Use `ImageNetInfo(subset='imagenet-1k')` to map class indices to synsets and descriptions. Supported normalized subset names include ImageNet-1k, 12k, 21k Google, 21k MIIL, 22k, and 22k Microsoft variants. Use `infer_imagenet_subset(model_or_cfg)` to infer a subset from `num_classes` when possible.

Typical helpers:

```python
from timm.data import ImageNetInfo, infer_imagenet_subset

subset = infer_imagenet_subset(model) or 'imagenet-1k'
info = ImageNetInfo(subset)
label = info.index_to_label_name(0)
description = info.index_to_description(0, detailed=True)
```

## Mixup and Random Erasing Objects

- `Mixup` applies mixup/cutmix after a normal loader returns image tensors and integer labels. Its `mode` can be `batch`, `pair`, or `elem`.
- `FastCollateMixup` is used as a collate function when prefetching and applying mixup in the fast-collate path.
- `NaFlexMixup` is the NaFlex-specific variant; it does not use the standard `mode` and is designed for variable-size patch batches.
- Random erasing can be configured through `create_transform`/`create_loader` with `re_prob`, `re_mode`, `re_count`, and split controls. With a prefetcher, random erasing can run in the prefetch path.
