# MedMNIST loading API reference

This reference describes the inspected MedMNIST `3.0.2` API. It is limited to
selection, metadata, construction, and sample access. Evaluation and export
APIs belong to the sibling evaluation sub-skill.

## Imports and registry

```python
import medmnist
from medmnist import PathMNIST
from medmnist.info import INFO, DEFAULT_ROOT, HOMEPAGE
```

`medmnist.INFO` is the authoritative registry. It contains 18 entries:

| Flag | Python class | Kind | Supported sizes |
|---|---|---|---|
| `pathmnist` | `PathMNIST` | 2D | 28, 64, 128, 224 |
| `chestmnist` | `ChestMNIST` | 2D | 28, 64, 128, 224 |
| `dermamnist` | `DermaMNIST` | 2D | 28, 64, 128, 224 |
| `octmnist` | `OCTMNIST` | 2D | 28, 64, 128, 224 |
| `pneumoniamnist` | `PneumoniaMNIST` | 2D | 28, 64, 128, 224 |
| `retinamnist` | `RetinaMNIST` | 2D | 28, 64, 128, 224 |
| `breastmnist` | `BreastMNIST` | 2D | 28, 64, 128, 224 |
| `bloodmnist` | `BloodMNIST` | 2D | 28, 64, 128, 224 |
| `tissuemnist` | `TissueMNIST` | 2D | 28, 64, 128, 224 |
| `organamnist` | `OrganAMNIST` | 2D | 28, 64, 128, 224 |
| `organcmnist` | `OrganCMNIST` | 2D | 28, 64, 128, 224 |
| `organsmnist` | `OrganSMNIST` | 2D | 28, 64, 128, 224 |
| `organmnist3d` | `OrganMNIST3D` | 3D | 28, 64 |
| `nodulemnist3d` | `NoduleMNIST3D` | 3D | 28, 64 |
| `adrenalmnist3d` | `AdrenalMNIST3D` | 3D | 28, 64 |
| `fracturemnist3d` | `FractureMNIST3D` | 3D | 28, 64 |
| `vesselmnist3d` | `VesselMNIST3D` | 3D | 28, 64 |
| `synapsemnist3d` | `SynapseMNIST3D` | 3D | 28, 64 |

The registry key for the adrenal entry is `adrenalmnist3d` (without a space);
the spaced rendering above is only a typographical separator. Prefer this
check when selecting dynamically:

```python
flag = "adrenalmnist3d"
assert flag in INFO
class_name = INFO[flag]["python_class"]
DatasetClass = getattr(medmnist, class_name)
```

The package's `__main__` command can also list the registry:

```bash
python -m medmnist available
python -m medmnist info --flag=pathmnist
```

`INFO[flag]` includes `python_class`, `description`, Zenodo `url`/MD5 fields,
`task`, `label`, `n_channels`, `n_samples`, and `license`. Use the per-entry
`label` mapping rather than assuming class indices have a universal meaning.

## Constructor

All concrete classes use:

```python
MedMNIST(
    split,
    transform=None,
    target_transform=None,
    download=False,
    as_rgb=False,
    root="~/.medmnist",
    size=None,
    mmap_mode=None,
)
```

The installed signature reports the default root as the expanded package
`DEFAULT_ROOT` value. In practice, pass an explicit existing `root` for
reproducible jobs.

| Parameter | Contract |
|---|---|
| `split` | Required exact string: `"train"`, `"val"`, or `"test"`. Other values raise `ValueError`. |
| `transform` | Optional callable. For 2D it receives a PIL image; for 3D it receives the normalized NumPy channel-first array. |
| `target_transform` | Optional callable applied after the target is converted to integer NumPy values. |
| `download` | If true, retrieve the selected file into `root`; default false. No download occurs with false. |
| `as_rgb` | For 2D, grayscale PIL images become RGB. For 3D, one normalized channel is repeated to three channels. |
| `root` | Existing directory containing the NPZ or a writable directory for an approved download. Missing roots raise `RuntimeError`. |
| `size` | `None` or `28` selects 28. 2D additionally supports 64/128/224; 3D additionally supports 64. Unsupported values are rejected. |
| `mmap_mode` | Passed directly to `numpy.load`; use `"r"` for a read-only memory-conscious attempt. |

The larger-size filename is selected by `size_flag`: blank at 28, otherwise
`_<size>`, so `PathMNIST(size=64)` requires `pathmnist_64.npz`.

## Sample contracts

### 2D

`MedMNIST2D.__getitem__(index)` reads the image and target at the same index:

- image is converted to `PIL.Image.Image` with `Image.fromarray`;
- grayscale data is mode `L` unless `as_rgb=True`, which calls `.convert("RGB")`;
- target is `self.labels[index].astype(int)`, normally shape `(1,)`;
- `transform` then receives the PIL image; `target_transform` then receives the
  integer target.

For a grayscale 28 fixture, the untransformed image has `mode == "L"` and
`size == (28, 28)`. With RGB conversion, `mode == "RGB"` and
`numpy.asarray(image).shape == (28, 28, 3)`.

### 3D

`MedMNIST3D.__getitem__(index)` reads a volume and target and computes:

```python
channels = 3 if as_rgb else 1
image = np.stack([raw / 255.0] * channels, axis=0)
```

Thus a grayscale volume with raw shape `(28, 28, 28)` returns a float NumPy
array of shape `(1, 28, 28, 28)` in `[0, 1]`; `as_rgb=True` returns
`(3, 28, 28, 28)`. The target is an integer NumPy array, normally `(1,)`.
There is no PIL conversion for 3D.

## Metadata and length

`len(dataset)` is the first dimension of the selected `*_images` array. The
implementation asserts that this agrees with `INFO[flag]["n_samples"][split]`
for official data. A synthetic fixture must therefore be consumed by a generic
NPZ reader or by a deliberately patched test class, not presented as an
official registry dataset.

Use this metadata probe before data interpretation:

```python
from medmnist.info import INFO
meta = INFO["chestmnist"]
print(meta["task"])
print(meta["n_channels"])
print(meta["n_samples"]["test"])
print(meta["label"])
print(meta["license"])
```

The official data source is Zenodo. The dataset is not intended for clinical
use. DermaMNIST is licensed CC BY-NC 4.0; the other listed MedMNIST datasets
use CC BY 4.0. Check the specific `INFO[flag]["license"]` before redistribution
or a commercial use.
