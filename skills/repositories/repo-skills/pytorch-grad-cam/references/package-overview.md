# Package Overview

## When to read

Read this for the verified public surface of the `grad-cam` distribution before
routing to a sub-skill or writing setup instructions.

## Verified public identity

- Distribution name: `grad-cam`
- Import package: `pytorch_grad_cam`
- Verified version during skill generation: `1.5.5`
- Core install: `pip install grad-cam`
- Python support from package metadata: Python `>=3.8` in `setup.py`.
- No console entry point is installed by the package; command-line examples are
  repository examples, so this skill bundles safe helper scripts instead.

## Main imports

```python
from pytorch_grad_cam import (
    GradCAM, HiResCAM, ScoreCAM, GradCAMPlusPlus, AblationCAM,
    XGradCAM, EigenCAM, EigenGradCAM, LayerCAM, FullGrad,
    GradCAMElementWise, KPCA_CAM, ShapleyCAM, FinerCAM, SegEigenCAM,
    RefineCAM, GuidedBackpropReLUModel,
)
from pytorch_grad_cam.utils.model_targets import (
    ClassifierOutputTarget, ClassifierOutputSoftmaxTarget,
    ClassifierOutputReST, BinaryClassifierOutputTarget,
    SemanticSegmentationTarget, FasterRCNNBoxScoreTarget,
)
from pytorch_grad_cam.utils.reshape_transforms import (
    vit_reshape_transform, swinT_reshape_transform,
    fasterrcnn_reshape_transform,
)
```

Additional task families:

- Metrics: `pytorch_grad_cam.metrics.cam_mult_image`,
  `pytorch_grad_cam.metrics.road`, `pytorch_grad_cam.metrics.arcc`.
- Deep Feature Factorization: `DeepFeatureFactorization`, `run_dff_on_image`.
- Images/visualization: `preprocess_image`, `show_cam_on_image`,
  `deprocess_image`, `show_factorization_on_image`.

## Workflow map

| Task | Best entry point | Notes |
| --- | --- | --- |
| Generate a heatmap for a classifier | `cam-generation` | Needs model, target layer list, input tensor, and optional target callables. |
| Choose among CAM algorithms | `methods-and-api` | Use method tradeoffs and signatures; expensive methods need batching. |
| Use ViT/Swin/CLIP or non-CNN activations | `model-task-adaptation` | Provide `reshape_transform`; avoid final ViT class-token-only layer. |
| Explain detection/segmentation/embeddings | `model-task-adaptation` | Use custom targets that reduce model outputs to scalar scores. |
| Score explanation quality | `metrics-and-evaluation` | ROAD/confidence metrics need input tensor, CAMs, targets, and model. |
| Discover concepts/features | `metrics-and-evaluation` | Use DFF with a target layer and optional classifier over concepts. |
| Debug install/device/API issues | root + nearest sub-skill troubleshooting | Keep optional deps and device runtimes explicit. |

## Data and tensor assumptions

- CAM input tensors are usually `B x C x H x W`; `BaseCAM` also supports
  3D/volumetric inputs where activations have compatible dimensions.
- `preprocess_image(img, mean, std)` expects a NumPy image and returns a
  batched normalized tensor.
- `show_cam_on_image(img, mask, use_rgb=False, image_weight=0.5)` expects
  the base image as `np.float32` in `[0, 1]`. It raises if the image range or
  `image_weight` is invalid.
- `targets` is either `None` (highest class per batch member) or a list of
  callables, usually one callable per batch member, that each return the scalar
  score to explain.
- A `reshape_transform` converts non-CNN activations to channel-first spatial
  activations before CAM weights are applied.

## Backend/dependency assumptions

- CPU is sufficient for API checks and small smoke tests.
- CUDA, MPS, and HPU are device variants: use only when PyTorch and the vendor
  runtime are installed and the model/tensors are placed on the same device.
- `timm` is not a base dependency but is commonly needed for Swin examples.
- `transformers` is not a base dependency but is needed for CLIP/HuggingFace
  examples.
- External pretrained model downloads are workflow choices, not required for
  the bundled smoke scripts.
