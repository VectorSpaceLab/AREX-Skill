# Data and model entry points

This reference covers the data-side pieces of anomalib that future agents most often need to choose correctly before they touch a model: datamodules, datasets, dataclasses, split modes, config shapes, and path/layout rules.

## 1) Quick chooser

| Need | Use | Key constructor facts | Common gotchas |
| --- | --- | --- | --- |
| MVTec-style benchmark images | `MVTecAD` | `root`, `category`, batch sizes, `test_split_mode`, `val_split_mode`; `prepare_data()` downloads if the category folder is missing. | The category folder must exist under `root`; defaults are `category="bottle"`, `test_split_mode="from_dir"`, `val_split_mode="same_as_test"`. |
| Custom image folder layout | `Folder` | Requires `name`, `normal_dir`, and `root`; optional `abnormal_dir`, `normal_test_dir`, `mask_dir`, `extensions`. | `normal_dir` is required. Relative subdirectories are resolved against `root`. Masks must match abnormal image stems. |
| Table-driven image layout | `Tabular` | Requires `name` and `samples` (`dict`, `list`, or `DataFrame`); `root` prefixes relative paths; `from_file()` reads csv/parquet/json via pandas. | The table must include `image_path` and at least one of `label_index`, `label`, or `split`. Invalid split labels often surface as `None`/`NaN` later. |
| Inference-only images | `PredictDataset` | Takes a file or directory path, optional transform, and `image_size`. | This is for prediction / inspection, not training. |
| Video anomaly detection | `Avenue` | Uses `root`, `gt_dir`, `clip_length_in_frames`, `frames_between_clips`, `target_frame`. | Requires the `av` extra at runtime through the video clip indexer. |
| RGB-D / depth anomaly detection | `MVTec3D`, `Folder3D`, `ADAM3D` | `MVTec3D` and `ADAM3D` are benchmark-style downloads; `Folder3D` is the custom layout entry point. | Depth layouts need both RGB and depth paths, and segmentation needs mask-path alignment. |

## 2) Public constructors to remember

These are the verified entry points that users are most likely to ask about.

```python
from anomalib.data import (
    ADAM3D,
    Avenue,
    Folder,
    Folder3D,
    MVTec3D,
    MVTecAD,
    PredictDataset,
    ShanghaiTech,
    Tabular,
    UCSDped,
)
```

```python
MVTecAD(root="./datasets/MVTecAD", category="bottle", ...)
Folder(name, normal_dir, root=None, abnormal_dir=None, normal_test_dir=None, mask_dir=None, ...)
Tabular(name, samples, root=None, ...)
PredictDataset(path, transform=None, image_size=(256, 256))
Avenue(root="./datasets/avenue", gt_dir="./datasets/avenue/ground_truth_demo", clip_length_in_frames=2, frames_between_clips=1, target_frame="last", ...)
MVTec3D(root="./datasets/MVTec3D", category="bagel", ...)
Folder3D(name, normal_dir, root, abnormal_dir=None, normal_test_dir=None, mask_dir=None, normal_depth_dir=None, abnormal_depth_dir=None, normal_test_depth_dir=None, ...)
ADAM3D(root="./datasets/ADAM3D", category="1m1", ...)
```

`ShanghaiTech` and `UCSDped` follow the same video-datamodule pattern as `Avenue`: clip length, clip stride, and target-frame selection matter most.

## 3) Dataclasses and batch shapes

The dataclass layer is the contract between datasets, dataloaders, models, and post-processing.

| Modality | Item type | Batch type | Core shapes / fields | Notes |
| --- | --- | --- | --- | --- |
| Image | `ImageItem` | `ImageBatch` | `image`: `(C,H,W)` / `(N,C,H,W)`; `gt_label`, `gt_mask`, `image_path`, `mask_path` | Default `collate_fn` for image datasets. |
| Video | `VideoItem` | `VideoBatch` | `image`: `(T,C,H,W)` / `(N,T,C,H,W)`; `video_path`, `frames`, `last_frame`, `original_image` | Target-frame selection can squeeze temporal dimensions when `clip_length_in_frames=1`. |
| Depth | `DepthItem` | `DepthBatch` | `image`: RGB, `depth_map`: depth tensor, optional `gt_mask` | Depth datasets carry both RGB and depth-path metadata. |
| Inference | `InferenceBatch` | n/a | `pred_score`, `pred_label`, `anomaly_map`, `pred_mask` | Returned by model forward/predict flows. |
| NumPy | `NumpyImageItem`, `NumpyVideoItem` | `NumpyImageBatch`, `NumpyVideoBatch` | Same concepts in array form | Useful for conversion or offline inspection. |

Useful behaviors:

- `Batch.update(...)` mutates a batch in place unless `inplace=False` is used.
- `Batch.collate(...)` builds a batch object from item objects.
- `batch.items` splits a batch back into individual items.
- `.to_numpy()` converts torch-backed items or batches to the NumPy variants.

## 4) Split modes and labels

The data modules use the shared split enums from `anomalib.data.utils.split`:

