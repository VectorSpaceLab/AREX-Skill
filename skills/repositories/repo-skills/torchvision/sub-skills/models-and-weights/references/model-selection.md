# Model Selection and Construction

TorchVision model builders live under `torchvision.models` and task-specific subpackages such as `torchvision.models.detection`, `torchvision.models.segmentation`, `torchvision.models.video`, `torchvision.models.quantization`, and `torchvision.models.optical_flow`.

## Core Lookup APIs

```python
import torchvision
from torchvision.models import get_model, get_model_builder, get_model_weights, get_weight, list_models

all_names = list_models()
resnets = list_models(include="resnet*")
detection_names = list_models(torchvision.models.detection)
model = get_model("resnet50", weights=None)
builder = get_model_builder("resnet50")
weights_enum = get_model_weights("resnet50")
weights = get_weight("ResNet50_Weights.DEFAULT")
```

Important signatures:

| API | Purpose |
| --- | --- |
| `list_models(module=None, include=None, exclude=None)` | Returns registered model names, optionally filtered with shell-style wildcards. |
| `get_model(name, **config)` | Instantiates the registered model and forwards `**config` to its builder. |
| `get_model_builder(name)` | Returns the model builder callable for inspection or delayed construction. |
| `get_model_weights(name_or_builder)` | Returns the `WeightsEnum` class associated with a builder. |
| `get_weight("EnumName.MEMBER")` | Returns a specific `WeightsEnum` value by fully qualified enum member name. |

`get_model_builder()` lowercases names. `list_models()` returns registered builder names, including task-specific builders when their submodule has been imported.

## Choosing by Task

| Task | Typical modules/builders | Output pattern |
| --- | --- | --- |
| Image classification | `resnet50`, `convnext_tiny`, `efficientnet_b0`, `vit_b_16`, `swin_t`, `mobilenet_v3_large` | Tensor logits shaped `[N, classes]`. Use `weights.meta["categories"]` for labels when available. |
| Quantized classification | `torchvision.models.quantization`, names like `quantized_resnet50` or `quantized_mobilenet_v3_large` | Quantized CPU-oriented models; use matching quantized weight enum. |
| Object detection | `fasterrcnn_*`, `retinanet_*`, `fcos_*`, `ssd*`, `ssdlite*` | In eval mode, list of dicts with boxes, labels, scores, and sometimes masks/keypoints. |
| Instance/keypoint segmentation | `maskrcnn_resnet50_fpn`, `keypointrcnn_resnet50_fpn` | Detection-style list of dicts plus masks or keypoints. |
| Semantic segmentation | `fcn_*`, `deeplabv3_*`, `lraspp_*` | Dict with `out` tensor and sometimes `aux`, typically `[N, classes, H, W]`. |
| Video classification | `r3d_18`, `mc3_18`, `r2plus1d_18`, `swin3d_*`, `mvit_v*`, `s3d` | Tensor logits for video clips; expected tensor layout is model/transform specific. |
| Optical flow | `raft_large`, `raft_small` | Sequence of flow predictions, with final item commonly used as the refined flow. |

## Safe Construction Patterns

Use no-download construction for tests and structural checks:

```python
from torchvision.models import get_model

model = get_model("resnet50", weights=None)
model.eval()
```

Use pretrained weights only when network/cache access is intended:

```python
from torchvision.models import ResNet50_Weights, resnet50

weights = ResNet50_Weights.DEFAULT
model = resnet50(weights=weights).eval()
preprocess = weights.transforms()
```

Detection builders often have both `weights` and `weights_backbone`. To avoid all downloads, set both explicitly:

```python
from torchvision.models.detection import fasterrcnn_resnet50_fpn

model = fasterrcnn_resnet50_fpn(weights=None, weights_backbone=None).eval()
```

If a builder accepts `num_classes`, pretrained weights may overwrite or constrain the class count based on `weights.meta["categories"]`. For custom class counts, use `weights=None` and load your own checkpoint, or replace the task head after building the pretrained backbone.

## Model Family Notes

- Classification builders usually accept `weights`, `progress`, and architecture-specific kwargs such as `num_classes`.
- Detection builders may require compiled TorchVision ops at runtime for NMS, ROIAlign, and related operators.
- Segmentation and detection builders can have `weights_backbone`; set it to `None` in offline tests.
- Quantized builders require quantized weights and are normally CPU-oriented.
- Optical flow weights bundle paired-image preprocessing; `weights.transforms()` expects two image batches.
- Video weights bundle clip preprocessing rather than single-image preprocessing.

## Inspection Script

The bundled script is safe by default and does not instantiate pretrained models:

```bash
python scripts/inspect_models.py list --include "*resnet*" --limit 20
python scripts/inspect_models.py weights resnet50
python scripts/inspect_models.py weight ResNet50_Weights.DEFAULT
```

Use `--construct` only with `weights=None` for lightweight smoke checks. Avoid constructing large detection/video models unless the user asks for it.
