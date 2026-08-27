# Data and transform reference

This reference covers Jittor's dataset, dataloader, built-in image datasets, and transform layout contracts. It is self-contained and does not require the source checkout.

## Imports and ownership

```python
import jittor as jt
from jittor.dataset import Dataset, DataLoader, TensorDataset, ImageFolder, MNIST, CIFAR10, CIFAR100, VOC
import jittor.transform as T
```

Use this sub-skill for data construction and model input preparation. Use the training sub-skill for optimizer loops, and the core API sub-skill for `Var`/autograd fundamentals.

## Dataset and DataLoader contracts

| API | Verified call shape | Contract and gotchas |
| --- | --- | --- |
| `Dataset` | `Dataset(batch_size=16, shuffle=False, drop_last=False, num_workers=0, buffer_size=512*1024*1024, stop_grad=True, keep_numpy_array=False, endless=False)` | Base iterable. Subclass it, implement `__getitem__(index)`, and call `set_attrs(total_len=sample_count, ...)`. Base `__len__` reports batch count after `total_len`/`batch_size`; for sample count, track `total_len` explicitly. |
| `dataset.set_attrs` | `dataset.set_attrs(batch_size=..., shuffle=..., num_workers=...)` | Mutates the existing dataset and returns it. It only accepts attributes already present on that dataset object; define custom attributes before setting them. |
| `DataLoader` | `DataLoader(dataset, *args, **kwargs)` | Thin wrapper around `dataset.set_attrs(...)`, not a separate PyTorch-style loader object. The returned object is the same dataset configured for iteration. |
| `TensorDataset` | `TensorDataset(*vars_or_arrays)` | Alias of `VarDataset`. Accepts one or more same-length tensors/arrays, disables multiprocessing workers, and yields aligned samples. Good no-download smoke choice. |
| `ImageFolder` | `ImageFolder(root, transform=None)` | Classification folder reader. Expects `root/class_name/image_file` layout; class names and files are sorted, labels are integer indices, and common image extensions are scanned recursively. |

### Collation and conversion

- `Dataset.collate_batch` stacks `jt.Var`, NumPy arrays, images, numeric scalars, tuples/lists, and dictionaries recursively.
- Unless `keep_numpy_array=True`, `Dataset.to_jittor` converts stacked NumPy arrays to `jt.Var` and applies `stop_grad()` when `stop_grad=True`.
- Raw PIL images collate through `np.array(image)` before Jittor conversion, producing HWC image batches. Most models expect NCHW, so use transforms to produce CHW arrays before batching.
- Strings are kept as Python strings and are not converted to `jt.Var`.
- Multiprocessing is optional; start with `num_workers=0` for debuggability and for no-download smoke scripts.

## Built-in datasets and download behavior

| Dataset | Constructor details | Data and output behavior | Download/cache guidance |
| --- | --- | --- | --- |
| `MNIST` | `MNIST(data_root=..., train=True, download=True, batch_size=16, shuffle=False, transform=None)` | Reads four gzip files. Converts each grayscale image to RGB PIL, applies `transform` if provided, then returns `T.to_tensor(img)` and label. The default output is CHW float data with three channels. | `download=True` fetches required gzip files into the selected root. For offline runs, pass an explicit `data_root` with the files already present and set `download=False`. |
| `CIFAR10` | `CIFAR10(root=..., train=True, transform=None, target_transform=None, download=True)` | Verifies the extracted CIFAR-10 Python batch files, loads images internally as HWC, returns a PIL image plus target; transform decides final layout. | `download=True` downloads and extracts the archive when integrity checks fail. For smoke tests, use synthetic data or an explicit prepared `root` with `download=False`. |
| `CIFAR100` | `CIFAR100(root=..., train=True, transform=None, target_transform=None, download=True)` | Subclass of `CIFAR10` with CIFAR-100 file names and metadata. Same HWC-to-PIL sample behavior. | Same as CIFAR-10: distinguish missing files, failed network transfer, and failed integrity checks. |
| `VOC` | `VOC(data_root=..., split="train")` | Expects a local Pascal VOC-style segmentation tree with `ImageSets/Segmentation`, `JPEGImages`, and `SegmentationClass`. Returns resized image as CHW NumPy array and label mask as NumPy array. | No automatic download path is provided by the public constructor; prepare data explicitly. |
| `ImageFolder` | `ImageFolder(root, transform=None)` | Reads RGB images from class subdirectories. Without a transform, batches are HWC image tensors; with `ImageNormalize`/`ToTensor`, batches become CHW. | Does not download; validate local layout before iterating. |