- `Split.TRAIN`, `Split.VAL`, `Split.TEST`
- `TestSplitMode.NONE`, `FROM_DIR`, `SYNTHETIC`
- `ValSplitMode.NONE`, `SAME_AS_TEST`, `FROM_TRAIN`, `FROM_TEST`, `FROM_DIR`, `SYNTHETIC`

Label values are encoded by `LabelName`:

- `UNKNOWN = -1`
- `NORMAL = 0`
- `ABNORMAL = 1`

Practical implications:

- Image datamodules usually derive validation and test subsets from the source directories and split modes in the base `AnomalibDataModule`.
- Video datamodules do **not** support synthetic test splitting in the same way as image datamodules.
- `Tabular` and `Folder` layouts should keep anomalous samples out of the training split unless the layout intentionally marks them as test-only data.

## 5) Custom layout recipes

### MVTecAD-style directory layout

`MVTecAD` expects the benchmark-style layout rooted at the category directory:

```text
root/
└── category/
    ├── train/
    │   └── good/
    ├── test/
    │   ├── good/
    │   └── defect_name/
    └── ground_truth/
        └── defect_name/
```

Notes:

- Call `prepare_data()` if the dataset is missing locally.
- The class default is `root="./datasets/MVTecAD"` and `category="bottle"`.
- `val_split_mode="same_as_test"` is the default because many anomaly datasets do not have a dedicated validation folder.

### Folder layout

Use `Folder` when you already have the directories you want and do not want to copy data into the benchmark layout.

Minimal classification-style setup:

```python
Folder(
    name="custom",
    root="./datasets/custom",
    normal_dir="train/good",
    abnormal_dir="test/bad",
)
```

Segmentation-style setup:

```python
Folder(
    name="custom",
    root="./datasets/custom",
    normal_dir="train/good",
    abnormal_dir="test/bad",
    normal_test_dir="test/good",
    mask_dir="ground_truth/bad",
)
```

Rules to remember:

- `normal_dir` is required.
- `mask_dir` is only meaningful when anomalous samples have pixel masks.
- `extensions` should be a tuple of dot-prefixed suffixes such as `(".png", ".jpg")`.
- Relative folder arguments are resolved against `root`.

### Tabular layout

Use `Tabular` when the filenames already live somewhere on disk and you want the samples described by a table instead of a folder tree.

Required or useful columns:

- `image_path` is required.
- At least one of `label_index`, `label`, or `split` must be present.
- `mask_path` is optional but needed for segmentation tasks.

Example schema:

```python
samples = {
    "image_path": ["train/good/000.png", "test/bad/001.png"],
    "label_index": [0, 1],
    "mask_path": ["", "ground_truth/bad/001_mask.png"],
    "split": ["train", "test"],
}
```

Useful behaviors:

- `root` prefixes relative paths.
- `from_file()` accepts csv/parquet/json-like files supported by pandas.
- Missing `label`, `label_index`, or `split` values may be inferred from the columns that are present.
- Invalid or unexpected split labels typically fail during normalization because the resulting table contains `None` or `NaN`.

### Video layout

`Avenue` is the reference video datamodule for this sub-skill.

Key layout cues from the source:

- video root contains `training_videos/` and `testing_videos/`
- masks live under `ground_truth_demo/testing_label_mask/`
- `clip_length_in_frames` controls how many frames each item returns
- `frames_between_clips` sets clip stride
- `target_frame` chooses which frame gets the ground truth when the clip has multiple frames

The same clip-based ideas apply to `ShanghaiTech` and `UCSDped`.

### Depth layout

Depth workflows combine RGB and depth paths.

- `MVTec3D` follows the benchmark-style category download layout.
- `Folder3D` is the custom analog of `Folder` for paired RGB/depth data.
- `ADAM3D` is another benchmark-style download with the same general depth pairing expectations.

Depth datasets are easiest to reason about when you keep three paths aligned:

1. RGB image path
2. depth map path
3. optional mask path for anomalies

## 6) Config shapes

### Data config

The `get_datamodule()` helper accepts a config object or plain dict and looks for a `data` section.

```yaml
data:
  class_path: anomalib.data.MVTecAD
  init_args:
    root: ./datasets/MVTecAD
    category: bottle
```

Notes:

- `class_path` is resolved against `anomalib.data`.
- `image_size` in `init_args` is normalized to a tuple when present.
- Unknown data classes raise `UnknownDatamoduleError`.

### Image inference config

`PredictDataset` is the smallest way to turn a file or directory into a batchable image dataset.

```python
from anomalib.data import PredictDataset

predict_data = PredictDataset(path="./images", image_size=(256, 256))
```

## 7) Utility rules worth remembering

- `validate_path()` rejects paths that are too long, contain non-printable characters, do not exist when `should_exist=True`, or fail extension checks.
- `validate_and_resolve_path()` combines root resolution and validation for folder-style layouts.
- `Folder` uses those path utilities internally, so bad extensions and bad roots are usually caught early.
- `Tabular` and `Folder` both rely on stem matching for masks.
- If a custom layout looks right but still fails, the first thing to inspect is usually path spelling plus image/mask stem alignment.
