# Datasets and Data Roots

## Built-in dataset workflow

TorchVision datasets live under `torchvision.datasets` and are ordinary `torch.utils.data.Dataset` implementations with `__getitem__` and `__len__`. Most image-style datasets accept `root`, `transform`, and `target_transform`; many downloadable datasets also accept `download=True`.

Use this sequence:

1. Choose the dataset family by task.
2. Confirm whether the dataset can download itself or requires manual files.
3. Create or validate the root directory layout before using a multi-worker or distributed loader.
4. Attach only sample/target transforms needed for loading; route complex v2 augmentation internals to `../transforms-and-tv-tensors/`.
5. Use a small `DataLoader` or `dataset[0]` smoke check before starting training.

## Dataset families

| Task | Common classes | Notes |
| --- | --- | --- |
| Classification | `ImageFolder`, `FakeData`, `CIFAR10`, `CIFAR100`, `MNIST`, `FashionMNIST`, `ImageNet`, `Flowers102`, `Food101`, `EuroSAT`, `Places365`, `SVHN`, `STL10` | `ImageNet` and some others require pre-arranged files; many small academic datasets can download. |
| Detection / segmentation | `CocoDetection`, `VOCDetection`, `VOCSegmentation`, `Cityscapes`, `Kitti`, `OxfordIIITPet`, `SBDataset`, `WIDERFace` | Annotation formats vary; use `wrap_dataset_for_transforms_v2` when using v2 transforms with boxes/masks. |
| Optical flow | `FlyingChairs`, `FlyingThings3D`, `HD1K`, `KittiFlow`, `Sintel` | Samples include paired images and flow targets; root layouts are dataset-specific. |
| Stereo matching | `CarlaStereo`, `Kitti2012Stereo`, `Kitti2015Stereo`, `CREStereo`, `FallingThingsStereo`, `SceneFlowStereo`, `SintelStereo`, `InStereo2k`, `ETH3DStereo`, `Middlebury2014Stereo` | Many require manually downloaded archives or exact benchmark layouts. |
| Image pairs / captions | `LFWPairs`, `PhotoTour`, `CocoCaptions` | Captions usually need annotation dependencies and files. |
| Video | `UCF101`, `HMDB51`, `Kinetics`, `MovingMNIST` | TorchVision video decoding moved toward TorchCodec; see troubleshooting. |

## `ImageFolder` layout

`ImageFolder` expects one subdirectory per class, with image files below each class directory. Class names are sorted alphabetically to build `class_to_idx`.

```text
root/
  cat/
    cat_000.png
    cat_001.jpg
  dog/
    dog_000.png
```

Useful attributes after construction:

- `dataset.classes`: sorted class names.
- `dataset.class_to_idx`: mapping from class name to integer target.
- `dataset.samples` and `dataset.imgs`: `(path, class_index)` pairs.
- `dataset.targets`: class index for each image.

Accepted image extensions include common JPEG, PNG, BMP, TIFF, PPM/PGM, and WebP suffixes. If a class folder is empty, construction raises unless `allow_empty=True`.

```python
from torchvision.datasets import ImageFolder
from torchvision.transforms import v2

transform = v2.Compose([v2.Resize((32, 32)), v2.ToImage(), v2.ToDtype(torch.float32, scale=True)])
dataset = ImageFolder(root="data/train", transform=transform)
image, target = dataset[0]
```

## `DatasetFolder` and custom datasets

Use `DatasetFolder` when samples are arranged in class folders but are not ordinary images or need a custom loader.

```python
from torchvision.datasets import DatasetFolder

def load_tensor(path):
    return torch.load(path, weights_only=True)

dataset = DatasetFolder(
    root="features/train",
    loader=load_tensor,
    extensions=(".pt",),
)
```

Key rules:

- Pass exactly one of `extensions` or `is_valid_file`.
- Override `find_classes()` in a subclass if class discovery is not one-folder-per-class.
- Override `make_dataset()` only for non-filesystem layouts such as archives or manifests.
- `VisionDataset` is the base class for fully custom datasets; override `__len__` and `__getitem__`.
- `VisionDataset` accepts either combined `transforms` or separate `transform`/`target_transform`, not both.

## `FakeData` for smoke tests

`FakeData(size=..., image_size=(C, H, W), num_classes=..., transform=...)` returns deterministic PIL images per index and integer targets. Use it to test transforms, loaders, and model plumbing without downloads.

```python
from torchvision.datasets import FakeData
from torchvision.transforms import v2

fake = FakeData(size=4, image_size=(3, 32, 32), num_classes=2, transform=v2.ToImage())
image, target = fake[0]
```

## Download and root safety

- Prefer `download=False` in reusable scripts unless the user explicitly asks for network access.
- If using `download=True`, run it once in a single process before distributed training or multi-worker jobs; the built-in download/extract logic is not multi-process safe.
- Keep each dataset in its own root or documented subdirectory to avoid overlapping archive names and partial extraction state.
- If a dataset reports `Dataset not found or corrupted`, check the exact root expected by that dataset rather than assuming every dataset uses an `ImageFolder` layout.
- For manually downloaded datasets such as ImageNet-style or benchmark datasets, use the dataset class docs and source-derived layout messages as the source of truth.

## `wrap_dataset_for_transforms_v2`

Use `torchvision.tv_tensors.wrap_dataset_for_transforms_v2(dataset, target_keys=None)` when a built-in dataset returns PIL images, plain tensors, or legacy annotation structures but the next pipeline uses transforms v2.

What it can wrap:

- Classification datasets such as `ImageFolder`: image-like samples can become transform-friendly image objects while targets remain labels.
- Detection datasets such as `CocoDetection`, `VOCDetection`, and `Kitti`: supported target fields can become dictionaries with `BoundingBoxes`, masks, labels, and related metadata.
- Segmentation datasets such as `VOCSegmentation`: masks can become `Mask` objects.
- Cityscapes semantic/instance targets: supported targets can become masks, labels, and boxes; unsupported target modes should be handled manually.
- Video classification datasets: video tensors can become `Video` objects while labels and metadata remain separate.

Use `target_keys` only for supported detection datasets when you want a subset of target fields. If the wrapper reports that a dataset or target mode is unsupported, write an adapter dataset that returns the sample structure expected by v2 transforms and route detailed TVTensor handling to `../transforms-and-tv-tensors/`.
