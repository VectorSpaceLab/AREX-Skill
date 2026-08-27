# Backbones, necks, data mappers, and feature-shape wiring

Use this reference when the task involves replacing detrex backbones, wiring feature maps into a neck, choosing a data mapper, or debugging Detectron2 dataset-dict inputs. It is safe-by-default: all snippets use `pretrained=False` unless the user explicitly requests pretrained weights.

## Backbone selection guide

| Backbone | Import | Best fit | Backend/dependency cautions |
|---|---|---|---|
| `ResNet`, `BasicStem`, `make_stage` | `detrex.modeling.backbone` | Default DETR/Conditional-DETR/Deformable-DETR style configs; standard C2-compatible feature names such as `res2`-`res5` | Usually CPU-importable with Detectron2 installed. |
| `TorchvisionBackbone` | `detrex.modeling.backbone` | Quick feature extraction from torchvision model names | Requires `torchvision.models.feature_extraction`; `pretrained=True` may download weights. |
| `TimmBackbone` | `detrex.modeling.backbone` | timm feature-pyramid models and project configs that expect `p*` feature names | Requires `timm`; `pretrained=True` may download weights; some models lack `feature_info` or reject custom `norm_layer`. |
| `ConvNeXt`, `FocalNet` | `detrex.modeling.backbone` | Project configs that already use these architectures | May have architecture-specific pretrained checkpoint expectations. |
| `InternImage`, `EVAViT`, `EVA02_ViT` | `detrex.modeling.backbone` | Advanced project configs and large backbones | Often tied to extra dependencies, custom operators, or large checkpoints; treat as project-specific. |

## LazyCall snippets

### ResNet-50 style backbone

```python
from detectron2.config import LazyCall as L
from detrex.modeling.backbone import BasicStem, ResNet

backbone = L(ResNet)(
    stem=L(BasicStem)(in_channels=3, out_channels=64, norm="FrozenBN"),
    stages=L(ResNet.make_default_stages)(
        depth=50,
        stride_in_1x1=False,
        norm="FrozenBN",
    ),
    out_features=["res2", "res3", "res4", "res5"],
    freeze_at=1,
)
```

Set `freeze_at=0` or `1` depending on whether the stem should be trainable. `out_features` must match the downstream neck's `in_features` and `input_shapes` keys.

### Dilated ResNet-DC5 style stage

```python
from detectron2.config import LazyCall as L
from detrex.modeling.backbone import BasicStem, ResNet, make_stage

backbone = L(ResNet)(
    stem=L(BasicStem)(in_channels=3, out_channels=64, norm="FrozenBN"),
    stages=L(make_stage)(
        depth=50,
        stride_in_1x1=False,
        norm="FrozenBN",
        res5_dilation=2,
    ),
    out_features=["res2", "res3", "res4", "res5"],
    freeze_at=1,
)
```

Use this pattern when a model expects a larger final feature map instead of the regular `res5` stride.

### Torchvision backbone without downloads

```python
from detectron2.config import LazyCall as L
from detrex.modeling.backbone import TorchvisionBackbone

backbone = L(TorchvisionBackbone)(
    model_name="resnet50",
    pretrained=False,
    return_nodes={
        "layer2": "res3",
        "layer3": "res4",
        "layer4": "res5",
    },
)
```

If you alter `return_nodes`, update the neck shape metadata. The keys on the left are torchvision graph node names; the values are the names returned to detrex.

### timm backbone without downloads

```python
from detectron2.config import LazyCall as L
from detrex.modeling.backbone import TimmBackbone

backbone = L(TimmBackbone)(
    model_name="resnet50",
    features_only=True,
    pretrained=False,
    in_channels=3,
    out_indices=(1, 2, 3),
    norm_layer=None,
)
```

`TimmBackbone` returns a dictionary named by output indices: for `out_indices=(1, 2, 3)`, expect `{"p1": tensor, "p2": tensor, "p3": tensor}`. If you use a local checkpoint through timm, pass `checkpoint_path` and still keep `pretrained=False` unless the user wants timm's remote pretrained loading.

## ChannelMapper and feature metadata

`ChannelMapper` converts a feature dictionary from a backbone into a tuple of same-channel feature maps for DETR heads.

```python
import torch
import torch.nn as nn
from detrex.layers import ShapeSpec
from detrex.modeling import ChannelMapper

features = {
    "res3": torch.randn(1, 512, 64, 64),
    "res4": torch.randn(1, 1024, 32, 32),
    "res5": torch.randn(1, 2048, 16, 16),
}
input_shapes = {
    "res3": ShapeSpec(channels=512),
    "res4": ShapeSpec(channels=1024),
    "res5": ShapeSpec(channels=2048),
}
neck = ChannelMapper(
    input_shapes=input_shapes,
    in_features=["res3", "res4", "res5"],
    out_channels=256,
    norm_layer=nn.GroupNorm(num_groups=32, num_channels=256),
)
outs = neck(features)
assert len(outs) == 3
```

