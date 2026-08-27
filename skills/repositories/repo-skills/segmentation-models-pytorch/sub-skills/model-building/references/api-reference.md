# SMP Model-Building API Reference

This reference covers model construction and inspection for `segmentation_models_pytorch` 0.5.1.dev0. Future agents should not need the source checkout to create or debug the supported model APIs described here.

## Import Surface

```python
import segmentation_models_pytorch as smp
```

Top-level model classes exposed by SMP:

- `smp.Unet`
- `smp.UnetPlusPlus`
- `smp.MAnet`
- `smp.Linknet`
- `smp.FPN`
- `smp.PSPNet`
- `smp.PAN`
- `smp.DeepLabV3`
- `smp.DeepLabV3Plus`
- `smp.UPerNet`
- `smp.Segformer`
- `smp.DPT`

`create_model` accepts case-insensitive architecture keys and dispatches to these classes.

```python
model = smp.create_model(
    arch="fpn",
    encoder_name="resnet34",
    encoder_weights=None,
    in_channels=3,
    classes=1,
)
```

Signature:

```python
smp.create_model(
    arch: str,
    encoder_name: str = "resnet34",
    encoder_weights: Optional[str] = "imagenet",
    in_channels: int = 3,
    classes: int = 1,
    **kwargs,
) -> torch.nn.Module
```

Use `encoder_weights=None` for deterministic offline creation. The default `encoder_weights="imagenet"` may attempt to load pretrained weights and can require network or cache availability depending on the encoder.

## Architecture Keys

Valid `arch` keys for `smp.create_model`:

| Key | Class | Notes |
| --- | --- | --- |
| `unet` | `smp.Unet` | U-Net decoder; accepts arbitrary spatial sizes because SMP marks this class as not requiring divisible input shapes. |
| `unetplusplus` | `smp.UnetPlusPlus` | Nested U-Net decoder; does not support `mit_b*` encoders. |
| `manet` | `smp.MAnet` | Multi-scale attention decoder with `decoder_channels`. |
| `linknet` | `smp.Linknet` | Efficient decoder; does not support `mit_b*` encoders. |
| `fpn` | `smp.FPN` | Feature Pyramid Network; `mit_b*` encoders require `encoder_depth=5`. |
| `pspnet` | `smp.PSPNet` | Pyramid pooling decoder; default `encoder_depth=3` and `upsampling=8`. |
| `pan` | `smp.PAN` | Pyramid Attention Network; `encoder_output_stride` must be `16` or `32`. |
| `deeplabv3` | `smp.DeepLabV3` | ASPP decoder; `encoder_output_stride` must be `8` or `16`, default `8`. |
| `deeplabv3plus` | `smp.DeepLabV3Plus` | DeepLabV3+ decoder; `encoder_depth` can be `3`, `4`, or `5`, default output stride `16`. |
| `upernet` | `smp.UPerNet` | Unified Perceptual Parsing decoder. |
| `segformer` | `smp.Segformer` | SegFormer-style decoder, often paired with Mix Transformer encoders. |
| `dpt` | `smp.DPT` | Dense Prediction Transformer; requires a timm encoder name with the `tu-` prefix. |

A wrong architecture key raises a `KeyError` that lists available lower-case keys.

## Shared Constructor Parameters

Most SMP model constructors share these parameters:

| Parameter | Purpose | Practical guidance |
| --- | --- | --- |
| `encoder_name` | Backbone used as feature extractor. | Use a known encoder such as `resnet18` or `resnet34` for smoke checks. Route encoder lookup to [Encoders And Preprocessing](../../encoders-preprocessing/SKILL.md). |
| `encoder_weights` | Pretrained encoder weights name or `None`. | Use `None` for offline tests and reproducible shape checks. Use a named weight set only when cache/network availability is intentional. |
| `encoder_depth` | Number of downsampling stages/features used by the decoder. | Lower values can make models lighter, but decoder channel lists may need matching lengths for `Unet`, `UnetPlusPlus`, `MAnet`, and `DPT`. |
| `in_channels` | Number of channels in the input tensor. | Must match `x.shape[1]`; use `1` for grayscale, `3` for RGB, higher values for multispectral tensors. |
| `classes` | Number of output mask channels. | Binary single-mask setups usually use `classes=1`; multiclass logits usually use one channel per class. |
| `activation` | Optional activation after the segmentation head. | Keep `None` for training with logits; add `sigmoid` or `softmax` only when downstream code expects activated outputs. |
| `aux_params` | Optional classification head configuration. | When not `None`, forward returns `(mask, label)` instead of only `mask`. |
| `**kwargs` | Extra encoder or architecture-specific arguments. | Timm-specific options such as DPT `dynamic_img_size=True` flow through here. |

## Class Construction Patterns

Use class constructors when the architecture is known at development time:

```python
model = smp.Unet(
    encoder_name="resnet34",
    encoder_weights=None,
    in_channels=1,
    classes=2,
)
```

Use `smp.create_model` when architecture comes from config, CLI arguments, experiments, or a registry:

```python
model = smp.create_model(
    arch=config["arch"],
    encoder_name=config.get("encoder_name", "resnet34"),
    encoder_weights=None,
    in_channels=config["in_channels"],
    classes=config["classes"],
)
```

`create_model` forwards all extra `**kwargs` to the selected class, so architecture-specific parameters such as `decoder_interpolation`, `encoder_output_stride`, `decoder_channels`, `upsampling`, or `dynamic_img_size` can still be configured.

## Input And Output Contract

SMP model inputs are PyTorch tensors in NCHW layout:

```python
x = torch.zeros(batch_size, in_channels, height, width)
```

Without aux output:

```python
mask = model(x)
assert mask.shape[:2] == (batch_size, classes)
```

With aux output:

```python
aux_params = {
    "pooling": "avg",
    "dropout": 0.5,
    "activation": "sigmoid",
    "classes": 4,
}
model = smp.Unet("resnet34", encoder_weights=None, classes=3, aux_params=aux_params)
mask, label = model(x)
assert mask.shape[:2] == (batch_size, 3)
assert label.shape == (batch_size, 4)
```

The `classes` constructor parameter controls segmentation mask channels. `aux_params["classes"]` controls auxiliary label channels.

## Encoder Freeze Helpers

All SMP segmentation models inherit these helpers:

```python
model.freeze_encoder()
model.unfreeze_encoder()
```

`freeze_encoder()` sets encoder parameters to `requires_grad=False` and places normalization layers that track running statistics into evaluation mode. SMP keeps a frozen encoder frozen even if code later calls `model.train()`. Call `unfreeze_encoder()` before full-model fine-tuning so encoder parameters and normalization layers become trainable again.

Quick inspection pattern:

```python
model.freeze_encoder()
assert not any(parameter.requires_grad for parameter in model.encoder.parameters())
model.unfreeze_encoder()
assert all(parameter.requires_grad for parameter in model.encoder.parameters())
```

## Shape Smoke Check

For a quick local check without pretrained weights, run:

```bash
python sub-skills/model-building/scripts/model_smoke_test.py --arch unet --encoder resnet18 --in-channels 1 --classes 1 --height 64 --width 64
```

The script prints JSON with `ok`, input shape, mask shape, optional aux label shape, resolved encoder weights, and model metadata.
