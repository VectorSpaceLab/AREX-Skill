# Inference API Reference

## Environment Assumptions

- MMDetection package version: `mmdet==3.3.0`.
- Install full `mmcv`, not `mmcv-lite`, when models or imports need `mmcv.ops`.
- Device strings are passed through PyTorch conventions such as `cpu`, `cuda`, and `cuda:0`.
- Image arrays are NumPy arrays in BGR channel order for MMDetection public inference APIs.

## `DetInferencer`

`DetInferencer` is the preferred high-level API for ordinary image, folder, list, URL, NumPy-array, visualization, and JSON prediction workflows.

### Constructor

```python
from mmdet.apis import DetInferencer

inferencer = DetInferencer(
    model='rtmdet_tiny_8xb32-300e_coco',
    weights=None,
    device='cpu',
    scope='mmdet',
    palette='none',
    show_progress=True,
)
```

Verified signature:

```text
DetInferencer.__init__(model=None, weights=None, device=None, scope='mmdet', palette='none', show_progress=True)
```

Important behavior:

- `model` can be a model alias, config path, or model object accepted by OpenMMLab inferencer machinery.
- `weights` can be a local path or URL; if omitted for a known model alias, metadata may provide default weights.
- If `model` is omitted, `weights` must contain enough MMEngine checkpoint metadata to recover the config.
- `palette` priority is explicit argument, then config/test dataset metainfo, then checkpoint metadata, then random fallback.
- If no checkpoint is loaded, predictions come from random weights and COCO classes are used by default.

### Call

```python
result = inferencer(
    inputs='images/',
    batch_size=4,
    return_vis=False,
    show=False,
    no_save_vis=True,
    pred_score_thr=0.3,
    return_datasamples=False,
    no_save_pred=False,
    out_dir='outputs',
)
```

Verified signature:

```text
DetInferencer.__call__(inputs, batch_size=1, return_vis=False, show=False, wait_time=0, no_save_vis=False, draw_pred=True, pred_score_thr=0.3, return_datasamples=False, print_result=False, no_save_pred=True, out_dir='', texts=None, stuff_texts=None, custom_entities=False, tokens_positive=None, **kwargs)
```

Inputs can be:

- a string image path or URL;
- a directory path containing supported image extensions;
- a NumPy BGR image array;
- a list or tuple mixing image paths and arrays.

Return format:

- `result['predictions']` contains JSON-serializable dicts by default, or `DetDataSample` objects when `return_datasamples=True`.
- `result['visualization']` contains visualization arrays only when visualization is requested with `return_vis=True`, `show=True`, or a saving path.
- JSON prediction files are written under `out_dir/preds/` only when `out_dir` is non-empty and `no_save_pred=False`.
- Visualization images are written under `out_dir/vis/` unless `no_save_vis=True`.

Open-vocabulary parameters:

- `texts` supplies text prompts for GLIP/Grounding-DINO style models.
- `custom_entities=True` means class names are provided explicitly, commonly in `"class1 . class2 ."` form.
- `tokens_positive` narrows Grounding DINO token spans when supported by the model.
- `stuff_texts` is for open panoptic tasks.

## `init_detector` + `inference_detector`

Use the lower-level pair when code needs a reusable initialized model, direct `DetDataSample` objects, custom test pipelines, frame-by-frame video processing, or manual visualization.

```python
from mmdet.apis import init_detector, inference_detector

model = init_detector('config.py', 'checkpoint.pth', device='cuda:0', palette='coco')
result = inference_detector(model, ['a.jpg', 'b.jpg'])
```

Verified signatures:

```text
init_detector(config, checkpoint=None, palette='none', device='cuda:0', cfg_options=None)
inference_detector(model, imgs, test_pipeline=None, text_prompt=None, custom_entities=False)
```

Behavior notes:

- `init_detector` accepts a config path, `pathlib.Path`, or `mmengine.Config` object.
- `cfg_options` merges overrides before model construction; when omitted, some backbone `init_cfg` entries are disabled for inference.
- The returned model has `model.cfg` attached and is set to eval mode on the requested device.
- `inference_detector` returns one `DetDataSample` for a single input or a list for a list/tuple input.
- For NumPy inputs, the test pipeline is switched to `mmdet.LoadImageFromNDArray` when MMDetection builds the pipeline.
- CPU inference asserts that unsupported `RoIPool` modules are not present.

## Visualization API

- `DetInferencer` initializes the configured visualizer and attaches `model.dataset_meta`.
- Manual workflows can build `VISUALIZERS.build(model.cfg.visualizer)` and set `visualizer.dataset_meta = model.dataset_meta`.
- `DetLocalVisualizer.add_datasample(...)` draws predictions, masks, and labels from `DetDataSample`.
- Palettes accept dataset names such as `coco`, `voc`, `citys`, `random`, common color strings, tuples, or explicit lists.

## Output Naming

- File-path inputs keep the input basename for `vis/` and `preds/` outputs.
- NumPy-array inputs are named with counters such as `00000000.jpg` for visualizations and numeric JSON stems for predictions.
- Panoptic predictions may additionally dump `_panoptic_seg.png` outputs in `preds/`.
