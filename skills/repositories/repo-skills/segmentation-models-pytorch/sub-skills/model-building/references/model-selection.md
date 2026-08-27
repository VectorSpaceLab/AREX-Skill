# SMP Model Selection

SMP exposes 12 semantic segmentation architectures through top-level classes and `smp.create_model`. Pick the architecture based on the task's constraints, then choose an encoder separately using [Encoders And Preprocessing](../../encoders-preprocessing/SKILL.md).

## Fast Selection Guide

| Need | Recommended starting point | Why |
| --- | --- | --- |
| General-purpose baseline, easiest debugging | `unet` / `smp.Unet` | Simple, widely used, supports arbitrary spatial sizes in SMP, good first shape smoke test. |
| Stronger U-Net-style decoder | `unetplusplus` / `smp.UnetPlusPlus` | Nested skip connections; useful when the task explicitly asks for U-Net++. |
| Lightweight efficient decoder | `linknet` / `smp.Linknet` | Compact decoder for speed-sensitive setups. |
| Pyramid multi-scale features | `fpn` / `smp.FPN` | Good general-purpose pyramid decoder; common for multi-scale objects. |
| Pyramid pooling context | `pspnet` / `smp.PSPNet` | Uses pyramid pooling and defaults to shallower encoder depth. |
| Attention pyramid decoder | `pan` / `smp.PAN` | Pyramid attention; configure `encoder_output_stride` as `16` or `32`. |
| Atrous spatial pyramid pooling | `deeplabv3` / `smp.DeepLabV3` | Use when the task calls for DeepLabV3 or output stride control. |
| DeepLab with decoder refinement | `deeplabv3plus` / `smp.DeepLabV3Plus` | Use when the task calls for DeepLabV3+ or stronger boundary refinement. |
| Unified perceptual parsing | `upernet` / `smp.UPerNet` | Useful for scene parsing-style architectures. |
| SegFormer-style decoder | `segformer` / `smp.Segformer` | Use when the task asks for SegFormer or transformer-style segmentation. |
| Dense prediction transformer | `dpt` / `smp.DPT` | Requires `tu-` timm ViT encoders; mind fixed image size and dynamic-size caveats. |
| Multi-scale attention U-Net variant | `manet` / `smp.MAnet` | Use when the task explicitly requests MAnet or attention U-Net-like behavior. |

For unknown tasks, start with `Unet` or `FPN` plus `encoder_weights=None` until shape and class counts are validated. Switch to pretrained weights only after the model contract is stable and preprocessing is routed through [Encoders And Preprocessing](../../encoders-preprocessing/SKILL.md).

## Architecture-Specific Notes

### Unet

```python
model = smp.Unet("resnet34", encoder_weights=None, in_channels=1, classes=1)
```

- SMP marks `Unet.requires_divisible_input_shape = False`, so it is a good first choice for arbitrary image sizes.
- Supports `decoder_channels`, `decoder_attention_type`, `decoder_interpolation`, `decoder_use_norm`, and the common model parameters.
- The model name is internally formed from the encoder, but downstream code should use the object directly instead of relying on that name.

### UnetPlusPlus

```python
model = smp.UnetPlusPlus("resnet34", encoder_weights=None, classes=3)
```

- Similar common parameters to `Unet`, with nested decoder blocks.
- Does not support encoder names beginning with `mit_b`; choose a different encoder or route to `Segformer`/`FPN` if a Mix Transformer encoder is required.
- If lowering `encoder_depth`, align `decoder_channels` length with the selected depth.

### MAnet

```python
model = smp.MAnet("resnet34", encoder_weights=None, classes=2)
```

- Supports `decoder_channels`, `decoder_pab_channels`, and `decoder_interpolation`.
- If lowering `encoder_depth`, trim `decoder_channels` to the same number of decoder stages.

### Linknet

```python
model = smp.Linknet("resnet34", encoder_weights=None, classes=1)
```

- Good for efficient encoder-decoder models.
- Does not support encoder names beginning with `mit_b`.

### FPN

```python
model = smp.FPN("resnet34", encoder_weights=None, classes=4)
```

- Useful pyramid baseline with `decoder_pyramid_channels`, `decoder_segmentation_channels`, `decoder_merge_policy`, `decoder_dropout`, `decoder_interpolation`, and `upsampling`.
- If using a `mit_b*` encoder, keep `encoder_depth=5`; SMP raises a `ValueError` otherwise.

### PSPNet

```python
model = smp.PSPNet("resnet34", encoder_weights=None, encoder_depth=3, classes=1)
```

