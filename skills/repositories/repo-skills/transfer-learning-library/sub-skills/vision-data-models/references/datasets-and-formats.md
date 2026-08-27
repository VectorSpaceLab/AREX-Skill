# TLLib Vision Datasets and Data Formats

This reference is for operating TLLib's installed `tllib.vision.datasets` APIs without relying on the original repository checkout. Dataset downloads are reference-only: prefer already prepared local datasets, and pass `download=False` where the constructor supports it unless the user explicitly accepts network, storage, and license constraints.

## Core local format: `ImageList`

Import:

```python
from tllib.vision.datasets.imagelist import ImageList
```

Constructor:

```python
dataset = ImageList(
    root="/path/to/dataset-root",
    classes=["cat", "dog", "bike"],
    data_list_file="/path/to/train.txt",
    transform=transform,
    target_transform=None,
)
```

Data-list contract:

- Each non-empty line must contain an image path followed by an integer class label.
- The label is the final whitespace-separated token on the line.
- Everything before the final token is treated as the image path, so paths containing spaces can work if the last token is still the label.
- Relative image paths are resolved against `root`; absolute paths are used as-is.
- Labels must be zero-based integers in `[0, len(classes) - 1]`.
- `classes[label]` is the class name for a sample. Keep the `classes` list stable across source/target/train/val lists.
- TLLib's parser does not treat `#` as a comment marker and does not skip malformed blank lines. Keep list files simple and explicit.

Example list file:

```text
amazon/back_pack/img_0001.jpg 0
amazon/bike/img_0002.jpg 1
webcam/back_pack/img_1001.jpg 0
webcam/bike/img_1002.jpg 1
```

Minimal validation command:

```bash
python /path/to/vision-data-models/scripts/validate_imagelist.py \
  --root /path/to/dataset-root \
  --list-file /path/to/train.txt \
  --classes back_pack,bike \
  --check-load 8
```

Use `--class-file classes.txt` instead of `--classes` when the class list is long; one class name per line.

## `MultipleDomainsDataset`

Import:

```python
from tllib.vision.datasets.imagelist import MultipleDomainsDataset
```

Purpose: concatenate several domain datasets while returning each sample plus a domain id.

Contract:

```python
multi = MultipleDomainsDataset(
    domains=[amazon_dataset, webcam_dataset],
    domain_names=["A", "W"],
    domain_ids=[0, 1],
)
image, label, domain_id = multi[0]
```

Notes:

- Each inner dataset item is expected to be tuple-like, so appending `(domain_id,)` is valid.
- Iterable-style datasets are not supported.
- `domain_names` and `domain_ids` must align with `domains` order.

## Classification dataset wrappers

Most classification wrappers subclass `ImageList` or TorchVision-style datasets and expose `samples`, `targets`, `classes`, `class_to_idx`, and sometimes `domains()`.

Common domain adaptation/generalization wrappers:

| Dataset | Typical selector | Notes |
| --- | --- | --- |
| `Office31(root, task, download=True)` | `task` in `A`, `D`, `W` | Classic Amazon/DSLR/Webcam classification domains. Use `download=False` for local-only operation. |
| `OfficeCaltech(root, task, download=False)` | Office-Caltech domains | Local data often required. |
| `OfficeHome(root, task, download=False)` | `Ar`, `Cl`, `Pr`, `Rw` style domains | External dataset/license applies. |
| `VisDA2017(root, task, download=False)` | synthetic/real validation style tasks | Large dataset; avoid implicit download in smoke checks. |
| `DomainNet(root, task, split='train', download=False)` | clipart/infograph/painting/quickdraw/real/sketch | Large dataset and potentially long file lists. |
| `PACS(root, task, split='all', download=True)` | art/cartoon/photo/sketch | Maintainer dataset links have historically been unreliable; prefer local verified data. |
| `ImageNetR(root, task, split='all', download=True)` and `ImageNetSketch(root, task, split='all', download=True)` | ImageNet variant tasks | Usually manually prepared from external sources. |

Digit wrappers:

- `MNIST(root, mode='L', split='train', download=True, **kwargs)`
- `USPS(root, mode='L', split='train', download=True, **kwargs)`
- `SVHN(root, mode='L', download=True, **kwargs)`
- RGB aliases: `MNISTRGB`, `USPSRGB`, `SVHNRGB`

Fine-grained and natural-recognition wrappers include `Aircraft`, `CUB200`, `StanfordCars`, `StanfordDogs`, `COCO70`, `OxfordIIITPets`, `DTD`, `OxfordFlowers102`, `Caltech101`, `PatchCamelyon`, `Retinopathy`, `EuroSAT`, `Resisc45`, `Food101`, `SUN397`, `CIFAR10`, and `CIFAR100`. Many use external data mirrors or upstream dataset licenses; local-only mode is safer than implicit download.

## Partial and open-set wrappers

Imports:

