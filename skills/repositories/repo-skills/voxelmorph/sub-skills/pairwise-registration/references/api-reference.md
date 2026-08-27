# Pairwise Registration API Reference

This reference describes the current PyTorch VoxelMorph pairwise registration API used by this skill. It is self-contained: future agents should rely on these distilled contracts and the bundled smoke script rather than reopening repository scripts.

## Verified runtime facts

| Component | Current contract |
| --- | --- |
| Package import | `import voxelmorph as vxm` |
| Model entry point | `vxm.nn.models.VxmPairwise` |
| Loss provider | `neurite.nn.modules` |
| Image tensor convention | `(B, C, *spatial)` channels-first PyTorch tensors |
| Field tensor convention | `(B, ndim, *spatial)` channels-first velocity/displacement fields |
| Minimum verified backend | CPU PyTorch; CUDA is optional for user workloads |

The current package is a PyTorch branch. Old TensorFlow examples and `vxm.networks.VxmDense`-style calls are not the runtime contract for this skill.

## Needed modules

`VxmPairwise` composes the following building blocks:

| Module | Role |
| --- | --- |
| `neurite.nn.models.BasicUNet` | Backbone that consumes concatenated source/target channels and produces feature maps. |
| `neurite.nn.modules.ConvBlock` | Flow layer used by `VxmPairwise._init_flow_layer()` to produce an `ndim`-channel velocity field. |
| `voxelmorph.nn.modules.IntegrateVelocityField` | Optional scaling-and-squaring integration when `integration_steps > 0`. |
| `voxelmorph.nn.modules.SpatialTransformer` | Warps source or target images when `return_warped_source` or `return_warped_target` is requested. |

For standalone transform math, field composition, or coordinate/sign details outside the model call, route to `transform-ops`.

## `VxmPairwise` constructor

Verified signature:

```python
vxm.nn.models.VxmPairwise(
    ndim: int,
    source_channels: int,
    target_channels: int,
    nb_features=(16, 16, 16, 16, 16),
    activations=torch.nn.ReLU,
    final_activation=None,
    flow_initializer=1e-5,
    integration_steps=5,
    resize_integrated_fields=False,
    device="cpu",
    unet_kwargs=None,
)
```

### Constructor arguments

| Argument | Meaning and guidance |
| --- | --- |
| `ndim` | Number of spatial dimensions. Use `2` for `(H, W)` tensors and `3` for `(D, H, W)` tensors. |
| `source_channels`, `target_channels` | Channel counts expected by `forward(source, target)`. A mismatch causes a PyTorch convolution channel error. |
| `nb_features` | Sequence of UNet feature counts. Short, small sequences such as `(4, 4, 4)` are suitable for smoke tests; larger defaults are for real workloads. Spatial dimensions must be compatible with the UNet down/up path. |
| `activations`, `final_activation` | Passed to Neurite `BasicUNet`. Default activation is `torch.nn.ReLU`; the flow head has its own initialization. |
| `flow_initializer` | Standard deviation for normal initialization of the flow layer convolution weights; bias is zeroed. Use the default unless you have a reason to change initial deformation scale. |
| `integration_steps` | `0` disables stationary-velocity integration; `>0` enables integrated displacement fields and permits `return_warped_target=True`. More steps cost more time/memory. |
| `resize_integrated_fields` | Stored by the model but not an active resizing branch in the verified forward path. Do not rely on it to fix shape/memory issues. |
| `device` | Used while creating the flow layer. A robust pattern is to construct the model for an available device and then call `model.to(device)` for the whole module. |
| `unet_kwargs` | Extra keyword arguments passed to `neurite.nn.models.BasicUNet` after fixed arguments are supplied. Do not duplicate `ndim`, `in_channels`, `out_channels`, `nb_features`, `activations`, or `final_activation`; duplicates raise `TypeError: got multiple values for ...`. |

## `forward()` signature and inputs

Verified signature:

```python
model.forward(
    source: torch.Tensor,
    target: torch.Tensor,
    return_warped_source: bool = False,
    return_warped_target: bool = False,
    return_field_type: Literal["displacement", "velocity", "svf"] = "displacement",
)
```

Input tensors:

| Tensor | Required shape | Notes |
| --- | --- | --- |
| `source` | `(B, C_source, *spatial)` | Moving image. Channels must match `source_channels`. |
| `target` | `(B, C_target, *spatial)` | Fixed image. Spatial shape and device should match `source`; channels must match `target_channels`. |

