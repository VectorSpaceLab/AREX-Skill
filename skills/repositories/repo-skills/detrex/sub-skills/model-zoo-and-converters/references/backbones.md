# Backbones

Use this reference when the issue is backbone selection, feature shapes, or pretrained backbone reuse.

## Built-in ResNet
- detrex uses a LazyConfig-friendly ResNet wrapper for the common DETR-style backbones.
- The standard recipe freezes only the stem with `freeze_at=1`.
- Use `res5_dilation=2` when the config is a DC5 variant.
- Keep `out_features` aligned with the neck or decoder expectations.

## Timm backbones
Use the timm wrapper when the backbone family is not one of the built-in ResNet variants and the pretrained weights come from timm.
- `features_only=True` turns the backbone into a feature extractor.
- `out_indices` chooses which stages feed the neck.
- `pretrained=True` lets timm manage the backbone weight load; `pretrained=False` is the safer choice when you want to point to your own local weight file.
- Set `train.init_checkpoint` only when the config expects a local checkpoint path.

## Torchvision backbones
Use the torchvision wrapper when the feature source is a torchvision model with named nodes.
- `return_nodes` must match actual node names from the model graph.
- Validate the node names before wiring the neck.
- If the node names are wrong, the failure usually shows up as missing intermediate features rather than a weight-load problem.

## DINO backbone families
The DINO model zoo includes several backbone families, and the exact config row matters:
- ResNet
- Swin
- FocalNet
- ViT / MAE-style pretrained backbones
- ConvNeXt
- InternImage
- EVA

Do not mix the backbone family with a different neck or resolution setting just because the detector name is the same. The published row determines the expected feature shapes.

## MaskDINO backbone contract
MaskDINO is more sensitive to backbone and channel-shape choices because the model also includes a pixel decoder.
- The encoder hidden dimension is `2048` by default in the published COCO tables.
- The `1024` variant exists, but it is a different model shape.
- Mask-enhanced box initialization changes how the decoder seeds boxes, so treat it as part of the backbone/config contract.

## Practical rule
If the problem is “which weights can I plug in?”, this is a backbone question. If the problem is “how do I rename tensor keys?”, that belongs to the converter helper instead.
