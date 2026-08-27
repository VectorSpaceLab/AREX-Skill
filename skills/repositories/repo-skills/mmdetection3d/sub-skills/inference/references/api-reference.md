# Inference API reference

This reference distills the MMDetection3D v1.4.x inference interfaces used by the demos and tests. It is written for future operating agents; it does not execute models.

## Choosing an interface

| Need | Preferred interface | Why |
| --- | --- | --- |
| Quick command for one sample | Demo command rendered by `scripts/build_inference_command.py` | File-path oriented and easy to reproduce. |
| Programmatic point-cloud detection | `LidarDet3DInferencer` or `init_model` + `inference_detector` | Inferencer handles prediction JSON/visualization; low-level API exposes data samples. |
| Programmatic monocular detection | `MonoDet3DInferencer` | Handles image arrays or paths plus camera matrices from an info file. |
| Programmatic multi-modality detection | `MultiModalityDet3DInferencer` | Handles LiDAR + image inputs plus camera matrices from an info file. |
| Programmatic LiDAR segmentation | `LidarSeg3DInferencer` or `init_model` + `inference_segmentor` | Inferencer supports arrays and output directories; low-level segmentor is file-path oriented. |

## Low-level `mmdet3d.apis` functions

### `init_model(config, checkpoint=None, device='cuda:0', palette='none', cfg_options=None)`

Purpose: construct a detector or segmentor from a config, optionally load weights, attach dataset metadata, move it to the requested device, and switch to eval mode.

Important behavior:

- `config` may be a config path, `Path`, or `mmengine.Config` object.
- `cfg_options` is merged before model construction, so it can override config values such as data roots or model settings.
- SyncBN-like normalization is converted before inference construction.
- If a checkpoint is supplied, dataset metadata and palette are taken from checkpoint metadata when available, otherwise from the test dataset metadata.
- Non-CPU devices call `torch.cuda.set_device(device)`; CPU emits a warning because some MMDetection3D functions are not fully supported on CPU.
- The returned module has `model.cfg` set and is in eval mode.

Minimal shape:

```python
from mmdet3d.apis import init_model

model = init_model('CONFIG.py', 'CHECKPOINT.pth', device='cuda:0')
```

### `inference_detector(model, pcds)`

Purpose: run point-cloud 3D detection.

Inputs:

- `pcds`: one point-cloud file path, one `numpy.ndarray`, a sequence of file paths, or a sequence of arrays.
- For file paths, the pipeline receives `lidar_points=dict(lidar_path=...)`, `timestamp=1`, and an identity `axis_align_matrix`.
- For arrays, the first test-pipeline transform is switched to `LoadPointsFromDict`, then the array is provided as `points`.

Returns:

- Single input: `(Det3DDataSample, data_dict)`.
- Batch input: `(list[Det3DDataSample], list[data_dict])`.

Limitations and cautions:

- Array dimensions must match the config pipeline's expected point layout.
- Results live under `pred_instances_3d` with boxes, labels, and scores.
- Use the inferencer class if you need output JSON files, directory input expansion, or visualization handling.

### `inference_mono_3d_detector(model, imgs, ann_file, cam_type='CAM_FRONT')`

Purpose: run monocular 3D detection with camera metadata from an info/annotation file.

Inputs:

- `imgs`: one image path or a sequence of image paths for the safest low-level usage.
- `ann_file`: an info file loadable by MMEngine whose top-level object contains `data_list`.
- `cam_type`: a key under each sample's `images` mapping; do not guess the spelling. Use the key present in the info file.

Behavior:

- The number of images must match `len(data_list)`.
- For each image, the basename must match the corresponding `data_list[index]['images'][cam_type]['img_path']` basename.
- The selected camera entry is narrowed to a single-view `images` mapping before the test pipeline runs.

Returns:

- Single input: `Det3DDataSample`.
- Batch input: `list[Det3DDataSample]`.

Limitations and cautions:

- Although the type hints mention arrays, the low-level implementation performs path-basename checks. Prefer `MonoDet3DInferencer` for ndarray images.
- The info file must contain camera calibration fields required by the model pipeline, commonly `cam2img`, `lidar2cam`, and optionally `lidar2img`.

### `inference_multi_modality_detector(model, pcds, imgs, ann_file, cam_type='CAM2')`

Purpose: run LiDAR + image 3D detection with calibration from an info/annotation file.

Inputs:

- `pcds`: one point-cloud file path or a sequence of file paths.
- `imgs`: one image file path, an image directory for multi-view `cam_type='all'`, or a sequence matching `pcds`.
- `ann_file`: an MMEngine-loadable info file with `data_list`.
- `cam_type`: camera key such as a KITTI, nuScenes, SUN RGB-D, or dataset-specific camera name; `all` is recognized for directory-based multi-view inputs when the model pipeline supports it.

Behavior:

- For batch path inputs, `pcds` and `imgs` must have equal length.
- For single-view mode, the image basename must match the selected camera's `img_path` in the info file.
- For LiDAR-coordinate models, `lidar2img` is used when present; for depth-coordinate models, `depth2img` is used.
- Timestamp is forwarded when present, which matters for multi-sweep data.

Returns:

- Single input: `(Det3DDataSample, data_dict)`.
- Batch input: `(list[Det3DDataSample], list[data_dict])`.

Limitations and cautions:

- This low-level API is primarily suitable for KITTI/SUN RGB-D-like single-view workflows. Multi-view pipelines are more constrained and should be validated against the selected config.
- For ndarray point or image inputs, prefer `MultiModalityDet3DInferencer`; the low-level function is path-oriented.

### `inference_segmentor(model, pcds)`

Purpose: run LiDAR point-cloud semantic segmentation.

Inputs:

- `pcds`: one point-cloud file path or a sequence of file paths.

Behavior:

- Test-pipeline transforms named `LoadAnnotations3D` and `PointSegClassMapping` are removed for inference.
- Each sample is passed as `lidar_points=dict(lidar_path=...)`.

Returns:

- Single input: `(Det3DDataSample, data_dict)`.
- Batch input: `(list[Det3DDataSample], list[data_dict])`.

Limitations and cautions:

- The low-level segmentor has a TODO for loaded point arrays. Use `LidarSeg3DInferencer` if ndarray input is needed.
- Predictions are exposed through `pred_pts_seg`, commonly `pts_semantic_mask`.

## Inferencer classes

All inferencer classes inherit common behavior:

```python
results = inferencer(
    inputs,
    batch_size=1,
    out_dir='outputs',
    show=False,
    pred_score_thr=0.3,
    no_save_vis=False,
    no_save_pred=False,
    print_result=False,
    return_datasamples=False,
)
```

Returned object shape:

- `results['predictions']`: dictionaries by default, or `Det3DDataSample` objects when `return_datasamples=True`.
- `results['visualization']`: visualization arrays only when requested/available.
- Prediction JSON files are saved under `out_dir/preds/` when `out_dir` is non-empty and `no_save_pred=False`.

Constructor shape:

```python
InferencerClass(
    model='MODEL_ALIAS_OR_CONFIG.py',
    weights='CHECKPOINT.pth',
    device='cuda:0',
    scope='mmdet3d',
    palette='none',
)
```

Notes:

- `model` may be a model alias from metafiles or a config path. If `weights` is omitted and `model` is an alias with registered weights, actual inference may trigger checkpoint download.
- If `device=None`, MMEngine chooses an available device. For reproducibility, pass `cuda:0` or another explicit device when possible.
- `return_vis=True` can be passed as a call keyword when you need returned visualization arrays; saved visualization still depends on task and display behavior.

### `LidarDet3DInferencer`

Registered names include `LidarDet3DInferencer` and `det3d-lidar`.

Inputs:

```python
inputs = dict(points='sample.bin')
# or dict(points=points_array)
# or [dict(points='a.bin'), dict(points='b.bin')]
# or dict(points='directory_of_point_cloud_files')
```

Pipeline requirements:

- The config test pipeline must contain `LoadPointsFromFile`.
- The loader records `coord_type`, `load_dim`, and `use_dim`; ndarray inputs must match these expectations.

Output behavior:

- JSON predictions are written to `out_dir/preds/<point_cloud_stem>.json`.
- Open3D LiDAR visualization files are only saved when visualization is actually shown; on headless servers, rely on JSON predictions or use a display-capable/virtual-display environment.

### `LidarSeg3DInferencer`

Registered names include `LidarSeg3DInferencer` and `seg3d-lidar`.

Inputs mirror `LidarDet3DInferencer`.

Pipeline requirements:

- The config test pipeline must contain `LoadPointsFromFile`.
- `LoadAnnotations3D` and `PointSegClassMapping` are removed because they are training/evaluation annotation transforms, not inference transforms.

Output behavior:

- JSON predictions are written to `out_dir/preds/<point_cloud_stem>.json` and include segmentation masks.
- Visualization uses the LiDAR visualizer and is display-sensitive like LiDAR detection.

### `MonoDet3DInferencer`

Registered names include `MonoDet3DInferencer` and `det3d-mono`.

Inputs:

```python
inputs = dict(img='image.png', infos='sample_infos.pkl')
# or dict(img=image_array, infos='sample_infos.pkl')
# or a list where each item has img and infos
```

Metadata requirements:

- `infos` must load to a mapping with a `data_list` list.
- Each selected camera entry must provide the calibration needed by the pipeline, usually `cam2img` and `lidar2cam`; `lidar2img` is computed if missing.
- For list inputs, each `infos` file is expected to contain one sample.

Camera handling:

- Pass `cam_type='CAM2'`, `cam_type='CAM_FRONT'`, or another exact key from the info file as a call keyword.
- Saved image visualization goes under `out_dir/vis_camera/<cam_type>/<image_name>`.

### `MultiModalityDet3DInferencer`

Registered names include `MultiModalityDet3DInferencer` and `det3d-multi_modality`.

Inputs:

```python
inputs = dict(points='sample.bin', img='sample.png', infos='sample_infos.pkl')
# or dict(points=points_array, img=image_array, infos='sample_infos.pkl')
# or a list of per-sample dictionaries
```

Metadata and pipeline requirements:

- `infos` has the same `data_list` and camera-calibration expectations as monocular inference.
- The config test pipeline must contain both `LoadPointsFromFile` and `LoadImageFromFile`.
- Pipelines using `LoadMultiViewImageFromFiles` are warned as unsupported by this inferencer; use single-view inputs unless the selected model/config has been validated separately.
- Directory input expansion is supported only when both image and point-cloud paths are directories and their file counts match.

Output behavior:

- JSON predictions are written to `out_dir/preds/<point_cloud_or_image_stem>.json`.
- Camera visualization can be saved under `out_dir/vis_camera/<cam_type>/`; LiDAR/Open3D output remains display-sensitive.
