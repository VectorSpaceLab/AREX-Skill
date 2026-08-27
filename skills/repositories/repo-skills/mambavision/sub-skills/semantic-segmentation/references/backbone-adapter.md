# Backbone Adapter

The bundled MambaVision adapter provides the backbone bridge used by MMSegmentation UPerNet configs. The same adapter is also registered for MMDetection, but this sub-skill only needs the segmentation-facing behavior.

## Role

The adapter turns the classification-style MambaVision backbone into a feature extractor that returns four stage tensors for a decoder head.

Key behavior:
- registers `MM_mamba_vision` with both `mmseg.registry.MODELS` and `mmdet.registry.MODELS`
- inherits the base MambaVision backbone
- removes the classification `norm` and `head`
- returns normalized stage features from the requested `out_indices`

## Import and registry contract

The segmentation CLI imports `mamba_vision` directly before building the config. If `MM_mamba_vision` is missing from the registry, the adapter module was not imported.

If you launch from a different working directory, make sure the target project directory that contains the adapter is on `PYTHONPATH`.

## Constructor contract

The segmentation configs call the adapter with these fields:

- required: `dim`, `in_dim`, `depths`, `window_size`, `mlp_ratio`, `num_heads`
- common optional fields: `out_indices`, `pretrained`, `norm_layer`, `layer_scale`

The adapter computes the stage dimensions as:

```text
[dim, 2 * dim, 4 * dim, 8 * dim]
```

The published segmentation configs use `out_indices=(0, 1, 2, 3)` so all four stages are returned.

## Stage channels by family

| Family | `dim` | Stage channels |
| --- | ---: | --- |
| tiny | 80 | `[80, 160, 320, 640]` |
| small | 96 | `[96, 192, 384, 768]` |
| base | 128 | `[128, 256, 512, 1024]` |
| L3 | 256 | `[256, 512, 1024, 2048]` |

These values must match the UPerNet decoder `in_channels` and auxiliary head channel count.

## Normalization choices

The adapter maps `norm_layer` to:

- `ln` -> `nn.LayerNorm`
- `ln2d` -> `LayerNorm2d`
- `bn` -> `nn.BatchNorm2d`

The published configs use `ln2d`.

## Checkpoint loading rules

The `pretrained` argument is a string path or `None`.

Behavior:
- `pretrained=None` leaves the backbone initialized from scratch
- `pretrained=<path>` calls `load_checkpoint(self, pretrained, strict=False)`
- the loader accepts checkpoints wrapped as `state_dict`, `model`, or a raw dictionary
- leading `module.` prefixes are stripped automatically
- leading `encoder.` prefixes are also stripped when present

This means a family-matched classification checkpoint can usually be reused directly as the backbone initialization file, as long as the backbone dimensions and stage channels match the config.

## Config implications

A valid segmentation config must keep these pieces aligned:

- `backbone.pretrained` should point to the matching tiny/small/base/L3 checkpoint family
- `backbone.dim` and `backbone.in_dim` should match the expected backbone variant
- `decode_head.in_channels` must equal the four stage output channels
- `auxiliary_head.in_channels` must equal the third-stage channel count
- `crop_size` and the backbone `window_size` tuple should match the published recipe for the chosen family

If you change `out_indices`, also change the decoder to match the returned feature list.

## Quick mental model

Use this shape contract when debugging a config:

```python
backbone = dict(
    type='MM_mamba_vision',
    out_indices=(0, 1, 2, 3),
    pretrained='...pth.tar',
    depths=(3, 3, 10, 5),
    num_heads=(2, 4, 8, 16),
    window_size=(8, 8, 64, 32),
    dim=128,
    in_dim=64,
    mlp_ratio=4,
    drop_path_rate=0.4,
    norm_layer='ln2d',
    layer_scale=1e-5,
)
```

Then match the UPerNet head to the stage dimensions:

```python
decode_head=dict(in_channels=[128, 256, 512, 1024], num_classes=150)
auxiliary_head=dict(in_channels=512, num_classes=150)
```
