# MedMNIST NPZ data formats

Use this reference when inspecting an NPZ directly, preparing a safe synthetic
fixture, or checking that a local file is suitable for a loader. The standard
MedMNIST distribution is an NPZ, not a directory of per-image files.

## File naming and keys

For a registry flag `<flag>`:

- 28-size data is `<flag>.npz`;
- MedMNIST+ data is `<flag>_64.npz`, `<flag>_128.npz`, or
  `<flag>_224.npz` for supported 2D sizes;
- 3D has `<flag>.npz` and `<flag>_64.npz`.

Every standard file contains exactly these six required member names:

```text
train_images  train_labels
val_images    val_labels
test_images   test_labels
```

Inspect keys without importing the PyTorch dataset classes:

```python
from pathlib import Path
import numpy as np

path = Path("./medmnist-data/pathmnist.npz")
with np.load(path, mmap_mode="r") as archive:
    print(sorted(archive.files))
    for split in ("train", "val", "test"):
        images = archive[f"{split}_images"]
        labels = archive[f"{split}_labels"]
        print(split, images.shape, images.dtype, labels.shape, labels.dtype)
```

`np.load` returns an `NpzFile` context manager. Keep it open while accessing
members, or copy the arrays before leaving the context. The bundled
[`npz_without_pytorch.py`](../scripts/npz_without_pytorch.py) performs this
validation and sample conversion without downloading.

## Image and label shapes

The first dimension is always the sample count `N`, and each image/label pair
must have the same `N`:

| Data kind | Standard image array | One sample before conversion |
|---|---|---|
| 2D grayscale | `(N, H, W)` | `(H, W)` uint8-like image |
| 2D RGB | `(N, H, W, 3)` | `(H, W, 3)` uint8-like image |
| 3D grayscale volume | `(N, D, H, W)` | `(D, H, W)` uint8-like volume |

At standard size, `H=W=28`; for 3D, `D=H=W=28`. At MedMNIST+ sizes, 2D
uses 64, 128, or 224 and 3D uses 64. Official image values are stored as
integer pixel values and the 3D dataset adapter divides by `255.0` when
returning a sample.

Labels are shape `N x L`, including for a single-label task where `L=1`.
`labels[index].astype(int)` therefore normally returns a one-element integer
NumPy array, not a Python scalar. Do not flatten or threshold labels before
checking `INFO[flag]["task"]`: tasks include `multi-class`, `binary-class`,
`multi-label, binary-class`, and `ordinal-regression`.

Validate a file's structural contract:

```python
required = {
    "train_images", "train_labels", "val_images", "val_labels",
    "test_images", "test_labels",
}
with np.load("./medmnist-data/pathmnist.npz", mmap_mode="r") as archive:
    missing = required.difference(archive.files)
    if missing:
        raise ValueError(f"missing NPZ members: {sorted(missing)}")
    for split in ("train", "val", "test"):
        if archive[f"{split}_images"].shape[0] != archive[f"{split}_labels"].shape[0]:
            raise ValueError(f"sample/label count mismatch in {split}")
```

## Loader conversion rules

`MedMNIST2D.__getitem__` performs `Image.fromarray` and returns a PIL image.
For grayscale data, `as_rgb=False` leaves a one-channel PIL image (normally
mode `L`); `as_rgb=True` calls `convert("RGB")` and returns three channels.
The optional `transform` sees the PIL image.

`MedMNIST3D.__getitem__` does not create a PIL image. It divides the raw volume
by `255.0`, stacks one channel (or repeats three channels when `as_rgb=True`),
and returns channel-first `(1,D,H,W)` or `(3,D,H,W)` float NumPy data. The
optional `transform` sees that normalized array. Targets for both classes are
integer NumPy arrays unless `target_transform` changes them.

`mmap_mode` is forwarded to `np.load`. It is an I/O/memory hint, not a resize
operation and not a guarantee that compressed NPZ members remain `memmap`
objects. A local fixture should still be tested through actual indexing.

## MedMNIST+ resolution rules

The 28 and larger files represent the same subset splits and sample indices;
only the standardized image resolution differs. Two-dimensional data supports
28, 64, 128, and 224. Three-dimensional data supports 28 and 64. MedMNIST+
keeps the dataset-specific preprocessing that defines the standard benchmark,
then resizes or crops to the requested target resolution; it is not a raw
re-download with a different filename.

Important examples from the published rules:

- PathMNIST 224 uses the 224 source images directly; 64 and 128 resize the
  224 source. Chest, Derma, and Breast resize their source images to each
  requested 2D target.
- OCT, Pneumonia, and Retina center-crop to the short edge before resizing;
  Blood center-crops to 200x200; Tissue makes a 2D maximum projection before
  resizing; OrganA/C/S extracts its view's center slice before resizing.
- OrganMNIST3D processes the source bounding boxes to 64 for the plus version;
  NoduleMNIST3D center-crops its standardized 80 volume to 28 and upsamples to
  64; AdrenalMNIST3D center-crops to 64; FractureMNIST3D center-crops to 64;
  VesselMNIST3D voxelizes to 64; and SynapseMNIST3D uses the documented crop
  and 64-voxel target.

These rules explain why `size=64` must select `<flag>_64.npz` rather than
resizing `dataset.imgs` after loading. Consult the source data documentation
when comparing raw-source dimensions; the loader only sees standardized NPZ
arrays.

## Safe synthetic fixtures

A fixture is for loader plumbing only; it is not an official MedMNIST subset and
must not be labeled with a real dataset's clinical meaning. Use small arrays,
keep all six keys, use deterministic values, and store targets as `(N, 1)`:

```python
import numpy as np
from pathlib import Path

root = Path("./synthetic-medmnist")
root.mkdir(exist_ok=True)
images2d = np.arange(2 * 28 * 28, dtype=np.uint8).reshape(2, 28, 28)
labels = np.array([[0], [1]], dtype=np.uint8)
np.savez(root / "fixture2d.npz",
         train_images=images2d, train_labels=labels,
         val_images=images2d, val_labels=labels,
         test_images=images2d, test_labels=labels)
```

For 3D, replace the image shape with `(2, 28, 28, 28)` and use a separate
filename. To test RGB conversion, keep the fixture grayscale and pass
`as_rgb=True`; this exercises the adapter's conversion rather than hiding it
in the fixture. Delete temporary fixtures after the check.