Checklist:

- `input_shapes` must contain every key listed in `in_features`.
- The channel count in `ShapeSpec(channels=...)` must match the actual feature tensor's channel dimension.
- `ChannelMapper.forward()` asserts `len(inputs) == len(self.convs)`, so pass only the feature dictionary expected by the mapper or adapt the mapper/in_features consistently.
- If `num_outs` is greater than the number of input features, extra stride-2 convolutions are appended from the last feature map or previous extra output.

## Safe backbone smoke patterns

For API-level smoke only, avoid pretrained downloads and large inputs:

```python
import torch
from detrex.modeling.backbone import TorchvisionBackbone

model = TorchvisionBackbone(
    model_name="resnet18",
    pretrained=False,
    return_nodes={"layer1": "res2", "layer2": "res3"},
)
model.eval()
with torch.no_grad():
    outs = model(torch.randn(1, 3, 64, 64))
assert set(outs) == {"res2", "res3"}
```

The bundled helper can run a similar check with:

```bash
python scripts/api_smoke.py --check-torchvision-backbone
```

## Data mapper map

| Mapper/transform | Import | Inputs | Output behavior |
|---|---|---|---|
| `DetrDatasetMapper` | `from detrex.data import DetrDatasetMapper` | Detectron2 dataset dict with `file_name`, image metadata, and optional `annotations` | Reads image, applies augmentation or augmentation-with-crop, emits `image` tensor and filtered `instances` during train. |
| `COCOInstanceNewBaselineDatasetMapper` | `from detrex.data import COCOInstanceNewBaselineDatasetMapper` | COCO instance-style dict with polygon masks | Adds `padding_mask`, transforms annotations, converts polygon masks to tensor masks. |
| `COCOPanopticNewBaselineDatasetMapper` | `from detrex.data import COCOPanopticNewBaselineDatasetMapper` | COCO panoptic-style dicts and panoptic segmentation assets | Produces panoptic-style instances/semantic outputs according to mapper config. |
| `MaskFormerSemanticDatasetMapper` | `from detrex.data import MaskFormerSemanticDatasetMapper` | Semantic-segmentation dataset dicts | Builds MaskFormer semantic training inputs. |
| `MaskFormerInstanceDatasetMapper` | `from detrex.data import MaskFormerInstanceDatasetMapper` | Instance-segmentation dataset dicts | Builds MaskFormer instance training inputs. |
| `MaskFormerPanopticDatasetMapper` | `from detrex.data import MaskFormerPanopticDatasetMapper` | Panoptic dataset dicts | Builds MaskFormer panoptic training inputs. |
| `ColorAugSSDTransform` | `from detrex.data import ColorAugSSDTransform` | RGB or BGR image arrays | Applies SSD-style random brightness/contrast/saturation/hue augmentation. |

### DetrDatasetMapper constructor

```python
from detrex.data import DetrDatasetMapper

mapper = DetrDatasetMapper(
    augmentation=[...],
    augmentation_with_crop=None,  # or another list of Detectron2 transforms
    is_train=True,
    mask_on=False,
    img_format="RGB",
)
```

Input dataset dict requirements:

```text
file_name: path or PathManager-readable URI to an image
height, width: image dimensions expected by Detectron2 utilities
annotations: optional list of Detectron2 annotation dicts for training
```

Training mode removes unsupported `keypoints`; it also removes `segmentation` unless `mask_on=True`. Evaluation mode removes `annotations` and returns only image metadata plus the image tensor.

### MaskFormer/COCO mapper transform builders

The dataset-mapper package also exposes transform-generation helpers for specific mapper families:

```python
from detrex.data.dataset_mappers import (
    coco_instance_transform_gen,
    coco_panoptic_transform_gen,
    maskformer_semantic_transform_gen,
)
```

Use these helpers only when you are building matching mapper configs. They are training-oriented and may assert `is_train=True` depending on the helper.

## Choosing between data APIs

- Use `DetrDatasetMapper` for DETR-style object detection configs expecting Detectron2 `Instances` from boxes and optional masks.
- Use the COCO LSJ or MaskFormer mappers for segmentation/panoptic configs that already expect `padding_mask`, semantic masks, or panoptic targets.
- Do not call a mapper just to inspect package imports; mappers read real images and apply transformations.
- If a dataset dict fails, inspect the dict schema, image readability, annotation format, and `mask_on` setting before changing model code.
