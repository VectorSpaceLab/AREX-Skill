# Dataset-loading workflows

These workflows are local-first and intentionally stop before training,
evaluation, export, or montage generation.

## 1. Install and inventory

Use the active environment selected by the caller:

```bash
python -m pip install medmnist
python - <<'PY'
import medmnist
from medmnist.info import INFO
print("version:", medmnist.__version__)
print("registry entries:", len(INFO))
for flag, meta in INFO.items():
    print(flag, meta["python_class"], meta["task"], meta["n_channels"])
PY
```

The inspected installation reports version `3.0.2` and 18 registry entries. The
package declares NumPy, Pillow, and PyTorch/torchvision among its dependencies;
the direct NPZ workflow in [the no-PyTorch guide](no-pytorch.md) needs only
NumPy (and optionally Pillow for 2D image objects). If import prints the
package's “install the required packages first” message, use the active
environment's `python -m pip`, then re-run the probe.

Choose a flag from the printed registry, then resolve its class rather than
hard-coding a potentially stale mapping:

```bash
python - <<'PY'
import medmnist
from medmnist.info import INFO
flag = "pathmnist"
if flag not in INFO:
    raise SystemExit(f"unknown flag: {flag}; choose one of {sorted(INFO)}")
meta = INFO[flag]
Dataset = getattr(medmnist, meta["python_class"])
print(meta["python_class"], meta["task"], meta["n_channels"])
PY
```

## 2. Inspect metadata and choose a file

Metadata is available without a dataset file:

```bash
python -m medmnist info --flag=pathmnist
```

Read `task`, `label`, `n_channels`, `n_samples`, `license`, and the appropriate
`url`/MD5 entry. The official source is the Zenodo record linked by the
project. DermaMNIST has CC BY-NC 4.0; the other listed subsets have CC BY 4.0.
MedMNIST is not intended for clinical use.

Map a requested size to a filename:

```python
size = None                 # or 28
size = 64                   # MedMNIST+
size_flag = "" if size in (None, 28) else f"_{size}"
filename = f"{flag}{size_flag}.npz"
```

For 2D, accepted sizes are 28/64/128/224. For 3D, accepted sizes are 28/64.
The size changes which preprocessed NPZ is opened; it does not resize an
already-loaded image in the Python constructor. MedMNIST+ preserves the
train/val/test splits and sample indices while using the documented resolution
rules. See [the data-format reference](data-formats.md) for shapes.

## 3. Load an existing local dataset

Always create or verify the root before construction. This example does not
network:

```bash
mkdir -p ./medmnist-data
python - <<'PY'
from medmnist import PathMNIST

root = "./medmnist-data"
dataset = PathMNIST(
    split="val",
    root=root,
    size=28,
    download=False,
    as_rgb=False,
    mmap_mode="r",
)
print(dataset)
print("length:", len(dataset))
print("images:", dataset.imgs.shape, dataset.imgs.dtype)
print("labels:", dataset.labels.shape, dataset.labels.dtype)
image, target = dataset[0]
print(type(image).__name__, image.mode, image.size, target, target.dtype)
PY
```

Expected official data properties are governed by `INFO["pathmnist"]`; the
exact sample count is checked by the library. If the file is not present, the
constructor raises `RuntimeError` and does not fetch it when `download=False`.

To explicitly permit an automatic fetch after verifying network and storage,
use an existing writable root and only the selected size:

```python
from pathlib import Path
from medmnist import PathMNIST
root = Path("./medmnist-data")
root.mkdir(parents=True, exist_ok=True)
val = PathMNIST(split="val", root=str(root), size=64, download=True)
```

The downloader uses the metadata URL and MD5 for that size. If it fails, follow
[troubleshooting](troubleshooting.md) and manually place the exact Zenodo NPZ;
do not change the filename to make a different size appear valid.

## 4. Check 2D and 3D return contracts

Use a small number of reads before a long job:

```python
from medmnist import PathMNIST, OrganMNIST3D

# Existing official files are required for these calls.
ds2 = PathMNIST(split="train", root="./medmnist-data", size=28)
img2, y2 = ds2[0]
assert img2.size == (28, 28)
assert y2.dtype.kind in "iu"

ds3 = OrganMNIST3D(split="train", root="./medmnist-data", size=28, as_rgb=True)
img3, y3 = ds3[0]
assert img3.shape == (3, 28, 28, 28)
assert 0.0 <= float(img3.min()) <= float(img3.max()) <= 1.0
assert y3.dtype.kind in "iu"
```

Use [the bundled script](../scripts/npz_without_pytorch.py) instead when
official files are unavailable. Its `--fixture 2d` and `--fixture 3d` modes
make no network request and are suitable for validating size, RGB, mmap, and
shape plumbing.

## 5. Apply transforms without changing the source contract

For 2D, a transform receives a PIL image:

```python
import numpy as np
from PIL import Image

def to_numpy(image: Image.Image):
    return np.asarray(image)

ds = PathMNIST(split="train", root="./medmnist-data", transform=to_numpy)
array, target = ds[0]
```

For 3D, a transform receives a normalized channel-first NumPy array. Keep the
transform's expected input explicit and do not apply a 2D PIL transform to a
3D volume. `target_transform` receives the integer NumPy target in both cases.

## 6. Direct no-PyTorch loading

When the package's PyTorch dependency is undesirable, open the six-key NPZ
with NumPy, validate paired lengths, and convert only what the caller needs.
Run:

```bash
python scripts/npz_without_pytorch.py --fixture 2d --split train --size 28 --as-rgb --mmap-mode r
python scripts/npz_without_pytorch.py --fixture 3d --split test --size 28 --as-rgb --mmap-mode r
```

For a caller-owned file:

```bash
python scripts/npz_without_pytorch.py \
  --npz ./medmnist-data/pathmnist.npz --kind 2d \
  --split val --size 28 --index 0 --mmap-mode r
```

The script never calls a downloader. See [no-pytorch.md](no-pytorch.md) for
its validation behavior and output interpretation.
