# Data-provider workflows

## 1. Synthetic NumPy arrays

Use `SimpleDataProvider` when you already have arrays in memory.

```python
from tf_unet.image_util import SimpleDataProvider

provider = SimpleDataProvider(data, labels)
X, Y = provider(1)
```

Choose the label layout carefully:

- binary mask labels for the two-class path,
- one-hot labels for multi-class workflows.

## 2. Paired TIFF images

Use `ImageDataProvider` when your input comes from paired image and mask files.

```python
from tf_unet.image_util import ImageDataProvider

provider = ImageDataProvider("/path/to/*.tif")
X, Y = provider(1)
```

The synthetic smoke helper shows how to create a temporary pair with the default `.tif` and `_mask.tif` naming convention.

## 3. Toy generators

Use `GrayScaleDataProvider` or `RgbDataProvider` when you want a quick segmentation fixture with no external files.

```python
from tf_unet.image_gen import GrayScaleDataProvider, RgbDataProvider

gray = GrayScaleDataProvider(32, 32, cnt=1, border=5)
rgb = RgbDataProvider(32, 32, cnt=1, border=5)
```

Tips:

- Keep the image size larger than the toy border.
- Use `rectangles=True` when you want a 3-class toy problem.

## 4. Launcher-style external datasets

The external workflows in this package follow simple patterns even when the original data is not present:

- RFI-style HDF5 chunks are read from `data` and `mask`.
- UFIG-style astronomy data reads `image` and the `segmaps/*` channels.
- Ultrasound-style image segmentation expects paired TIFFs.

Use these as format guides for synthetic test fixtures or private datasets.

## 5. Validation strategy

Run `scripts/smoke_data_providers.py` to check that these contracts still behave correctly in the current environment.
