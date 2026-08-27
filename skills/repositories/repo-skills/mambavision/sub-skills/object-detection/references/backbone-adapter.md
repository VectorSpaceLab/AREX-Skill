# Backbone Adapter Reference

The detection adapter lives in the MambaVision object-detection tooling and registers the backbone as `MM_mamba_vision` for both MMDetection and MMSegmentation.

## What the adapter does

- subclasses the core `MambaVision` backbone
- registers the class into both OpenMMLab `MODELS` registries
- removes the ImageNet classifier head and final pooled norm
- adds stage-specific normalization layers named `outnorm0` through `outnorm3`
- returns a list of four stage feature maps in `forward`, not classification logits
- loads the backbone checkpoint with `mmengine.runner.load_checkpoint(..., strict=False)` when `pretrained` is a string path

The adapter is the bridge between the published classification checkpoint family and downstream OpenMMLab detectors.

## Constructor contract

The published configs build the adapter with these fields:

| Field | Purpose |
| --- | --- |
| `type` | Must be `MM_mamba_vision` |
| `dim` | Base channel width of the first stage |
| `in_dim` | Input stem width |
| `depths` | Number of blocks per stage |
| `num_heads` | Attention heads per stage |
| `window_size` | Window size per stage |
| `mlp_ratio` | MLP expansion ratio |
| `out_indices` | Which stages to expose to the detector neck |
| `pretrained` | Path to the published backbone checkpoint |
| `norm_layer` | One of `ln`, `ln2d`, or `bn`; the published configs use `ln2d` |
| `layer_scale` | Optional layer-scale coefficient |

The small, tiny, and base variants use these output widths:

| Family | Stage channels |
| --- | --- |
| Tiny | `[80, 160, 320, 640]` |
| Small | `[96, 192, 384, 768]` |
| Base | `[128, 256, 512, 1024]` |

The detector neck must match these channels with `neck.in_channels`.

## Import and registry behavior

The training and testing entry points import the adapter module before building the runner. If you launch MMDetection from another script or notebook, import the adapter first:

```python
import mamba_vision
from mmdet.registry import MODELS

print(MODELS.get('MM_mamba_vision'))
```

If the adapter module is not importable from the target project, add the adapter directory to `PYTHONPATH` before building the runner.

## Checkpoint loading behavior

- `pretrained` is the backbone initializer, not the detector checkpoint.
- `load_checkpoint(..., strict=False)` tolerates some mismatch, but it does not make a tiny checkpoint compatible with a base config or vice versa.
- If the file contains `state_dict` or `module.` prefixes, the underlying loader can still consume it, but the architecture must still match the published family.
- A path typo usually surfaces as a missing file error; a family mismatch usually surfaces as missing or unexpected keys.

## Expected forward contract

Downstream heads consume the four feature maps returned by the adapter. The result is a list of tensors, one per selected stage, each with batch dimension first and channels matching the family table above.

Do not expect logits from the detection backbone. The ROI and mask heads produce the detector outputs.
