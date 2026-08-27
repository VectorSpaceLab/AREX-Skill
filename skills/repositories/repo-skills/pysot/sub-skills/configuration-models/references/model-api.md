# PySOT model API reference

This reference covers the config-driven model construction API and component mappings used by PySOT. It is for safe inspection/construction, not for full tracking execution, snapshot loading, or training.

## Verified construction entry points

PySOT builds model/tracker objects from the global `cfg`:

```python
from pysot.core.config import cfg
from pysot.models.model_builder import ModelBuilder
from pysot.tracker.tracker_builder import build_tracker

cfg.merge_from_file(config_path)
model = ModelBuilder()
tracker = build_tracker(model)
```

Facts verified for this skill:

- `cfg.merge_from_file(path)` is the YACS config merge operation used by PySOT configs.
- `ModelBuilder()` reads the current global `cfg` and constructs backbone, optional neck, RPN head, and optional mask/refine modules.
- `build_tracker(model)` dispatches on `cfg.TRACK.TYPE`.
- A sample AlexNet SiamRPN config loaded and constructed `ModelBuilder` plus `SiamRPNTracker` on CPU without loading a snapshot.
- Construction is safe only if you do not call training `forward`, do not run video/dataset inference, and do not load external checkpoints.

## Component factory mappings

### Backbones

`BACKBONE.TYPE` must be one of these exact factory keys:

| Config key | Factory target | Common config usage |
| --- | --- | --- |
| `alexnetlegacy` | legacy AlexNet module | Inference configs for `siamrpn_alex_dwxcorr` and `_otb`. |
| `alexnet` | layer-split AlexNet module | Training config variant for AlexNet. |
| `mobilenetv2` | MobileNetV2 module | `siamrpn_mobilev2_l234_dwxcorr`. |
| `resnet18` | atrous ResNet-18 | Supported factory, not common in model-zoo YAMLs. |
| `resnet34` | atrous ResNet-34 | Supported factory, not common in model-zoo YAMLs. |
| `resnet50` | atrous ResNet-50 | ResNet SiamRPN++, SiamMask, and long-term variants. |

Common `BACKBONE.KWARGS`:

- AlexNet: `width_mult`.
- ResNet: `used_layers`, commonly `[2, 3, 4]` for SiamRPN++ or `[0, 1, 2, 3]` for SiamMask.
- MobileNetV2: `used_layers: [3, 5, 7]` and `width_mult: 1.4` in the model-zoo config.

### Neck/adjust layers

`ADJUST.ADJUST` controls whether `ModelBuilder` creates `self.neck`.

| Config key | Factory target | Notes |
| --- | --- | --- |
| `AdjustLayer` | single adjust layer | Use when one feature map is adjusted. |
| `AdjustAllLayer` | multiple adjust layers | Common for ResNet/MobileNet multi-layer features. |

For `AdjustAllLayer`, `ADJUST.KWARGS.in_channels` and `out_channels` lists should align with the backbone feature list used by the RPN. For example, ResNet-50 l234 configs use three feature maps and three channel entries.

### RPN heads

`RPN.TYPE` must be one of:

| Config key | Factory target | Important kwargs |
| --- | --- | --- |
| `UPChannelRPN` | up-channel RPN | `anchor_num`, `feature_in` if customized. |
| `DepthwiseRPN` | depth-wise cross-correlation RPN | `anchor_num`, `in_channels`, `out_channels`. |
| `MultiRPN` | multiple depth-wise RPN heads averaged or weighted | `anchor_num`, `in_channels` list, optional `weighted`. |

RPN output conventions:

- Classification channels are `2 * anchor_num`.
- Localization channels are `4 * anchor_num`.
- `ModelBuilder.log_softmax` reshapes classification output as `[batch, 2, anchors, height, width]`; channel counts must remain consistent with anchor settings.
- For `MultiRPN`, `RPN.KWARGS.in_channels` length should match the number of selected adjusted feature maps.

### Mask and refine heads

