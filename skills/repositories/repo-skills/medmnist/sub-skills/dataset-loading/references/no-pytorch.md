# No-PyTorch NPZ workflow

MedMNIST files are standard NumPy serialization and can be consumed without
PyTorch. This route is useful for inspection, preprocessing, or a caller's
NumPy-based pipeline. It does not provide training, evaluation, export, or
clinical interpretation.

## Run the bundled checker

The bundled
[`npz_without_pytorch.py`](../scripts/npz_without_pytorch.py) is an executable,
local-only adaptation of the repository's `examples/dataset_without_pytorch.py`
pattern. It imports NumPy and Pillow for 2D image conversion, never imports
`torch` or `medmnist`, never invokes `download_url`, and never writes to a
caller-provided NPZ.

First inspect the interface:

```bash
python scripts/npz_without_pytorch.py --help
```

Expected help includes mutually exclusive `--npz` and `--fixture` inputs,
`--split {train,val,test}`, `--size`, `--as-rgb`, and `--mmap-mode`.

Run safe, temporary fixtures:

```bash
python scripts/npz_without_pytorch.py \
  --fixture 2d --split train --size 28 --as-rgb --mmap-mode r

python scripts/npz_without_pytorch.py \
  --fixture 3d --split test --size 28 --as-rgb --mmap-mode r
```

The 2D run should report a six-key NPZ, `kind: 2d`, `size: 28`, and a sample
such as:

```text
sample: image_type=PIL.Image.Image mode=RGB size=(28, 28) array_shape=(28, 28, 3) dtype=uint8
status: OK (local read only; no download performed)
```

The 3D run should report `kind: 3d` and a sample shape of
`(3, 28, 28, 28)`, a float dtype, a range within `[0, 1]`, and the same status.
The temporary fixture is deleted automatically. It contains no real dataset
content and must not be treated as a MedMNIST registry subset.

## Inspect a caller-provided NPZ

Use the exact local file and state whether it is 2D or 3D when shape inference
could be ambiguous:

```bash
python scripts/npz_without_pytorch.py \
  --npz ./medmnist-data/chestmnist.npz \
  --kind 2d --split val --size 28 --index 0 --mmap-mode r
```

The script validates all six member names, paired sample counts, `N x L` label
shape, supported dimensions, selected size, and index before converting the
sample. `--size` validates the stored spatial size; it deliberately does not
resize. Use the output to confirm:

- 2D conversion is a PIL image, with `as_rgb` changing grayscale `(H,W)` to
  RGB `(H,W,3)`;
- 3D conversion is normalized float NumPy data with channel-first shape
  `(1,D,H,W)` or `(3,D,H,W)`;
- targets are integer NumPy arrays retaining their `(L,)` shape;
- the selected split and the actual archive shapes are visible.

A missing file, bad extension/content, missing key, mismatched count, invalid
shape, unsupported size, or out-of-range index exits nonzero with a
`validation error:` message and a corrective action. It does not fall back to
network access.

## Minimal direct reader

For a custom pipeline, preserve the schema and conversion rules explicitly:

```python
from pathlib import Path
import numpy as np
from PIL import Image

path = Path("./medmnist-data/pathmnist.npz")
with np.load(path, mmap_mode="r", allow_pickle=False) as archive:
    images = archive["train_images"]
    labels = archive["train_labels"]
    if images.shape[0] != labels.shape[0] or labels.ndim != 2:
        raise ValueError("expected paired images and N x L labels")
    image = Image.fromarray(images[0])
    target = labels[0].astype(int)
```

For a 3D volume, replace the PIL conversion with:

```python
volume = images[0].astype(np.float32, copy=False) / 255.0
volume = np.stack([volume], axis=0)  # (1,D,H,W)
```

Repeat the normalized volume three times only when the consumer explicitly
expects RGB-like channels. Do not transpose the standardized 3D output to
channel-last without recording that adaptation.

## Dependency and safety notes

This direct route avoids the package's PyTorch dataset superclass, but 2D PIL
conversion requires Pillow. If only array inspection is needed, omit Pillow
and use `np.asarray(images[index])`. Use `allow_pickle=False` for untrusted
local files. `mmap_mode="r"` is read-only intent; because NPZ archives may be
compressed, confirm memory behavior for the selected file rather than relying
on the `memmap` type alone.
