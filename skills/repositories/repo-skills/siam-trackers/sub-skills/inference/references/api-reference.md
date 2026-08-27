# NanoTrack Inference API Reference

## Public construction surface

| Surface | Signature / shape | Operating contract |
|---|---|---|
| Global configuration | `nanotrack.core.config.cfg` | Mutable YACS configuration shared by model and tracker modules. Merge one variant before construction; use a fresh process to switch variants. |
| Model | `ModelBuilder()` | Takes no arguments. Reads `cfg` to build backbone, optional neck, and BAN head. `template(z)` caches template features as `model.zf`; `track(x)` returns raw `cls` and `loc` tensors. |
| Checkpoint loader | `load_pretrain(model, pretrained_path)` | Accepts a direct state dict or a mapping containing `state_dict`, strips a leading `module.`, requires at least one overlapping key, and loads with `strict=False`. Missing/unused keys therefore still need review. |
| Tracker factory | `build_tracker(model)` | Dispatches on `cfg.TRACK.TYPE`. The maintained registry contains `NanoTracker`; an unknown type raises a key error. |
| Tracker | `NanoTracker(model)` | Calls `model.eval()`, builds its point grid and Hanning window from current config, and owns mutable target state. |
| Initialize | `tracker.init(img, bbox)` | `img` is a BGR HWC array. `bbox` is zero-based `[x, y, w, h]`. Extracts a template crop and stores template features on the model. Returns no prediction. |
| Advance | `tracker.track(img)` | Extracts a search crop around prior state, runs the model, penalizes/smooths the prediction, updates state, and returns a mapping. |
| Result | `{"bbox": [x, y, w, h], "best_score": scalar}` | Box values are floating point. Score is the foreground softmax value at the selected location. |

`ModelBuilder.forward(data)` contains training-oriented behavior and an alternate
speed-test branch. For ordinary inference, use the explicit `template` and
`track` methods through `NanoTracker` rather than calling `forward` with a
mapping.

## Construction timing

Several values are captured before the first frame:

- `ModelBuilder()` reads backbone, neck, and BAN settings at model construction.
- `NanoTracker(model)` reads output size and stride to create a flattened point
  grid and Hanning window.
- `init` reads exemplar size and context amount, computes target center/size and
  channel mean, then stores model template features.
- each `track` reads current state plus instance size and tracking
  hyperparameters, then updates center and size.

Changing backbone/head/channel settings after model construction is invalid.
Changing `POINT.STRIDE` or `TRACK.OUTPUT_SIZE` after tracker construction leaves
cached arrays inconsistent. Set every inference field first.

## Core configuration fields

| Field | Core default | Maintained inference meaning |
|---|---:|---|
| `CUDA` | `True` | Whether extracted template/search tensors call `.cuda()`. Override from the resolved model device. |
| `BACKBONE.TYPE` | `res50` | Must be replaced by the selected NanoTrack variant backbone. |
| `BACKBONE.KWARGS` | empty | Maintained variants use `used_layers: [4]`. |
| `ADJUST.ADJUST` | `True` | Enables the neck. Maintained variants use `AdjustLayer`. |
| `ADJUST.KWARGS.in_channels` | unset | 64 for V1/V2, 96 for V3. |
| `ADJUST.KWARGS.out_channels` | unset | 64 for V1/V2, 96 for V3. |
| `BAN.BAN` | `False` | Must be `True` for NanoTrack inference. |
| `BAN.TYPE` | `MultiBAN` | Must be `DepthwiseBAN` for maintained variants. |
| `BAN.KWARGS.in_channels` | unset | 64 for V1/V2, 96 for V3. |
| `BAN.KWARGS.out_channels` | unset | 64 for V1/V2, 96 for V3. |
| `POINT.STRIDE` | `8` | Maintained V1/V2/V3 variant setting is 16. |
| `TRACK.TYPE` | `NanoTracker` | Factory selector. |
| `TRACK.EXEMPLAR_SIZE` | `127` | Square template crop supplied to the model. |
| `TRACK.INSTANCE_SIZE` | `255` | Square search crop supplied for each later frame. |
| `TRACK.OUTPUT_SIZE` | `16` | Point-grid side: 16 for V1/V2; explicitly 15 for V3. |
| `TRACK.BASE_SIZE` | `8` | Maintained variant YAMLs set 7; current tracker uses explicit `OUTPUT_SIZE` rather than recomputing from base size. |
| `TRACK.CONTEXT_AMOUNT` | `0.5` | Context added around target for crop sizing. |
| `TRACK.PENALTY_K` | `0.16` | Scale/aspect-ratio change penalty. Variant-specific. |
| `TRACK.WINDOW_INFLUENCE` | `0.46` | Hanning-window influence. Variant-specific. |
| `TRACK.LR` | `0.34` | State size interpolation factor. Variant-specific. |

The core defaults describe fallback library state, not a valid variant pairing.
Always merge or create an explicit inference profile.

## Variant matrix