`MASK.MASK: true` causes `ModelBuilder` to create `self.mask_head`. If `REFINE.REFINE: true`, it also creates `self.refine_head`.

| Config key | Factory target | Notes |
| --- | --- | --- |
| `MaskCorr` | mask correlation head | Common kwargs include `in_channels`, `hidden`, and `out_channels`; model-zoo SiamMask uses `out_channels: 3969`. |
| `Refine` | mask refinement head | Required by `SiamMaskTracker`; constructor takes no config kwargs. |

`SiamMaskTracker` asserts that the model has both `mask_head` and `refine_head`. If you set `TRACK.TYPE: SiamMaskTracker` without enabling both mask and refine, construction fails immediately.

### Tracker dispatch

`build_tracker(model)` uses this exact map:

| `TRACK.TYPE` | Tracker class | Config expectations |
| --- | --- | --- |
| `SiamRPNTracker` | short-term bounding-box tracker | RPN outputs only; `MASK.MASK` normally false. |
| `SiamMaskTracker` | short-term tracker with mask/polygon output | Requires `MASK.MASK: true` and `REFINE.REFINE: true`. |
| `SiamRPNLTTracker` | long-term SiamRPN tracker | Uses confidence thresholds and lost-instance search size. |

Unsupported strings cause a `KeyError` in tracker construction; the bundled validator reports this before construction.

## Safe construction pattern for agents

Use the bundled validator for routine checks. If you must write custom code, keep it equivalent to this pattern:

```python
from pathlib import Path

config_path = Path("path/to/config.yaml")

from pysot.core.config import cfg
cfg.merge_from_file(str(config_path))

from pysot.models.model_builder import ModelBuilder
from pysot.tracker.tracker_builder import build_tracker

model = ModelBuilder()
model.eval()
tracker = build_tracker(model)
print(type(model).__name__, type(tracker).__name__)
```

Safety constraints:

- Run in a fresh Python process so the global `cfg` is not contaminated by a previous merge.
- Do not call `model.forward(data)`: the training forward path calls `.cuda()` on tensors.
- Do not call `tracker.init` or `tracker.track` unless the tracking-inference sub-skill has validated images/video and snapshot loading.
- Do not load a snapshot in this construction smoke. Checkpoint compatibility is a separate user-asset validation step.
- If `pysot` cannot import, remember that PySOT's packaging installs the `toolkit` distribution; `pysot` usually imports from a checkout/PYTHONPATH or editable-development setup.

## Snapshot/config compatibility reasoning

A snapshot is coupled to the model graph defined by the config. The most common incompatible edits are:

- Changing `BACKBONE.TYPE` or `BACKBONE.KWARGS.used_layers`.
- Turning `ADJUST.ADJUST` on/off or changing adjust channel lists.
- Changing `RPN.TYPE`, `RPN.KWARGS.in_channels`, `RPN.KWARGS.weighted`, or anchor counts.
- Switching between `SiamRPNTracker`, `SiamMaskTracker`, and `SiamRPNLTTracker`.
- Enabling/disabling `MASK.MASK` or `REFINE.REFINE`.

Expected signals for mismatch include PyTorch `size mismatch`, missing/unexpected state-dict keys, `SiamMaskTracker must have mask_head`, or downstream score/bbox reshape failures. Fix by pairing the snapshot with its original config or by retraining/exporting a checkpoint for the edited graph.

## Quick mapping checklist

Before optional construction, confirm:

- `BACKBONE.TYPE` appears in the backbone map.
- `ADJUST.TYPE` appears in the neck map when `ADJUST.ADJUST` is true.
- `RPN.TYPE` appears in the RPN map.
- `MASK.TYPE` and `REFINE.TYPE` appear in their maps when mask/refine is enabled.
- `TRACK.TYPE` appears in the tracker map.
- `ANCHOR.ANCHOR_NUM` and `RPN.KWARGS.anchor_num` agree.
- Training configs satisfy the output-size formula in [configuration.md](configuration.md).
