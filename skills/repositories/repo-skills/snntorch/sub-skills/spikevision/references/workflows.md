# spikevision workflows

> [!WARNING]
> `snntorch.spikevision` is deprecated. If you are starting fresh, use the Tonic-based neuromorphic data workflow instead of this legacy surface.

## 1) Confirm the legacy import surface

Use the bundled helper to confirm the warning and the public classes without downloading any data:

```bash
python scripts/spikevision_introspect.py
```

What this should confirm:
- the import-time deprecation warning is still emitted
- `spikedata` exposes `NMNIST`, `DVSGesture`, and `SHD`
- the legacy helper signatures match the installed package
- the synthetic transform smoke passes

## 2) Pick the wrapper that matches the raw file layout

| Dataset | Use when your local data looks like this | Generated cache | Keep in mind |
| --- | --- | --- | --- |
| `NMNIST` | `Train/<digit>/*.bin` and `Test/<digit>/*.bin` or the matching zip archives | `n_mnist.hdf5` | The constructor expects a dataset directory, not the HDF5 file itself. |
| `DVSGesture` | `DvsGesture/userXX*.aedat` plus label CSVs | `dvs_gesture.hdf5` | The constructor can return metadata when `return_meta=True`. |
| `SHD` | `shd_train.h5` and `shd_test.h5` | `shd.hdf5` | The constructor expects a dataset directory, not the HDF5 file itself. |

### Minimal legacy import pattern

```python
from snntorch.spikevision import spikedata

train_ds = spikedata.NMNIST("dataset/nmnist", train=True, download_and_create=False)
```

Use `download_and_create=False` when you already have the generated cache or when you want to prove that no network access occurs. If the cache file is missing, the constructor will raise instead of downloading.

## 3) Build a safe transform chain

The legacy transform helpers are still useful for inspecting old code or wrapping raw event arrays. Keep the examples synthetic and file-free:

```python
import numpy as np
from torchvision.transforms import Compose
from snntorch.spikevision.neuromorphic_dataset import StandardTransform
from snntorch.spikevision._transforms import Downsample, ToCountFrame, ToTensor, Repeat, toOneHot

# synthetic event rows: time, polarity, x, y
events = np.array([[0, 0, 1, 1], [1000, 1, 2, 3], [1500, 0, 0, 0]])
frames = Compose([
    Downsample([1000, 1, 1, 1]),
    ToCountFrame(T=2, size=[2, 4, 4]),
    ToTensor(),
])(events)

label_tf = StandardTransform(
    transform=lambda x: x,
    target_transform=Compose([Repeat(3), toOneHot(4)]),
)
```

Notes:
- `ToCountFrame` and `ToEventSum` expect event rows with a time column followed by the address dimensions named by `size`.
- `ToChannelHeightWidth` is the SHD-friendly helper when the input has 2 columns and needs to be expanded to 4.
- `toOneHot` is usually fed by `Repeat(...)` so that the label becomes a column vector first.

## 4) Keep downloads out of extraction work

The legacy constructors may try to download or build caches if `download_and_create=True` and the cache file is missing. That is fine in a user’s own environment, but it is not part of this sub-skill’s extraction contract.

For extraction and verification:
- prefer `scripts/spikevision_introspect.py`
- prefer local files already present on disk
- avoid calling `download_url` or `download_and_extract_archive`

## 5) Recommended migration path

If the ask is really “load neuromorphic data in a new project,” route the user to Tonic and treat `spikevision` only as a compatibility bridge.

If the ask is “make an old script work again,” use the legacy wrappers, keep the transforms narrow, and check the troubleshooting guide for constructor quirks.