- Defaults to `encoder_depth=3`, `psp_out_channels=512`, `psp_dropout=0.2`, and `upsampling=8`.
- A good match when pyramid pooling context is more important than a deep skip-connected decoder.

### PAN

```python
model = smp.PAN("resnet34", encoder_weights=None, encoder_output_stride=16, classes=1)
```

- `encoder_output_stride` must be `16` or `32`; SMP raises `ValueError` for other values.
- Defaults to `encoder_output_stride=16`, `decoder_channels=32`, and `upsampling=4`.

### DeepLabV3

```python
model = smp.DeepLabV3("resnet34", encoder_weights=None, encoder_output_stride=8, classes=1)
```

- `encoder_output_stride` must be `8` or `16`; default is `8`.
- Supports atrous rates, ASPP separability, ASPP dropout, and optional upsampling.

### DeepLabV3Plus

```python
model = smp.DeepLabV3Plus("resnet34", encoder_weights=None, encoder_output_stride=16, classes=1)
```

- `encoder_depth` can be `3`, `4`, or `5`; `encoder_output_stride` must be `8` or `16`.
- Default `decoder_aspp_separable=True`, `decoder_aspp_dropout=0.5`, and `upsampling=4`.

### UPerNet

```python
model = smp.UPerNet("resnet34", encoder_weights=None, classes=1)
```

- Supports `decoder_channels`, `decoder_use_norm`, and `upsampling`.
- A scene parsing-style choice when the user explicitly names UPerNet or wants pyramid pooling plus feature pyramid behavior.

### Segformer

```python
model = smp.Segformer("resnet34", encoder_weights=None, classes=1)
```

- Supports `decoder_segmentation_channels` and `upsampling`.
- Often requested with transformer-family encoders; route encoder availability and preprocessing details to [Encoders And Preprocessing](../../encoders-preprocessing/SKILL.md).

### DPT

```python
model = smp.DPT(
    encoder_name="tu-vit_tiny_patch16_224",
    encoder_weights=None,
    classes=1,
)
```

- Requires a timm encoder name with the `tu-` prefix; SMP raises `ValueError` otherwise.
- Defaults to a ViT-style encoder and `encoder_depth=4`.
- Some DPT encoders require fixed image sizes. Use the encoder's trained size, or pass `dynamic_img_size=True` when the timm encoder supports dynamic sizes.
- For smoke tests, use DPT-specific dimensions such as `224x224` and keep `encoder_weights=None` unless pretrained weight access is intentional.

## Configuration Recipes

### Grayscale Binary Segmentation

```python
model = smp.create_model(
    arch="unet",
    encoder_name="resnet18",
    encoder_weights=None,
    in_channels=1,
    classes=1,
)
x = torch.zeros(1, 1, 64, 64)
mask = model.eval()(x)
assert tuple(mask.shape) == (1, 1, 64, 64)
```

### Multiclass Segmentation

```python
model = smp.create_model(
    arch="fpn",
    encoder_name="resnet34",
    encoder_weights=None,
    in_channels=3,
    classes=7,
)
```

Use `classes=number_of_mask_channels`. Loss and metric choices are covered by [Training And Evaluation](../../training-evaluation/SKILL.md).

### Aux Classification Head

```python
aux_params = {
    "pooling": "avg",
    "dropout": 0.5,
    "activation": "sigmoid",
    "classes": 4,
}
model = smp.create_model(
    arch="unet",
    encoder_name="resnet18",
    encoder_weights=None,
    in_channels=3,
    classes=2,
    aux_params=aux_params,
)
mask, label = model(torch.zeros(1, 3, 64, 64))
assert tuple(mask.shape) == (1, 2, 64, 64)
assert tuple(label.shape) == (1, 4)
```

### Decoder-Only Fine-Tuning

```python
model = smp.FPN("resnet34", encoder_weights=None, classes=1)
model.freeze_encoder()
# train decoder and heads
model.unfreeze_encoder()
# resume full-model training
```

Route the optimizer, scheduler, loss, and metric setup to [Training And Evaluation](../../training-evaluation/SKILL.md).

## Constructor Inspection

When adapting config files, inspect the live callable signature rather than guessing optional parameters:

```python
import inspect
import segmentation_models_pytorch as smp

print(inspect.signature(smp.Unet))
print(inspect.signature(smp.create_model))
```

If the task is only to verify that a proposed architecture/encoder/channel/class configuration runs, prefer the bundled [model_smoke_test.py](../scripts/model_smoke_test.py) before writing a full training script.
