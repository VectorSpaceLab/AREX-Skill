# Tracker API reference

This reference covers the inference-time API surface used by PySOT demos and tests.

## Build sequence

1. Merge the config before constructing the model or tracker:

   ```python
   from pysot.core.config import cfg
   cfg.merge_from_file("path/to/config.yaml")
   ```

2. Build the model from the global config:

   ```python
   from pysot.models.model_builder import ModelBuilder
   model = ModelBuilder()
   ```

3. Load a matching snapshot and set evaluation mode/device.
4. Build the tracker:

   ```python
   from pysot.tracker.tracker_builder import build_tracker
   tracker = build_tracker(model)
   ```

`build_tracker(model)` dispatches only on `cfg.TRACK.TYPE`:

| `cfg.TRACK.TYPE` | Class | Typical use |
| --- | --- | --- |
| `SiamRPNTracker` | `pysot.tracker.siamrpn_tracker.SiamRPNTracker` | Standard short-term box tracking. |
| `SiamMaskTracker` | `pysot.tracker.siammask_tracker.SiamMaskTracker` | Box plus mask/polygon tracking; model must include mask/refine heads. |
| `SiamRPNLTTracker` | `pysot.tracker.siamrpnlt_tracker.SiamRPNLTTracker` | Long-term mode with confidence thresholds and larger search after loss. |

Any other value raises a lookup failure in the tracker builder. Use the bundled validator to catch this before a run.

## Image and bbox conventions

- Images are OpenCV-style `numpy.ndarray` values in BGR channel order with shape `[height, width, channels]`.
- `tracker.init(img, bbox)` takes a 0-based rectangle `[x, y, width, height]` in pixels. OpenCV `selectROI` returns this convention.
- `tracker.track(img)` must be called sequentially on later frames after one successful `init` call.
- Returned boxes are floats in `[x, y, width, height]`. Convert to `int` only for drawing or for a target output format that requires integer coordinates.
- For VOT polygon ground truth, PySOT uses `get_axis_aligned_bbox(region)` to turn either `[x,y,w,h]` or an 8-value polygon into center/size, then converts back to `[x,y,w,h]` for initialization.

Useful bbox helpers:

| Helper | Purpose |
| --- | --- |
| `get_axis_aligned_bbox(region)` | Convert 4-value rect or 8-value polygon to `(cx, cy, w, h)`. |
| `cxy_wh_2_rect(pos, sz)` | Convert center/size to 0-based `[x, y, w, h]`. |
| `rect_2_cxy_wh(rect)` | Convert 0-based `[x, y, w, h]` to center and size arrays. |
| `center2corner` / `corner2center` | Convert between center and corner boxes for arrays or namedtuples. |

## `init(img, bbox)` behavior

For Siamese trackers, initialization:

- Stores target center and size from the initial box.
- Computes context crop size from `TRACK.CONTEXT_AMOUNT` and `TRACK.EXEMPLAR_SIZE`.
- Computes per-channel image average for padding.
- Extracts a template crop and calls `model.template(z_crop)`.

If `cfg.CUDA` is true, crop tensors are moved to CUDA inside the crop helper, so the model and config device settings must agree.

## `track(img)` outputs

### `SiamRPNTracker`

Returns:

```python
{
    "bbox": [x, y, width, height],
    "best_score": float,
}
```

The tracker updates its internal center and size each frame. Width and height are clipped to at least 10 pixels and not beyond image bounds. A low `best_score` can indicate poor target match, wrong first-frame box, wrong config/snapshot pair, or a severe appearance change.

### `SiamMaskTracker`

Returns:

```python
{
    "bbox": [x, y, width, height],
    "best_score": float,
    "mask": mask_in_image,
    "polygon": [x1, y1, x2, y2, x3, y3, x4, y4],
}
```

`mask` is an image-sized mask probability/activation array after crop-back. `polygon` is the flattened minimum-area rectangle around the largest mask contour, or a rectangle derived from the box when the mask is empty. The config key is spelled `TRACK.MASK_THERSHOLD` in PySOT.

`SiamMaskTracker` asserts that the model has `mask_head` and `refine_head`; a plain SiamRPN snapshot/config cannot be used as a mask tracker.

### `SiamRPNLTTracker`

Returns the same keys as `SiamRPNTracker` and additionally manages long-term search state internally:

- If `best_score < TRACK.CONFIDENCE_LOW`, it keeps the previous center/size and enters long-term search.
- If `best_score > TRACK.CONFIDENCE_HIGH`, it exits long-term search.
- In long-term state, it uses `TRACK.LOST_INSTANCE_SIZE`; otherwise it uses `TRACK.INSTANCE_SIZE`.

## Minimal direct-use checklist

- Config is merged before `ModelBuilder()`.
- Snapshot matches the config family and tracker type.
- Model is in `.eval()` mode.
- Model device matches `cfg.CUDA` and crop tensor device.
- The first frame is a valid BGR image; `cv2.imread` returning `None` must be treated as a hard input error.
- Initial bbox is within frame bounds, uses positive width/height, and is 0-based.
- `track` is not called before `init`.
- For mask workflows, `cfg.MASK.MASK` is true and the model has mask/refine heads.

## Common API symptoms

| Symptom | Likely cause | Next step |
| --- | --- | --- |
| `KeyError` from tracker builder | Unsupported `TRACK.TYPE` | Validate the config and route model/config edits to `configuration-models`. |
| `AssertionError: SiamMaskTracker must have mask_head` | Mask tracker selected with non-mask model/config | Use a SiamMask config/snapshot or switch tracker type. |
| CUDA tensor/device mismatch | `cfg.CUDA`, model device, and crop device disagree | Set `cfg.CUDA = torch.cuda.is_available() and cfg.CUDA`, move model to the same device. |
| Empty/poor mask polygon | Wrong mask config/snapshot, bad initial bbox, or threshold issue | Confirm `MASK.MASK`, snapshot family, and `TRACK.MASK_THERSHOLD`. |
| Bbox drifts immediately | Wrong first-frame ROI, non-BGR input, frame resize mismatch, or wrong snapshot | Recheck input image loading and config/snapshot pair. |
