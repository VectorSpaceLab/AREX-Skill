---
name: dataset-loading
description: "Load, inspect, and validate MedMNIST 2D and 3D datasets from local
  NPZ files with the standard split, size, metadata, and transform contracts."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# MedMNIST dataset loading

Use this sub-skill for installing or importing MedMNIST, choosing one of the 18
registered subsets, reading `INFO`, loading a local NPZ, selecting `train`,
`val`, or `test`, using MedMNIST+ resolutions, controlling `mmap_mode`,
converting grayscale images to RGB, applying transforms, and consuming the
standardized arrays without PyTorch.

## Route before acting

- Read [the API reference](references/api-reference.md) before choosing a
  class, split, size, or expected return type.
- Read [the data format reference](references/data-formats.md) before opening
  an NPZ directly or building a fixture.
- Follow [the normal workflows](references/workflows.md) for installation,
  metadata inspection, local loading, and deterministic smoke checks.
- Use [the no-PyTorch guide](references/no-pytorch.md) and the bundled
  [NPZ inspection script](scripts/npz_without_pytorch.py) when torch is not
  wanted.
- Use [troubleshooting](references/troubleshooting.md) for missing roots/files,
  invalid arguments, broken NPZ keys, and download recovery.

Do not use this sub-skill for evaluator metrics, result CSV parsing/naming,
figure export, or montage generation. Route those requests to the sibling
[`evaluation-and-export`](../evaluation-and-export/SKILL.md) sub-skill. Do not
teach model training, bulk downloads, or clinical decisions.

## Operating procedure

1. **Install or verify the package.** Run `python -m pip install medmnist` in
   the caller's selected environment, then verify with:
   `python -c "import medmnist; print(medmnist.__version__)"`. The expected
   inspected release is `3.0.2`. Do not silently install a second environment.
2. **Choose a registry flag.** Inspect `medmnist.INFO` and select an exact
   lowercase flag such as `pathmnist` or `organmnist3d`; do not infer a class
   from a filename alone. There are 18 registry entries, with 12 2D and 6 3D
   subsets. See the complete table in [the API reference](references/api-reference.md).
3. **Inspect metadata before interpreting labels.** Use
   `INFO[flag]["task"]`, `INFO[flag]["label"]`, `n_channels`, `n_samples`, and
   `license`. Labels are not uniformly multiclass: tasks include binary,
   multiclass, multilabel, and ordinal regression.
4. **Create the root explicitly.** `root` must be an existing directory. For a
   controlled run use `root = Path("./medmnist-data")` and call
   `root.mkdir(parents=True, exist_ok=True)` before construction. The package
   does not create an arbitrary missing caller-provided root.
5. **Load one split and one size.** Construct the class named in `INFO` with a
   required `split` of `train`, `val`, or `test`. `size=None` and `size=28`
   select the 28 variant. 2D accepts 28, 64, 128, 224; 3D accepts 28, 64.
   Dataset files are named `<flag>.npz` for 28 and `<flag>_<size>.npz` for
   larger variants.
6. **Check one sample before downstream use.** For 2D, expect a PIL image and
   an integer NumPy target. For 3D, expect a normalized channel-first NumPy
   array and an integer NumPy target. Check `len(dataset)`, `dataset.imgs.shape`,
   `dataset.labels.shape`, and the first sample's type/shape.
7. **Use local files by default.** `download=False` is the safe default. To use
   automatic download, pass `download=True` only with an existing writable
   root and an intentional network approval; the official source is Zenodo.
   For offline checks, use a local NPZ or the bundled no-PyTorch fixture mode.
8. **Use `mmap_mode` deliberately.** The constructor forwards the value to
   `numpy.load`; `mmap_mode="r"` is useful for large arrays. Check the resulting
   array type and actual access behavior rather than assuming every NPZ member
   is a live `memmap`.
9. **Keep labels task-aware.** Every standard label array is `N x L`. Preserve
   the target vector and consult `INFO` before converting it to a scalar,
   one-hot vector, threshold, or ordinal value.

## Canonical commands

List registry entries and metadata without downloading:

```bash
python - <<'PY'
import medmnist
from medmnist.info import INFO
print(medmnist.__version__)
print(len(INFO), sorted(INFO))
print(INFO["pathmnist"]["task"], INFO["pathmnist"]["n_channels"])
PY
```

Expected output starts with `3.0.2`, then `18`, includes `pathmnist`, and prints
`multi-class 3` for the final line. Load an already-present file:

```bash
mkdir -p ./medmnist-data
python - <<'PY'
from medmnist import PathMNIST

ds = PathMNIST(split="train", root="./medmnist-data", size=28,
               download=False, mmap_mode="r")
image, target = ds[0]
print(len(ds), type(image).__name__, image.size, image.mode,
      target.shape, target.dtype)
PY
```

The command succeeds only if `./medmnist-data/pathmnist.npz` exists; otherwise
follow [troubleshooting](references/troubleshooting.md), not a blind retry.

For a no-download synthetic check covering both 2D and 3D return contracts, run
these commands (the fixture is temporary and contains no real medical data):

```bash
python scripts/npz_without_pytorch.py --fixture 2d --split train --size 28 --as-rgb --mmap-mode r
python scripts/npz_without_pytorch.py --fixture 3d --split test --size 28 --as-rgb --mmap-mode r
```

Each command prints the six-key schema, the selected split, `size=28`, and a
sample shape of `(28, 28, 3)` for 2D or `(3, 28, 28, 28)` for 3D, with a target
shape of `(1,)`. See [the script guide](references/no-pytorch.md) for the
expected output and local-NPZ form.

## Return handoff

When handing a loading result to another sub-skill, report: package version;
flag and class; root and exact NPZ filename; split and size; `download` and
`mmap_mode`; NPZ keys and image/label shapes; task and label interpretation;
2D/3D sample type and shape; RGB and transform choices; checks run; and any
missing file, backend, or data-quality limitation. State explicitly when a
synthetic fixture was used instead of official data.
