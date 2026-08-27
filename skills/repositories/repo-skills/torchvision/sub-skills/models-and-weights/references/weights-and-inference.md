# Weights, Metadata, and Inference Preprocessing

TorchVision uses multi-weight enums for pretrained models. Builders accept `weights=<WeightsEnum member>`, `weights="MEMBER"`, or `weights=None`. The old `pretrained=True/False` flag is deprecated; prefer explicit `weights=`.

## Weight Objects

```python
from torchvision.models import ResNet50_Weights, get_model_weights, get_weight

weights = ResNet50_Weights.DEFAULT
same = get_weight("ResNet50_Weights.DEFAULT")
weights_enum = get_model_weights("resnet50")
all_members = list(weights_enum)
```

Each weight enum member exposes:

| Attribute/API | Use |
| --- | --- |
| `weights.url` | Download URL used by `get_state_dict()`. Do not call in no-network tests. |
| `weights.transforms()` | Builds the exact preprocessing pipeline for that weight member. |
| `weights.meta` | Metadata such as categories, recipe, metrics, parameter counts, ops, min input size, or task-specific labels. |
| `weights.get_state_dict(progress=True, check_hash=True)` | Downloads/loads state dict through PyTorch Hub cache. |
| `WeightsEnum.verify(obj)` | Normalizes strings and validates enum members inside builders. |

`DEFAULT` is an alias to the best available weight for the installed TorchVision version. It can change between releases. Pin a concrete member such as `IMAGENET1K_V1` or `COCO_V1` when reproducibility matters.

## Avoiding Downloads

For tests, CI, shape checks, and examples that must be offline, always use `weights=None`. For builders with a backbone weight argument, also set it to `None`.

```python
from torchvision.models import resnet50
from torchvision.models.detection import fasterrcnn_resnet50_fpn

classification = resnet50(weights=None).eval()
detection = fasterrcnn_resnet50_fpn(weights=None, weights_backbone=None).eval()
```

Do not call `weights.get_state_dict()` and do not instantiate a model with `weights=...` unless a download/cache hit is acceptable.

## Download and Cache Behavior

Pretrained weights are loaded through PyTorch Hub. Cache location follows PyTorch Hub rules and can be influenced with `TORCH_HOME`. Agents should mention this when diagnosing slow first runs, permission errors, or unexpected disk usage.

Safe cache-aware pattern:

```python
import os
from torchvision.models import ResNet50_Weights, resnet50

os.environ.setdefault("TORCH_HOME", "<approved-cache-dir>")
weights = ResNet50_Weights.IMAGENET1K_V2
model = resnet50(weights=weights).eval()
```

Replace `<approved-cache-dir>` with a process-specific or user-approved cache directory before running. Do not bake machine-specific paths into public guidance.

## Inference Preprocessing

Use the transform bundled with the exact weights member. Do not hand-roll resize/crop/normalization unless reproducing a specific recipe.

```python
from PIL import Image
from torchvision.models import ResNet50_Weights, resnet50

weights = ResNet50_Weights.DEFAULT
model = resnet50(weights=weights).eval()
preprocess = weights.transforms()

image = Image.open("image.jpg").convert("RGB")
batch = preprocess(image).unsqueeze(0)
logits = model(batch)
class_id = logits.argmax(dim=1).item()
label = weights.meta["categories"][class_id]
```

The returned preprocessing object is often scriptable and may include resizing, center crop, dtype conversion, rescaling, and normalization. Inspect it with `print(weights.transforms())` for user explanations.

## Task-Specific Inference Notes

### Classification

- Input is usually an image tensor batch shaped `[N, 3, H, W]` after `weights.transforms()`.
- Output is logits; apply `softmax(dim=1)` only when probabilities are needed.
- Labels are commonly in `weights.meta["categories"]`.

### Detection and Instance Segmentation

- In eval mode, pass a list of image tensors or a batched form accepted by the model transform.
- Output is a list of dictionaries. Common keys: `boxes`, `labels`, `scores`, `masks`, `keypoints`.
- Keep `model.eval()` for inference. In train mode, detection models expect targets and return losses.
- Use `weights_backbone=None` when offline construction is required.

### Semantic Segmentation

- Output is a dictionary. Use `output["out"]` for class logits per pixel.
- Convert logits to a mask with `output["out"].argmax(1)`.
- Some models include `aux` outputs during training or when auxiliary heads are enabled.

### Video

- Use the weight transform for clip preprocessing; video models expect a clip tensor layout consistent with that transform.
- Do not reuse single-image classification preprocessing for video clips.

### Optical Flow

- RAFT weights bundle transforms for paired image batches.
- Use both transformed images from `weights.transforms()(img1_batch, img2_batch)`.
- RAFT returns multiple flow predictions; the last prediction is typically the most refined estimate.

```python
from torchvision.models.optical_flow import Raft_Large_Weights, raft_large

weights = Raft_Large_Weights.DEFAULT
transforms = weights.transforms()
model = raft_large(weights=None).eval()  # offline structural example
```

## Deprecated `pretrained` Migration

Replace deprecated calls:

```python
# Old
model = resnet50(pretrained=True)

# New, explicit and reproducible
model = resnet50(weights=ResNet50_Weights.IMAGENET1K_V1)

# New, best available for this installed version
model = resnet50(weights=ResNet50_Weights.DEFAULT)

# No weights
model = resnet50(weights=None)
```

The deprecated positional boolean form, such as `resnet50(True)`, should also be replaced.
