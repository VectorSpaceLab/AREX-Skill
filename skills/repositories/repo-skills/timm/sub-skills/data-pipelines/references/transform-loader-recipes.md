# Transform and Loader Recipes

## Model-Aligned Eval Transform

Use this for validation or single-image inference preprocessing:

```python
import timm
from timm.data import create_transform, resolve_data_config

model = timm.create_model('resnet50', pretrained=False)
data_config = resolve_data_config(model=model)
transform = create_transform(**data_config)
```

Why this shape matters:

- `input_size` controls channel count and target height/width.
- `interpolation`, `crop_pct`, and `crop_mode` control resize/crop behavior.
- `mean` and `std` must match the model's pretrained recipe for reliable accuracy.

If a task overrides input size, keep the rest of the pretrained config unless there is a reason to change it:

```python
data_config = resolve_data_config(args={'input_size': (3, 384, 384)}, model=model)
transform = create_transform(**data_config)
```

## Training Transform Without a Dataset

Use direct transforms when the caller owns image loading:

```python
train_transform = create_transform(
    **data_config,
    is_training=True,
    scale=(0.08, 1.0),
    ratio=(3 / 4, 4 / 3),
    hflip=0.5,
    color_jitter=0.4,
    auto_augment='rand-m9-mstd0.5-inc1',
    re_prob=0.25,
    re_mode='pixel',
    re_count=1,
)
```

Set `no_aug=True` for a training-shaped transform with augmentation disabled during debugging.

## Folder Dataset and CPU-Safe Eval Loader

`create_loader` defaults to `device=torch.device('cuda')` when `use_prefetcher=True`. On CPU-only machines, explicitly set `device` or disable the prefetcher.

```python
import torch
from timm.data import create_dataset, create_loader, resolve_data_config

dataset = create_dataset(
    name='',
    root='dataset-root',
    split='validation',
    search_split=True,
)
loader = create_loader(
    dataset,
    **data_config,
    batch_size=32,
    is_training=False,
    num_workers=4,
    use_prefetcher=True,
    device=torch.device('cpu'),
    img_dtype=torch.float32,
)
```

Use `use_prefetcher=False` when a downstream pipeline expects a plain PyTorch `DataLoader` that yields tensors already normalized by the transform.

## Training Loader With Mixup

For standard non-NaFlex training, choose one of two mixup paths:

```python
from timm.data import Mixup, FastCollateMixup, create_loader

mixup_args = dict(
    mixup_alpha=0.8,
    cutmix_alpha=1.0,
    prob=1.0,
    switch_prob=0.5,
    mode='batch',
    label_smoothing=0.1,
    num_classes=1000,
)

# Path A: use a normal loader and apply mixup in the training step.
mixup_fn = Mixup(**mixup_args)
loader = create_loader(dataset, **data_config, batch_size=128, is_training=True, use_prefetcher=False)

# Path B: use fast collate mixup with a prefetcher.
collate_fn = FastCollateMixup(**mixup_args)
loader = create_loader(dataset, **data_config, batch_size=128, is_training=True, collate_fn=collate_fn)
```

When mixup is active, training losses usually need soft-label handling. Route loss decisions to the training-workflows sub-skill.

## Random Erasing Choices

Random erasing is part of `create_transform` and `create_loader` arguments:

- `re_prob=0` disables random erasing.
- `re_mode='const'` uses constant fill; `re_mode='pixel'` uses random pixel values.
- `re_count` is the number of regions.
- `re_split=True` applies erasing only to the augmented half/split when using augmentation splits.
- With a prefetcher, erasing can happen in the prefetch path after tensors are moved to the target device.

## Iterable Dataset Loader Notes

For `hfids/...`, `tfds/...`, and `wds/...` datasets:

- `create_dataset` returns `IterableImageDataset`.
- `is_training=True`, `batch_size`, `num_samples`, `seed`, and `repeats` are meaningful reader hints.
- `create_loader` does not shuffle with a sampler for iterable datasets.
- Distributed repeat augmentation is not supported for iterable datasets in `create_loader`.

## NaFlex Transform-Only Probe

NaFlex transforms output patch dictionaries instead of ordinary image tensors when `patchify=True`:

```python
from timm.data import create_transform

naflex_eval_transform = create_transform(
    **data_config,
    naflex=True,
    patch_size=16,
    max_seq_len=576,
    patchify=True,
    patchify_channels_last=True,
)
```

Use this when a task needs to inspect or manually apply NaFlex preprocessing without constructing a loader.

## NaFlex Loader Recipe

NaFlex loader construction is separate from standard `create_loader`:

```python
import torch
from timm.data import create_naflex_loader

loader = create_naflex_loader(
    dataset,
    patch_size=16,
    train_seq_lens=(128, 256, 576, 784, 1024),
    max_seq_len=576,
    batch_size=64,
    is_training=True,
    re_prob=0.25,
    use_prefetcher=True,
    device=torch.device('cuda'),
    patchify_channels_last=True,
)
```

Important NaFlex constraints:

- Use a NaFlex-compatible model or a model created with a NaFlex conversion option from the model-library sub-skill.
- Training mode wraps map-style datasets in `NaFlexMapDatasetWrapper`; iterable dataset support is marked as WIP.
- `train_seq_lens` changes the per-batch sequence length; the loader derives dynamic batch size from max tokens per batch.
- Validation uses a fixed `max_seq_len` and `NaFlexCollator`.
- `patch_size_choices` and `patch_size_choice_probs` must have matching lengths when variable patch sizes are enabled.
- `patchify_channels_last=True` is the default NaFlex flat patch layout; set it to `False` for channels-first flat patch layouts expected by some integrations.

## Loader Argument Decision Table

| Decision | Default | Change when |
| --- | --- | --- |
| `use_prefetcher=True` | Moves normalization/device transfer into prefetcher | Set `False` for plain CPU dataloading or custom device transfer |
| `device=torch.device('cuda')` | CUDA target for prefetcher | Set CPU explicitly on CPU-only systems |
| `img_dtype=torch.float32` | Full precision image tensor | Use `torch.float16`/`bfloat16` only when model and device path support it |
| `pin_memory=False` in `create_loader` | No pinned host memory by default | Enable for GPU training/eval input throughput |
| `persistent_workers=True` | Keep workers alive | Disable when debugging worker startup or using `num_workers=0` in older environments |
| `worker_seeding='all'` | Seed worker randomness broadly | Change only when reproducing a specific external seeding policy |
| `distributed=False` | No distributed sampler | Enable for DDP; eval gets ordered distributed sampling |
| `use_multi_epochs_loader=False` | Normal DataLoader lifecycle | Enable to reuse worker process state across epochs |
