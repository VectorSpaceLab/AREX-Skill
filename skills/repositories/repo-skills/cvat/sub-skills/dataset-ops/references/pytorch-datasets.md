# CVAT SDK datasets and PyTorch adapter

CVAT SDK includes dataset helpers for reading task/project media and annotations, and an optional PyTorch adapter for ML workflows.

## Install

Base dataset package:

```bash
pip install cvat-sdk
```

PyTorch adapter:

```bash
pip install "cvat-sdk[pytorch]"
```

The PyTorch extra installs Torch/TorchVision/scikit-image and can be large or backend-specific. Do not install it merely for ordinary import/export automation.

## `cvat_sdk.datasets`

The base datasets layer exposes:

- `TaskDataset`
- `FrameAnnotations`
- `MediaElement`
- `MediaDownloadPolicy`
- `Sample`
- `UnsupportedDatasetError`
- `UpdatePolicy`

Use this layer when you need SDK-managed task samples without constructing a Torch dataset.

## `cvat_sdk.pytorch`

The PyTorch adapter exposes:

- `TaskVisionDataset`
- `ProjectVisionDataset`
- `Target`
- `ExtractBoundingBoxes`
- `ExtractInstanceMasks`
- `ExtractSingleLabelIndex`
- `LabeledBoxes`
- `LabeledMasks`
- `UpdatePolicy` compatibility imports

Example:

```python
from cvat_sdk import make_client
from cvat_sdk.pytorch import ProjectVisionDataset, ExtractSingleLabelIndex

with make_client("https://cvat.example.com", access_token=token) as client:
    dataset = ProjectVisionDataset(
        client,
        project_id=12345,
        include_subsets=["Validation"],
        target_transform=ExtractSingleLabelIndex(),
    )
    image, target = dataset[0]
```

## Sample shape

For vision datasets, indexing returns `(image, target)`:

- `image`: a `PIL.Image.Image`.
- `target.annotations.tags`: image-level tag annotations.
- `target.annotations.shapes`: shape annotations for the frame.
- `target.label_id_to_index`: mapping from CVAT server label ids to stable ML label indices.
- `target.image_size`: `(width, height)`.

Track annotations are not exposed like regular frame shapes. Video data support is limited; confirm the adapter supports the target task before relying on it.

## Transforms

Dataset constructors accept torchvision-like transform parameters:

- `transforms(image, target) -> (image, target)`
- `transform(image) -> image`
- `target_transform(target) -> target`

Do not pass `transforms` together with `transform` or `target_transform`.

## Label indices

By default, labels are assigned deterministic indices based on server labels. For reproducible ML training across projects, supply `label_name_to_index` with every label name:

```python
label_name_to_index = {"car": 0, "person": 1}
dataset = ProjectVisionDataset(client, 123, label_name_to_index=label_name_to_index)
```

If a label is missing from the mapping, construction should fail; fix the mapping rather than letting classes shift.

## Caching

Datasets cache media/annotations locally. Default policy is `UpdatePolicy.IF_MISSING_OR_STALE`; `UpdatePolicy.NEVER` refuses network refreshes and fails if necessary data is missing. Use `Client(Config(cache_dir=...))` to control cache location.

## Troubleshooting

- `ModuleNotFoundError: torch`: install `cvat-sdk[pytorch]` or avoid the PyTorch adapter.
- `UnsupportedDatasetError`: task media/annotation layout is unsupported by the adapter; use dataset export instead.
- Slow construction: cache is missing/stale or project has many tasks; use subsets/task filters and cache policy.
- Wrong label indices: supply `label_name_to_index` explicitly.
- Network calls after construction: construction populates/validates cache; after construction, dataset indexing should rely on cached data.
