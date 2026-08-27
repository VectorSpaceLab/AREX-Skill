# Targets and Reshape Transforms

## Target callable contract

A target is callable and receives one model output for one batch member. It must
return a scalar tensor suitable for gradient computation. Common built-ins:

```python
from pytorch_grad_cam.utils.model_targets import (
    ClassifierOutputTarget,
    ClassifierOutputSoftmaxTarget,
    ClassifierOutputReST,
    BinaryClassifierOutputTarget,
    SemanticSegmentationTarget,
    FasterRCNNBoxScoreTarget,
)

class_target = ClassifierOutputTarget(category=281)
prob_target = ClassifierOutputSoftmaxTarget(category=281)
rest_target = ClassifierOutputReST(category=281)
binary_target = BinaryClassifierOutputTarget(category=1)
seg_target = SemanticSegmentationTarget(category=2, mask=mask_numpy)
box_target = FasterRCNNBoxScoreTarget(
    labels=[1], bounding_boxes=[box_numpy], iou_threshold=0.5
)
```

Use one target per batch item. For structured outputs, write a custom callable
that selects the relevant field, class, box, mask, or similarity score and
returns a scalar.

## Reshape transform contract

`reshape_transform(activation)` is called for both activations and gradients.
It should return `B x C x H x W` (or the spatial dimensionality expected by the
CAM method) and must preserve the batch dimension.

ViT-style tokens (class token + 14x14 patches):

```python
def vit_transform(tensor, height=14, width=14):
    patches = tensor[:, 1:, :].reshape(tensor.size(0), height, width, tensor.size(2))
    return patches.transpose(2, 3).transpose(1, 2)
```

Swin-style tokens (7x7 patches, no class token):

```python
def swin_transform(tensor, height=7, width=7):
    patches = tensor.reshape(tensor.size(0), height, width, tensor.size(2))
    return patches.transpose(2, 3).transpose(1, 2)
```

Pass it to any CAM constructor:

```python
cam = GradCAM(model=model, target_layers=[target_layer], reshape_transform=vit_transform)
```

## Structured outputs

- Faster R-CNN feature pyramid activations can be converted with the package's
  `fasterrcnn_reshape_transform`; it interpolates feature maps to the pooled
  target size and concatenates channels.
- Semantic segmentation outputs are typically `C x H x W` per sample; use a
  binary spatial mask with `SemanticSegmentationTarget` to sum one class over
  selected pixels.
- Embedding/similarity models need a target that returns the desired similarity
  or embedding component. If the output is a tuple/dict, select the tensor field
  before applying any scalar operation.

Validate custom transforms with the bundled helper before running a full model.