The model concatenates `source` and `target` along channel dimension `1`, predicts a positive velocity field from source to target, optionally integrates it, and optionally warps source/target images.

## Return matrix

Let `S = *spatial`, `Cs = source_channels`, and `Ct = target_channels`.

| Options | Return value | Shapes |
| --- | --- | --- |
| Default flags, `return_field_type="displacement"` | `field` | `(B, ndim, *S)`. If `integration_steps > 0`, this is the integrated displacement; if `integration_steps == 0`, it is the raw velocity used as a displacement. |
| Default flags, `return_field_type="velocity"` or `"svf"` | `velocity` | `(B, ndim, *S)` raw stationary velocity field. |
| `return_warped_source=True` | `(field, warped_source)` | `field: (B, ndim, *S)`, `warped_source: (B, Cs, *S)`. |
| `return_warped_target=True` | `(field, warped_target)` | `field: (B, ndim, *S)`, `warped_target: (B, Ct, *S)`. Requires `integration_steps > 0`. |
| Both warped flags | `(field, warped_source, warped_target)` | Field first, then source warp, then target warp. |

`return_field_type` only changes the first returned tensor. Warped image outputs are still computed from displacement fields internally.

## Error and edge cases

| Symptom | Cause | Resolution |
| --- | --- | --- |
| `ValueError: Cannot return warped target image when integration_steps=0` | Target warping requires an inverse transform from integrated stationary velocity. | Set `integration_steps > 0`, or request only the source warp/field. |
| `ValueError: return_field_type must be one of ...` | Invalid `return_field_type`. | Use `"displacement"`, `"velocity"`, or `"svf"`. |
| `TypeError: got multiple values for keyword argument ...` | `unet_kwargs` duplicates fixed constructor arguments. | Remove duplicates from `unet_kwargs`. |
| PyTorch channel mismatch in the first convolution | `source_channels`/`target_channels` do not match input tensors. | Reconstruct the model with matching channels or reshape data upstream. |
| Size mismatch during UNet skip concatenation | Spatial dimensions are incompatible with the selected UNet depth/downsampling path, often odd or not divisible enough. | For smoke tests, use square power-of-two sizes such as `16` with `(4, 4, 4)` features. For real data, crop/pad/resample upstream. |
| Device mismatch | Model and tensors are on different devices. | Move model and every batch tensor to the same `torch.device`. |

## Loss selection through Neurite

Do not instantiate `voxelmorph.nn.losses.MSE`, `NCC`, `Dice`, or `Grad`; those classes raise `NotImplementedError` and point to Neurite replacements.

Use Neurite modules directly:

| Goal | Neurite module | Verified call pattern |
| --- | --- | --- |
| Mean-squared image matching | `ne.nn.modules.MSE()` | `image_loss = ne.nn.modules.MSE()(target, warped_source).mean()` |
| Local normalized cross-correlation | `ne.nn.modules.NCC(window_size=9)` | `image_loss = ne.nn.modules.NCC()(target, warped_source).mean()` |
| Field smoothness | `ne.nn.modules.SpatialGradient(penalty="l1" or "l2")` | `reg_loss = ne.nn.modules.SpatialGradient("l2")(field).mean()` |
| Segmentation overlap when tensors are already prepared | `ne.nn.modules.Dice()` | `dice_loss = ne.nn.modules.Dice()(seg_a, seg_b).mean()` |

A typical unsupervised pairwise objective is:

```python
loss = image_weight * image_loss + grad_weight * reg_loss
```

The bundled smoke script exposes `--image-loss mse|ncc`, `--grad-penalty l1|l2`, and `--lambda-grad` for this pattern.

## Checkpoint contract

Prefer saving a dictionary with both architecture config and weights:

```python
payload = {
    "model_config": {
        "ndim": 2,
        "source_channels": 1,
        "target_channels": 1,
        "nb_features": (4, 4, 4),
        "integration_steps": 1,
    },
    "state_dict": model.state_dict(),
}
torch.save(payload, "vxm_pairwise.pt")
```

Reload by reconstructing the same `VxmPairwise` config and then calling `load_state_dict(payload["state_dict"])`. Avoid relying on full-object `torch.save(model, ...)` because it is less portable across source/package revisions.
