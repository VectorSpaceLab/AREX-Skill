# Inference and Visualization Workflows

## Choose the Inference Route

| Task | Prefer | Why |
| --- | --- | --- |
| Single image, folder, URL, mixed path/array batch | `DetInferencer` | Handles inputs, batching, JSON, visualization, and progress. |
| Headless batch JSON dump | `DetInferencer(...)(..., out_dir=..., no_save_pred=False, no_save_vis=True)` | Saves machine-readable predictions without GUI or image writes. |
| Downstream filtering with tensors/data samples | `return_datasamples=True` or `inference_detector` | Keeps `DetDataSample` structures. |
| Frame-by-frame video processing | `init_detector` + `inference_detector` + visualizer | Avoids assuming GUI/codecs and allows custom frame IO. |
| Large images | slicing workflow around `inference_detector` | Needs SAHI-style tiling, NMS merge, and memory control. |
| Model ensemble visualization | multiple `DetInferencer` calls + fusion + visualizer | The demo route uses weighted boxes fusion after per-model predictions. |
| Production deployment | MMDeploy/TorchServe route | Requires external backend/service choices; see `deployment.md`. |

## Headless CPU Batch: Save Predictions Only

This is the safest route for a server with no display and no GPU.

```python
from mmdet.apis import DetInferencer

inferencer = DetInferencer(
    model='rtmdet_tiny_8xb32-300e_coco',
    weights=None,
    device='cpu',
    palette='coco',
    show_progress=True,
)

result = inferencer(
    inputs='images/',
    batch_size=2,
    out_dir='outputs',
    no_save_pred=False,
    no_save_vis=True,
    show=False,
    return_vis=False,
    pred_score_thr=0.3,
)
```

Expected output layout when prediction saving is enabled:

```text
outputs/
└── preds/
    ├── image_a.json
    └── image_b.json
```

Do not set both `no_save_pred=True` and `no_save_vis=True` if the user expects files. If both are true, `out_dir` is effectively unused.

## Save Visualizations and JSON

```python
result = inferencer(
    'image.jpg',
    out_dir='outputs',
    no_save_pred=False,
    no_save_vis=False,
    pred_score_thr=0.4,
)
```

Expected layout:

```text
outputs/
├── preds/
│   └── image.json
└── vis/
    └── image.jpg
```

Use `show=False` on remote or headless systems. Use `return_vis=True` only when the caller needs visualization arrays in memory.

## NumPy BGR Input Returning Data Samples

```python
import mmcv
from mmdet.apis import DetInferencer

image_bgr = mmcv.imread('image.jpg')
inferencer = DetInferencer('rtmdet_tiny_8xb32-300e_coco', device='cpu')
result = inferencer(image_bgr, return_datasamples=True, no_save_vis=True)
sample = result['predictions'][0]
instances = sample.pred_instances
kept = instances[instances.scores > 0.5]
```

Key details:

- MMDetection expects the NumPy array in BGR order.
- `return_datasamples=True` disables JSON conversion and returns `DetDataSample` objects.
- Saving data samples directly through `DetInferencer` is not supported; save your own filtered data if needed.

## Lower-Level API for Custom Postprocessing

```python
from mmdet.apis import init_detector, inference_detector

model = init_detector('config.py', 'checkpoint.pth', device='cuda:0')
samples = inference_detector(model, ['a.jpg', 'b.jpg'])
for sample in samples:
    instances = sample.pred_instances
    high_confidence = instances[instances.scores >= 0.6]
```

Use this when the task asks for direct structures, custom visualization, shared model lifecycle, or repeated calls inside a service loop.

## Open-Vocabulary Prompt Inference

```python
from mmdet.apis import DetInferencer

inferencer = DetInferencer('glip_atss_swin-t_a_fpn_dyhead_pretrain_obj365', device='cuda:0')
result = inferencer(
    'image.jpg',
    texts='bench . car .',
    custom_entities=True,
    pred_score_thr=0.35,
    out_dir='outputs',
    no_save_pred=False,
)
```

Notes:

- Prompt-capable models need their multimodal dependencies installed.
- `custom_entities=True` is for explicitly enumerated entity names.
- Dataset shorthand such as `$: coco` is implemented in the packaged helper script by expanding through `mmdet.evaluation.get_classes`.
- `tokens_positive` is model-specific and should be parsed as a Python literal list or `-1` only when the chosen model documents support.

## Video and Webcam Pattern

Use video/webcam scripts as patterns, not as guaranteed portable runtime commands, because codecs, displays, realtime cameras, and OpenCV build options vary by environment.

Recommended structure:

1. Initialize once with `init_detector(config, checkpoint, device=device)`.
2. Switch the first test pipeline transform to `mmdet.LoadImageFromNDArray` for frames.
3. Build a `Compose` test pipeline from `model.cfg.test_dataloader.dataset.pipeline`.
4. Build `VISUALIZERS.build(model.cfg.visualizer)` and assign `model.dataset_meta`.
5. Read frames with a video reader, call `inference_detector(model, frame, test_pipeline=test_pipeline)`, draw with `visualizer.add_datasample`, and write frames with the environment's supported codec.
6. Avoid `show=True` unless a GUI/display is confirmed.

## Large-Image Pattern

Large images should be sliced before inference and merged after inference.

Recommended structure:

1. Load the image as BGR.
2. Slice into overlapping patches with a known patch size and overlap ratio.
3. Run `inference_detector(model, patch_batch)` with a memory-safe batch size.
4. Shift patch predictions back to original coordinates.
5. Merge with NMS using a selected IoU threshold.
6. Visualize the merged `DetDataSample`; optionally dump debug patch images only when requested.

Dependencies and caveats:

- SAHI is required for the demo-style `slice_image` route.
- Test-time augmentation requires `tta_model` and `tta_pipeline` in the config.
- Batch size, patch size, and overlap directly affect memory and runtime.

## Multi-Model Fusion Pattern

The multi-model demo runs each model over the same inputs, collects `bboxes`, `scores`, and `labels`, applies weighted boxes fusion, then visualizes a synthetic `DetDataSample`.

Use it when the user explicitly asks for ensemble inference. Otherwise, prefer a single robust model route to reduce memory and calibration complexity.
