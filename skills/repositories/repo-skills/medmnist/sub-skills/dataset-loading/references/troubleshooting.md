# Dataset-loading troubleshooting

Use the smallest local recovery first. Do not solve a missing file by silently
downloading a different size or by substituting a real dataset for a fixture.

## Package import or version mismatch

**Symptom:** `import medmnist` prints that required packages are missing, or the
version is not the intended release.

```bash
python -m pip show medmnist
python -c "import medmnist; print(medmnist.__version__)"
python -m pip install --upgrade medmnist
```

Use the same `python` executable for pip and the smoke test. The inspected
facts are Python 3.11, MedMNIST 3.0.2, and successful CPU torch/torchvision
imports. No CUDA-specific MedMNIST path is required. If the package catches an
import error while initializing, inspect the first dependency error rather
than attempting to import a class repeatedly.

## Missing root directory

**Symptom:** constructor raises:

```text
Failed to setup the default `root` directory. Please specify and create the `root` directory manually.
```

The constructor requires an existing root. Create it and pass it explicitly:

```bash
mkdir -p ./medmnist-data
python - <<'PY'
from pathlib import Path
root = Path("./medmnist-data")
root.mkdir(parents=True, exist_ok=True)
print(root.resolve(), root.is_dir())
PY
```

Do not use a file path as `root`, and do not assume a missing custom root will be
created. The default `~/.medmnist` may be unavailable in a restricted runtime;
an explicit writable project-local root is clearer.

## Dataset NPZ not found

**Symptom:** constructor raises `RuntimeError` beginning `Dataset not found`.

Check the exact expected filename before choosing a recovery:

```bash
python - <<'PY'
from pathlib import Path
flag, size = "pathmnist", 64
name = f"{flag}{'' if size in (None, 28) else '_' + str(size)}.npz"
path = Path("./medmnist-data") / name
print(path, path.exists())
PY
```

With `download=False`, this is an offline failure by design. For an approved
network operation, pass `download=True` and use an existing writable root. The
package uses the per-size Zenodo URL and MD5 from `INFO`. If the download fails,
follow the error's manual steps: obtain the exact file from the official Zenodo
source, verify its optional MD5, and place it under the root with the exact
name. A local file with the wrong size suffix is not a valid substitute.

For offline loader plumbing, use:

```bash
python scripts/npz_without_pytorch.py --fixture 2d --split train --size 28
```

This never downloads and is not a replacement for official data.

## Invalid split

**Symptom:** a construction with `split="validation"`, a typo, or `None` raises
`ValueError`.

Use exactly one of `train`, `val`, and `test`:

```python
assert split in {"train", "val", "test"}
```

The NPZ member names use `val_images` and `val_labels`, not
`validation_images`/`validation_labels`.

## Invalid size or wrong file

**Symptom:** an assertion/validation error occurs for a requested size.

Use `None` or `28` for the base file. 2D classes support `[28, 64, 128, 224]`;
3D classes support `[28, 64]`. The selected file suffix must match:

```text
size=None or 28  -> <flag>.npz
size=64          -> <flag>_64.npz
size=128         -> <flag>_128.npz  (2D only)
size=224         -> <flag>_224.npz  (2D only)
```

For the bundled checker, `--size` validates the stored spatial dimensions and
never resizes. A clear mismatch message means choose the matching file or
remove the wrong size assertion; it does not mean that the array can be
silently resampled.

## Corrupt or nonstandard NPZ schema

**Symptom:** direct NumPy loading fails, or a key is missing/mismatched.

Inspect the archive without pickle:

```bash
python - <<'PY'
import numpy as np
path = "./medmnist-data/pathmnist.npz"
with np.load(path, allow_pickle=False) as z:
    print(z.files)
    for key in z.files:
        print(key, z[key].shape, z[key].dtype)
PY
```

Require all six standard keys and pair each `*_images` with its corresponding
`*_labels`. Labels must be `N x L`; do not repair a missing split by duplicating
another split. Re-acquire the official file or use a deliberately documented
synthetic fixture.

## Unexpected sample type or shape

- 2D without a transform: expect `PIL.Image.Image`, not a tensor; grayscale is
  typically mode `L`, and `as_rgb=True` is mode `RGB`.
- 3D without a transform: expect normalized channel-first NumPy data, not PIL;
  the shape is `(1,D,H,W)` or `(3,D,H,W)`, values generally in `[0,1]`.
- Target: expect integer NumPy data, normally `(1,)`; multilabel datasets have
  multiple columns.

If a transform changes the type, inspect the transform itself. For 3D, a 2D
PIL transform is the wrong input contract.

## mmap surprises

**Symptom:** `mmap_mode="r"` does not produce a `numpy.memmap` instance.

The constructor forwards `mmap_mode` to `numpy.load`, but NPZ members may be
compressed or materialized by NumPy. Treat `mmap_mode` as a requested loading
mode, not a guarantee. Confirm `dataset.imgs.dtype`, shape, and access behavior
on the actual file. Keep the archive/dataset alive while using lazy data.

## Fixture validation failures

The safe script's fixture is grayscale with two samples, all six keys, and
spatial size 28. A successful 2D RGB smoke check is:

```bash
python scripts/npz_without_pytorch.py --fixture 2d --size 28 --as-rgb --mmap-mode r
```

A successful 3D RGB smoke check is:

```bash
python scripts/npz_without_pytorch.py --fixture 3d --size 28 --as-rgb --mmap-mode r
```

For an intentional error, try `--split test --index 2`; it should return a
nonzero exit status and explain the valid range. Use these fixtures only for
loader behavior; they carry no `INFO` semantics, official sample counts, or
clinical meaning.

## Scope boundary

If the request is about evaluator AUC/ACC, standardized result filename
parsing, CSV generation, image/GIF export, or montage behavior, stop here and
route to [`evaluation-and-export`](../../evaluation-and-export/SKILL.md).