| Property | V1 | V2 | V3 |
|---|---:|---:|---:|
| Backbone type | `mobilenetv3_small` | `mobilenetv3_small` | `mobilenetv3_small_v3` |
| Head module | `nanotrack.models.head.ban_v1` | `nanotrack.models.head.ban_v2` | `nanotrack.models.head.ban_v3` |
| Neck/head channels | 64 | 64 | 96 |
| Point stride | 16 | 16 | 16 |
| Output size | 16 (core default in historical YAML) | 16 (core default in historical YAML) | 15 (explicit) |
| Exemplar / instance | 127 / 255 | 127 / 255 | 127 / 255 |
| Base size | 7 | 7 | 7 |
| Context amount | 0.5 | 0.5 | 0.5 |
| Window influence | 0.462 | 0.490 | 0.455 |
| Penalty K | 0.148 | 0.150 | 0.138 |
| Tracking LR | 0.390 | 0.385 | 0.348 |

V1 and V2 differ in implementation even where YAML architecture fields match.
Selecting a YAML does not change the module-level BAN registry. Register the
matching module before constructing the model:

```python
import importlib
import nanotrack.models.head as head_registry

module = importlib.import_module(f"nanotrack.models.head.ban_{variant}")
head_registry.BANS["UPChannelBAN"] = module.UPChannelBAN
head_registry.BANS["DepthwiseBAN"] = module.DepthwiseBAN
```

This explicit registry update avoids source edits. Run only one variant per
process; changing module imports and merging another config into the same global
object is vulnerable to stale fields, especially V1/V2 YAMLs that historically
omit `TRACK.OUTPUT_SIZE` and rely on the core value 16.

## Frame contract

A safe frame adapter should enforce:

```python
frame = np.asarray(frame)
if frame.ndim != 3 or frame.shape[2] != 3 or frame.size == 0:
    raise ValueError("expected nonempty HxWx3 BGR frame")
if frame.dtype != np.uint8:
    raise TypeError("convert explicitly to uint8 without changing value range")
frame = np.ascontiguousarray(frame)
```

NanoTrack does no RGB-to-BGR conversion or normalization in the tracker crop
path. OpenCV decode normally produces BGR. Convert RGB/PIL inputs explicitly;
do not merely relabel them. Convert grayscale with `GRAY2BGR` and discard alpha
with an explicit color transform before validation.

The crop path pads outside-image regions with the frame's per-channel mean,
resizes to exemplar/search size, transposes HWC to NCHW, adds a batch dimension,
casts to float32, and moves to CUDA only when `cfg.CUDA` is true.

## Initialization box contract

- order: `[x, y, width, height]`, never `[x1, y1, x2, y2]`;
- origin: zero-based top-left image coordinates;
- values: finite numeric scalars;
- dimensions: `width > 0`, `height > 0`;
- recommended range: fully inside `[0, frame_width] x [0, frame_height]`.

Initialization converts the box to center as
`[x + (w - 1)/2, y + (h - 1)/2]`. A caller that uses corner coordinates by
mistake can produce huge crops or invalid state without an early, clear error.
Use the bundled checker before model execution.

## Output and clipping contract

Tracking decodes the four regression channels around a point grid, applies
scale/aspect penalties and a Hanning window, selects one location, smooths size,
and clips center/size. Width and height are forced to at least 10 pixels during
tracking and at most the image dimensions. The final top-left corner is derived
after that clip, so it can still be negative near an edge.

For a consumer that requires an in-frame integer rectangle:

```python
x, y, w, h = map(float, result["bbox"])
x1 = max(0, min(frame_width, x))
y1 = max(0, min(frame_height, y))
x2 = max(0, min(frame_width, x + w))
y2 = max(0, min(frame_height, y + h))
if x2 <= x1 or y2 <= y1:
    raise ValueError("prediction has no in-frame area")
draw_box = tuple(map(round, (x1, y1, x2 - x1, y2 - y1)))
```

Keep the original floating box for tracker state or result serialization unless
the downstream protocol explicitly demands clipping/rounding.

## State ownership and concurrency

`NanoTracker` stores `center_pos`, `size`, `channel_average`, point grid, and
window. `ModelBuilder.template` stores `zf` on the model. Therefore:

- one tracker instance is one temporal target state;
- two tracker instances sharing one model share template state and interfere;
- copying only the tracker box is insufficient to clone a target;
- frame-level parallel calls on one tracker/model are unsafe;
- a fresh model and tracker per concurrent target is the simplest correct
  policy, at the cost of duplicated weights.

For batched or multi-object tracking, first design explicit template-feature
storage and synchronization; do not assume this single-object API is stateless.

## Checkpoint loading semantics

`load_pretrain` maps checkpoint storage to CPU, unwraps `state_dict` when
present, removes a leading `module.`, checks key overlap, and loads with
`strict=False`. Its return does not prove an exact architecture match:

1. require the checkpoint file to exist before constructing the runtime;
2. pair checkpoint, config profile, and head variant by version;
3. capture missing and unused key logs;
4. treat any unexpected architecture keys as a failure unless deliberately
   reviewed;
5. run at least one initialized frame and one tracked frame before integrating
   a new checkpoint into a service.

Do not fetch checkpoints implicitly. Checkpoint provenance, license, and digest
belong to the caller's asset-management process.