Do not rely on the default Jittor user data cache in deterministic tests. Pass an explicit dataset root controlled by the task, or avoid the dataset constructor entirely and use `TensorDataset`.

## Transform layout expectations

Jittor transforms are close to torchvision-style image transforms, but the PIL/NumPy layout contract is easy to misuse.

| Transform surface | Input expectation | Output shape/layout |
| --- | --- | --- |
| PIL spatial/color transforms (`Resize`, `CenterCrop`, `RandomCrop`, flips, `ColorJitter`, `RandomPerspective`) | Prefer `PIL.Image`. If passed a non-PIL value, many wrappers call `to_pil_image`, which expects HWC data. | Usually a `PIL.Image`, unless the transform explicitly returns an array. |
| `T.ToTensor()` / `T.to_tensor` on PIL | PIL image. | NumPy array in CHW layout, scaled to float `[0, 1]` for uint8 images. |
| `T.ToTensor()` / `T.to_tensor` on NumPy | 2D or 3D NumPy array. For 3D arrays, Jittor preserves the given axis order. | Same axis order as input; uint8 is converted to float `[0, 1]`. Do not assume HWC NumPy becomes CHW. |
| `T.ToPILImage()` / `T.to_pil_image` | NumPy array or `jt.Var` in HWC layout, with 1/2/3/4 supported channels. | `PIL.Image`. To convert CHW data, transpose it to HWC first. |
| `T.ImageNormalize(mean, std)` on PIL | RGB PIL image. | CHW normalized NumPy array. |
| `T.ImageNormalize(mean, std)` on NumPy/Var | CHW or batch-NCHW data. | Same layout, normalized by channel. HWC data is not the intended input. |
| `T.Compose([...])` | Runs each transform in sequence. | Output is whatever the last transform returns. |

Recommended image-classification transform order:

```python
transform = T.Compose([
    T.Resize((224, 224)),          # PIL -> PIL
    T.RandomHorizontalFlip(0.5),   # PIL -> PIL
    T.ToTensor(),                  # PIL -> CHW float NumPy
    T.ImageNormalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
```

A shorter Jittor pattern also works for PIL inputs because `ImageNormalize` can both convert RGB PIL to CHW and normalize it:

```python
transform = T.Compose([
    T.Resize((224, 224)),
    T.ImageNormalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])
```

Avoid placing PIL-only transforms after `ToTensor()` or `ImageNormalize()` unless you deliberately transpose CHW data back to HWC first.

## No-network data smoke pattern

Use synthetic images and `TensorDataset` when the goal is to verify that Jittor, transforms, batching, and model input shapes work without touching external data:

```python
import numpy as np
import jittor as jt
from PIL import Image
from jittor.dataset import TensorDataset
import jittor.transform as T

pipeline = T.Compose([T.Resize((32, 32)), T.ToTensor(), T.ImageNormalize([0.5]*3, [0.5]*3)])
arr = np.zeros((36, 34, 3), dtype=np.uint8)
chw = pipeline(Image.fromarray(arr, "RGB"))
images = jt.array(np.stack([chw, chw]).astype("float32"))
labels = jt.array(np.array([0, 1], dtype="int32"))
dataset = TensorDataset(images, labels).set_attrs(batch_size=1, shuffle=False, num_workers=0)
for x, y in dataset:
    assert list(x.shape)[1:] == [3, 32, 32]
    break
```

For a ready-to-run version that also checks a model-zoo constructor, use the bundled smoke script.
