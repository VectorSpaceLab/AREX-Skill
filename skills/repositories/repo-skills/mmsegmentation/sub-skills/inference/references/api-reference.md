# Inference API Reference

## Verified public API

Installed inspection confirmed these MMSegmentation 1.2.2 exports:

- `mmseg.apis.init_model(config, checkpoint=None, device='cuda:0', cfg_options=None)`
- `mmseg.apis.inference_model(model, img)`
- `mmseg.apis.show_result_pyplot(model, img, result, opacity=0.5, title='', draw_gt=True, draw_pred=True, wait_time=0, show=True, with_labels=True, save_dir=None, out_file=None)`
- `mmseg.apis.MMSegInferencer(model, weights=None, classes=None, palette=None, dataset_name=None, device=None, scope='mmseg')`
- `mmseg.apis.RSInferencer(model, batch_size=1, thread=1)`
- `mmseg.apis.RSImage(image)`

## `MMSegInferencer`

`MMSegInferencer` is the highest-level entry point for semantic segmentation and depth-style outputs.

```python
from mmseg.apis import MMSegInferencer

inferencer = MMSegInferencer(
    model='PATH/TO/MMSEG_CONFIG.py',
    weights='PATH/TO/CHECKPOINT.pth',
    dataset_name='cityscapes',
    device='cpu',
)
result = inferencer(
    'PATH/TO/IMAGE.png',
    show=False,
    out_dir='outputs/inferencer',
    img_out_dir='vis',
    pred_out_dir='pred',
    opacity=0.5,
    with_labels=False,
)
```

Important behavior:

- `model` can be a model alias from MMSegmentation metafiles, a config path, or a `Config`/config dict object.
- If `model` is a known alias and `weights` is omitted, MMEngine may download the configured checkpoint. Avoid aliases in offline or deterministic automation unless the user explicitly approves network access.
- If `model` is a config path, pass a local `weights` file for meaningful predictions. Without weights, predictions come from random initialization and should only be used for pipeline smoke tests.
- `device=None` lets the inferencer select an available device. Pass `device='cpu'` for CPU-only hosts or deterministic CI.
- On CPU or when CUDA is unavailable, `MMSegInferencer` reverts SyncBN layers internally.
- `out_dir` controls saved outputs. The default subdirectories are `vis/` for rendered overlays and `pred/` for predicted masks.
- With `return_datasamples=False`, the result is a dict with `predictions` and `visualization`. `predictions` is a label-index segmentation map or depth map array. With `return_datasamples=True`, the return is a `SegDataSample` or list of samples.

## `init_model` + `inference_model`

Use the lower-level API when the agent needs explicit control over model lifetime, frame loops, or the returned `SegDataSample`.

```python
from mmengine.model import revert_sync_batchnorm
from mmseg.apis import init_model, inference_model, show_result_pyplot

model = init_model(
    'PATH/TO/MMSEG_CONFIG.py',
    'PATH/TO/CHECKPOINT.pth',
    device='cpu',
)
model = revert_sync_batchnorm(model)
result = inference_model(model, 'PATH/TO/IMAGE.png')
show_result_pyplot(
    model,
    'PATH/TO/IMAGE.png',
    result,
    opacity=0.5,
    draw_gt=False,
    draw_pred=True,
    show=False,
    with_labels=False,
    out_file='outputs/demo_overlay.png',
)
```

Important behavior:

- `config` may be a file path, `Path`, or `mmengine.Config`.
- `checkpoint=None` builds the model without trained weights. Use only for smoke checks or when the user explicitly accepts random weights.
- `cfg_options` can override config values before model construction.
- `inference_model(model, img)` accepts one image path, one `np.ndarray`, or a list/tuple of paths/arrays. It returns a `SegDataSample` for one input or a list for batch input.
- `show_result_pyplot` reads path inputs as RGB, creates a `SegLocalVisualizer`, and returns the drawn RGB image array.
- For headless runs, set `show=False` and pass `out_file` or `save_dir`; do not rely on popup windows.

## `SegDataSample` and predicted masks

`SegDataSample` is the common inference result container. For semantic segmentation, inspect:

- `result.pred_sem_seg.data`: tensor-like label-index mask, usually shape `[1, H, W]`.
- `result.seg_logits.data`: logits if the model/config returns them.
- `result.gt_sem_seg.data`: ground truth when a sample includes labels.

For depth-style results, visualizer and inferencer paths can use `pred_depth_map` or `gt_depth_map` when present.

## Labels, palettes, and dataset metadata

Visualization requires aligned class names and palettes:

- Checkpoints may store `dataset_meta` with `classes` and `palette`; `init_model` attaches this metadata to `model.dataset_meta`.
- Older checkpoints may store `CLASSES` and `PALETTE`; MMSegmentation maps these to `model.dataset_meta`.
- If metadata is missing, MMSegmentation warns and tries a dataset with matching `num_classes`; otherwise it falls back to Cityscapes.
- `MMSegInferencer(classes=..., palette=...)` overrides dataset metadata. `dataset_name=...` is a convenient alias-based fallback.
- `SegLocalVisualizer.set_dataset_meta` asserts that `len(classes) == len(palette)`.

## Remote-sensing API

Remote-sensing inference uses geospatial raster helpers:

```python
from mmseg.apis import RSImage, RSInferencer

inferencer = RSInferencer.from_config_path(
    'PATH/TO/REMOTE_SENSING_CONFIG.py',
    'PATH/TO/REMOTE_SENSING_CHECKPOINT.pth',
    batch_size=1,
    thread=1,
    device='cpu',
)
image = RSImage('input.tif')
inferencer.run(image, window_size=(512, 512), strides=(512, 512), output_path='output_label.tif')
```

Important behavior:

- `RSImage` imports and uses `osgeo.gdal`; actual geospatial image use requires GDAL bindings.
- `RSImage.create_grids(window_size, stride)` creates tiled windows. A zero stride component means use the corresponding window size.
- `RSInferencer` reads tiles, runs `model.test_step`, and writes a one-band label GeoTIFF with the source geotransform and projection.
- Keep `batch_size` and `thread` conservative unless the user confirms memory and IO capacity.