```python
from tllib.vision.datasets.partial import partial, default_partial
from tllib.vision.datasets.openset import open_set, default_open_set
```

Partial-domain adaptation keeps only selected classes but preserves the original label space:

```python
from tllib.vision.datasets import Office31
PartialOffice31 = partial(Office31, ["back_pack", "bike", "calculator"])
dataset = PartialOffice31(root="/data/office31", task="A", download=False)
```

Open-set adaptation remaps public classes to contiguous labels and maps selected private classes to a final `unknown` class:

```python
OpenOffice31 = open_set(
    Office31,
    public_classes=["back_pack", "bike", "calculator"],
    private_classes=["laptop_computer", "monitor"],
)
dataset = OpenOffice31(root="/data/office31", task="W", download=False)
```

Do not mix partial/open-set class mappings across source and target until you verify the resulting `classes`, `class_to_idx`, and labels.

## Regression datasets

Imports:

```python
from tllib.vision.datasets.regression.image_regression import ImageRegression
from tllib.vision.datasets.regression.dsprites import DSprites
from tllib.vision.datasets.regression.mpi3d import MPI3D
```

`ImageRegression` list format is analogous to `ImageList`, but labels are continuous factors rather than one class id:

```python
dataset = ImageRegression(
    root="/path/to/root",
    factors=["scale", "position x", "position y"],
    data_list_file="/path/to/regression.txt",
    transform=transform,
)
```

Use task-specific sub-skills for regression-domain-adaptation losses; this sub-skill only covers the data/model surface.

## Segmentation datasets and lists

Imports:

```python
from tllib.vision.datasets.segmentation.segmentation_list import SegmentationList
from tllib.vision.datasets.segmentation.cityscapes import Cityscapes, FoggyCityscapes
from tllib.vision.datasets.segmentation.gta5 import GTA5
from tllib.vision.datasets.segmentation.synthia import Synthia
```

`SegmentationList` separates image and label lists:

```python
seg = SegmentationList(
    root="/path/to/seg-root",
    classes=["road", "sidewalk", "building"],
    data_list_file="images_train.txt",
    label_list_file="labels_train.txt",
    data_folder="leftImg8bit",
    label_folder="gtFine",
    id_to_train_id={255: 255},
    train_id_to_color=None,
    transforms=seg_transform,
)
```

Operational notes:

- Image and label lists must have the same length and aligned order.
- Segmentation transforms receive and return `(image, label)` pairs.
- Labels should use nearest-neighbor resizing; do not use RGB image interpolation for masks.
- Cityscapes, FoggyCityscapes, GTA5, and Synthia have external licenses and manual preparation requirements.

## Keypoint datasets

Imports include:

```python
from tllib.vision.datasets.keypoint_detection.keypoint_dataset import KeypointDataset, Body16KeypointDataset, Hand21KeypointDataset
from tllib.vision.datasets.keypoint_detection.rendered_hand_pose import RenderedHandPose
from tllib.vision.datasets.keypoint_detection.hand_3d_studio import Hand3DStudio
from tllib.vision.datasets.keypoint_detection.freihand import FreiHand
from tllib.vision.datasets.keypoint_detection.surreal import SURREAL
from tllib.vision.datasets.keypoint_detection.lsp import LSP
from tllib.vision.datasets.keypoint_detection.human36m import Human36M
```

`KeypointDataset` consumes prepared sample metadata and returns images with keypoint heatmaps/metadata. The common image/heatmap size defaults are `image_size=(256, 256)` and `heatmap_size=(64, 64)`. The packaged wrappers may attempt downloads; Human3.6M and many pose datasets require manual agreement with external terms.

## Re-identification datasets

Imports:

```python
from tllib.vision.datasets.reid.market1501 import Market1501
from tllib.vision.datasets.reid.dukemtmc import DukeMTMC
from tllib.vision.datasets.reid.msmt17 import MSMT17
```

Dataset items and metric helpers use tuples shaped like:

```python
(image_path_or_filename, person_id, camera_id)
```

Common train/query/gallery splits are owned by the dataset wrapper. External data licensing is important for Market1501, DukeMTMC, MSMT17, PersonX, and UnrealPerson; do not imply these are freely redistributable just because wrappers exist.

## Broken-link and license policy

TLLib maintainers reported dataset mirror failures in 2023. Some links were restored, while several datasets had no backup at that time, including COCO70, EuroSAT, PACS, PatchCamelyon, CaltechImageNet, Hand3DStudio, LSP, SURREAL, Comic, PersonX, and UnrealPerson.

When operating this skill:

1. Prefer explicit local paths and `download=False`.
2. Treat automatic downloads as best-effort convenience, not a verification dependency.
3. Ask the user to confirm dataset license/terms before download or conversion.
4. Never make network access part of a smoke test.
5. For custom datasets, use `ImageList` or `SegmentationList` with local files instead of changing TLLib source code.
