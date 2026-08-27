# Data and Configuration

## Purpose

Use this reference for CIFAR-100 data layout, transforms, normalization constants, and the shared settings used by `train.py` and the embedded evaluation loop.

## CIFAR-100 loading path

The training workflow uses torchvision directly:

- training split: `torchvision.datasets.CIFAR100(root='./data', train=True, download=True, transform=...)`
- test split: `torchvision.datasets.CIFAR100(root='./data', train=False, download=True, transform=...)`

The first run may download CIFAR-100 into the local `./data` tree in torchvision's default CIFAR-100 layout.

## Transform pipelines

### Training split

1. `RandomCrop(32, padding=4)`
2. `RandomHorizontalFlip()`
3. `RandomRotation(15)`
4. `ToTensor()`
5. `Normalize(mean, std)`

### Test split

1. `ToTensor()`
2. `Normalize(mean, std)`

## Normalization values

`train.py` and the test loader both use the training statistics from `conf/global_settings.py`:

```text
mean = (0.5070751592371323, 0.48654887331495095, 0.4409178433670343)
std  = (0.2673342858792401, 0.2564384629170883, 0.27615047132568404)
```

The file also contains commented-out test-specific constants, but the active workflow does not use them.

## Shared configuration constants

| Setting | Value | Meaning |
| --- | --- | --- |
| `CHECKPOINT_PATH` | `checkpoint` | Root directory for model weights. |
| `LOG_DIR` | `runs` | Root directory for TensorBoard logs. |
| `EPOCH` | `200` | Total training epochs. |
| `MILESTONES` | `[60, 120, 160]` | Epochs where the learning rate is decayed. |
| `SAVE_EPOCH` | `10` | Regular checkpoint interval. |
| `DATE_FORMAT` | `%A_%d_%B_%Y_%Hh_%Mm_%Ss` | Timestamp format for run folders. |
| `TIME_NOW` | computed at import time | Wall-clock tag used in fresh run folders. |

## Legacy pickle dataset module

`dataset.py` is a reference implementation for the older CIFAR-100 python pickle layout.
It is not wired into the current training path, but it is useful if you need to adapt the repo to another loader.

Important caveats:

- It reads `train` and `test` files directly from the provided path.
- It rebuilds each image by splitting the flat `data` array into `r`, `g`, and `b` planes and stacking them with `numpy.dstack`.
- `CIFAR100Train.__getitem__` and `CIFAR100Test.__getitem__` return `(label, image)` rather than the usual `(image, label)` order.
- `compute_mean_std` expects that legacy label-first layout, so do not reuse it unchanged with a standard PyTorch dataset.

## Practical notes

- The training and test loaders both use `num_workers=4` and `shuffle=True` in the current code.
- If you replace torchvision with the legacy pickle dataset, adjust the item order before plugging it into the training loop.
