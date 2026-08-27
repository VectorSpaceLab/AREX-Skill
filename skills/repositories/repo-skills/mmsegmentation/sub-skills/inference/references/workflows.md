# Inference Workflows

## Workflow: local config/checkpoint image inference

1. Confirm the user has a local config, checkpoint, and image. A config without a checkpoint can only prove the pipeline runs; it cannot produce meaningful predictions.
2. Pick the device. Use `cuda:0` only when `torch.cuda.is_available()` is true; otherwise use `cpu`.
3. Run `init_model(config, checkpoint, device=device)`. If `device == 'cpu'`, apply `revert_sync_batchnorm(model)` before inference.
4. Run `inference_model(model, image)`.
5. Save visualization with `show_result_pyplot(..., draw_gt=False, show=False, out_file='...')` for headless or batch automation.
6. If the user needs raw predicted labels, read `result.pred_sem_seg.data[0]` and save it as a numeric mask with a format that preserves label indices.

Minimal pattern:

```python
from pathlib import Path
import numpy as np
from PIL import Image
from mmengine.model import revert_sync_batchnorm
from mmseg.apis import init_model, inference_model, show_result_pyplot

model = init_model(config, checkpoint, device=device)
if device == 'cpu':
    model = revert_sync_batchnorm(model)
result = inference_model(model, image)
show_result_pyplot(model, image, result, draw_gt=False, show=False, out_file=overlay_path)
mask = result.pred_sem_seg.data[0].cpu().numpy().astype(np.uint8)
Image.fromarray(mask).save(mask_path)
```

## Workflow: one-call inferencer for saved overlays and masks

1. Prefer a local config path and local `weights` in automation.
2. Use a model alias only when the user explicitly accepts possible checkpoint downloads and cache use.
3. Pass `out_dir` to save both visualization and predicted masks.
4. Pass `show=False` on servers and CI.
5. Pass `dataset_name`, `classes`, or `palette` when checkpoint metadata is missing or a custom dataset uses non-Cityscapes classes.

Pattern:

```python
from mmseg.apis import MMSegInferencer

inferencer = MMSegInferencer(
    model=config_or_alias,
    weights=checkpoint_or_none,
    dataset_name='cityscapes',
    device='cpu',
)
outputs = inferencer(
    inputs,
    show=False,
    out_dir='outputs/inferencer',
    img_out_dir='vis',
    pred_out_dir='pred',
    opacity=0.5,
    with_labels=False,
)
```

Expected saved files:

- `outputs/inferencer/vis/<input-name>` for rendered overlays.
- `outputs/inferencer/pred/00000000_pred.png` for semantic segmentation label masks.
- `outputs/inferencer/pred/00000000_pred.npy` for depth-map style outputs.

## Workflow: batch and directory inference

`MMSegInferencer` accepts one image path, one `np.ndarray`, a list of images, or a directory path. For large directories:

- Use `batch_size=1` first to reduce memory pressure.
- Confirm output naming is acceptable; prediction files are numbered rather than source-name-preserving.
- Keep `show=False` and `return_vis=False` unless the user needs image arrays returned in memory.
- Save outputs with `out_dir` rather than collecting all arrays in Python for large jobs.

## Workflow: video inference

The demo pattern uses OpenCV for frames and the lower-level API for each frame:

1. Open video input with `cv2.VideoCapture`; a digit string can mean webcam id.
2. Require at least one output: display (`--show`) or video writer (`--output-file`).
3. Run `inference_model(model, frame)` for each frame.
4. Render with `show_result_pyplot(model, frame, result, ...)`.
5. Resize rendered frames to the writer dimensions if needed.
6. Release the writer and capture in a `finally` block.

Headless servers should use `--output-file` and avoid OpenCV display windows.

## Workflow: local visualization without inference

Use `SegLocalVisualizer` when the task is to render an existing `SegDataSample`, ground-truth mask, or synthetic sample:

1. Build `PixelData` for `gt_sem_seg`, `pred_sem_seg`, `gt_depth_map`, or `pred_depth_map`.
2. Create a `SegDataSample` and attach the field.
3. Initialize `SegLocalVisualizer(vis_backends=[dict(type='LocalVisBackend')], save_dir='outputs/vis')`.
4. Set `dataset_meta = {'classes': ..., 'palette': ...}` with matching lengths.
5. Call `add_datasample(name, image, data_sample, show=False, out_file='...')`.

`draw_gt=True` and `draw_pred=True` stitches ground truth and prediction side by side. Use `draw_gt=False` for prediction-only overlays.

## Workflow: remote-sensing tiled inference

Use this only after verifying GDAL is importable:

```python
try:
    from osgeo import gdal  # noqa: F401
except ImportError as exc:
    raise RuntimeError('Remote-sensing inference requires GDAL/osgeo bindings') from exc
```

Then:

1. Initialize `RSInferencer.from_config_path(config, checkpoint, batch_size=1, thread=1, device=device)` or `RSInferencer.from_model(model, checkpoint_path=..., ...)`.
2. Wrap the input raster with `RSImage(image_path)`.
3. Choose `window_size=(width, height)` that matches the model crop size or config test assumptions.
4. Choose `strides` equal to `window_size` for non-overlap, or smaller for overlap. Smaller strides increase runtime and memory pressure.
5. Run `inferencer.run(image, window_size, strides, output_path)`.
6. Confirm the output is a one-band label raster and preserves geotransform/projection.

Remote-sensing data conversion and dataset config design belong in `../data-configuration/SKILL.md`; this sub-skill only covers inference once model and raster inputs already exist.

## Workflow: feature/depth visualization

Feature-map visualization uses `SegLocalVisualizer.draw_featmap` plus explicit forward hooks on named modules. It may require WandB or other visualization backends and is not the default path for ordinary prediction overlays.

Depth-map style results are handled by `SegLocalVisualizer._draw_depth_map` and inferencer postprocessing as `.npy` outputs. Verify that the chosen model actually returns `pred_depth_map` before promising depth outputs.
