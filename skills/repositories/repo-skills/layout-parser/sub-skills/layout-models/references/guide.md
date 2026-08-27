# Layout Models Guide

This guide covers LayoutParser's model-zoo wrappers and backend selection
logic.

## Main APIs

| Symbol | Purpose | Notes |
| --- | --- | --- |
| `AutoLayoutModel(config_path, ...)` | Select an available backend from an `lp://` path | Chooses by backend name first, then by dataset name |
| `Detectron2LayoutModel(...)` | Detectron2-backed layout detector | Available only when Detectron2 is installed |
| `EfficientDetLayoutModel(...)` | EfficientDet-backed layout detector | Requires `torch`, `torchvision`, and `effdet` |
| `PaddleDetectionLayoutModel(...)` | PaddleDetection-backed layout detector | Available only when Paddle is installed |
| `LayoutModelConfig` | Parsed representation of an `lp://` config path | Stores backend, dataset, model arch, and identifier |
| `layout_model_config_parser(...)` | Parse `lp://` forms into `LayoutModelConfig` | Handles full, short, and brief forms |

## `lp://` path forms

LayoutParser accepts these forms for model/config paths:

- `lp://<backend>/<dataset>/<model>/<config|weight>`
- `lp://<dataset>/<model>/<config|weight>`
- `lp://<dataset>`

The source code also accepts short forms that omit the backend or the config
identifier and then fills in the missing pieces from the available catalogs.

## Backend families

### Detectron2

Supported datasets in the repository catalogs:

- HJDataset
- PubLayNet
- PrimaLayout
- NewspaperNavigator
- TableBank
- MFD

Detectron2 is the broadest backend family in the repo, but it also has the most
installation friction.

### EfficientDet

Supported datasets in the catalogs:

- PubLayNet
- MFD

This is the backend family that is easiest to smoke-test in the verified
inspection environment.

### PaddleDetection

Supported datasets in the catalogs:

- PubLayNet
- TableBank

The Paddle path uses a model tarball layout with a custom cache/extraction
handler.

### Catalog snapshot

| Backend | Example model families | Typical config names |
| --- | --- | --- |
| Detectron2 | Faster R-CNN, Mask R-CNN, RetinaNet | `faster_rcnn_R_50_FPN_3x`, `mask_rcnn_R_50_FPN_3x`, `retinanet_R_50_FPN_3x`, `mask_rcnn_X_101_32x8d_FPN_3x` |
| EfficientDet | EfficientDet D0/D1 | `tf_efficientdet_d0`, `tf_efficientdet_d1` |
| PaddleDetection | PP-YOLOv2 | `ppyolov2_r50vd_dcn_365e` |

The source catalogs also define dataset-specific label maps, so you usually do
not need to build the category mapping by hand unless the task uses a custom
model.

## Runtime behavior

- `AutoLayoutModel` first looks for an installed backend name inside the config
  string.
- If that fails, it falls back to the dataset name and uses the first available
  backend for that dataset.
- `Detectron2LayoutModel` and `EfficientDetLayoutModel` choose CUDA when the
  installed torch build reports CUDA availability.
- `PaddleDetectionLayoutModel` uses Paddle's inference runtime and model tar
  extraction helper.
- All model families use `PathManager` to resolve model and config URLs.

## Typical workflows

### 1) Load a known backend explicitly

1. Choose the backend class.
2. Pass the matching `lp://` path.
3. If the backend-specific label map matters, override `label_map` explicitly.
4. Detect on an image array or PIL image.

### 2) Let LayoutParser choose the backend

1. Use `AutoLayoutModel` with a valid `lp://` path.
2. Make sure at least one backend for the dataset is installed.
3. If you want CPU instead of the default CUDA path, set `device='cpu'`
   explicitly.
4. Use the returned model like any other layout detector.

### 3) Check backend readiness before choosing a config

1. Run `../../../scripts/inspect_backends.py`.
2. Confirm the backend package is installed.
3. Confirm the model family supports the dataset you want.
4. Only then move on to a model download or inference run.

## Model catalogs

The source catalogs define the model URLs and label maps. When writing guidance,
keep the public dataset and model names intact:

- `HJDataset`
- `PubLayNet`
- `PrimaLayout`
- `NewspaperNavigator`
- `TableBank`
- `MFD`

## Troubleshooting

- `ValueError: Invalid model config_path`: the path is not an `lp://` path or
  the format is malformed.
- `ValueError: No available model found`: no installed backend matches the
  requested dataset or backend string.
- Backend `ImportError`: install the matching backend package before trying to
  instantiate the class.
- `Detectron2LayoutModel` may need a separate Detectron2 install path even when
  the rest of LayoutParser is installed.
- `PaddleDetectionLayoutModel` expects the extracted inference files inside the
  downloaded model directory.
- `torch.cuda.is_available()` changes the default device choice for the torch-
  backed models.
- Model download or cache problems usually live in the `PathManager` layer, not
  in the model class itself.

## Read next

- `../layout-objects/references/guide.md` for the `Layout` and `TextBlock`
  objects returned by the models
- `../visualization/references/guide.md` for drawing the model output
- `../../../references/troubleshooting.md` for backend installation and cache issues
