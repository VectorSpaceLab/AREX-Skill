# Tracking API Reference

## Public constructors

```python
from boxmot import BoxMOT, Detector, ReIDModel
from boxmot.trackers import OccluBoost
from boxmot.trackers.registry import create_tracker, get_tracker_config
```

### `BoxMOT`

```python
BoxMOT(
    detector='yolov8n',
    reid='osnet_x0_25_msmt17',
    tracker='bytetrack',
    classes=None,
    project='runs',
    *,
    detector_kwargs=None,
    reid_kwargs=None,
    tracker_kwargs=None,
    model=None,
    recipe=None,
)
```

Relevant methods:

```python
BoxMOT.track(source=..., tracker_backend='python', ...)
BoxMOT.generate(benchmark=..., source=...)
BoxMOT.val(benchmark=..., split=..., tracker_backend='python', tracking_backend='thread')
BoxMOT.tune(benchmark=..., split=..., n_trials=10, objectives=None, maximize=None, minimize=None)
BoxMOT.research(benchmark=..., project=None, tracker_backend='python', tracking_backend='thread')
BoxMOT.train(cfg=None, recipe=None, model='csl_tinyvit_11m', dataset='market1501', data=None, data_dir=None, ...)
BoxMOT.eval_reid(weights=..., dataset=..., data_dir=..., model=None, preprocess=None, imgsz=None, inference_feature=None, flip_tta=None, ...)
BoxMOT.export(format=None, include=('onnx',), ...)
BoxMOT.embed(source=..., boxes=None, preprocess=None)
```

### `Detector`

```python
Detector(model, *, device='cpu', image_size=None, confidence=None, iou=0.7, classes=None, agnostic_nms=False, half=False, batch=1, vid_stride=1)
```

### `ReIDModel`

```python
ReIDModel(weights, *, device='cpu', half=False, preprocess=None)
```

### Tracker factory

```python
create_tracker(
    tracker_type,
    tracker_config=None,
    reid_weights=None,
    device=None,
    half=None,
    per_class=None,
    class_ids=None,
    class_names=None,
    evolve_param_dict=None,
    tracker_kwargs=None,
    reid_preprocess=None,
    reid_model=None,
    tracker_backend='python',
    precomputed_reid=False,
)
```

`get_tracker_config(tracker_type)` resolves the tracker YAML under `boxmot/configs/trackers/`.

## Tracker registry facts

`boxmot.trackers.registry.TRACKER_MAPPING` currently registers:

- `strongsort`
- `ocsort`
- `bytetrack`
- `sfsort`
- `botsort`
- `deepocsort`
- `hybridsort`
- `boosttrack`
- `occluboost`
- `sam2mot`

## Direct tracker export

The package-level tracker export is:

```python
from boxmot.trackers import OccluBoost
```

## Result objects

`tracker.update(...)` returns `boxmot.trackers.results.TrackResults`, which behaves like a NumPy array and provides these accessors:

- `xyxy` for AABB geometry
- `xywha` for OBB geometry
- `id`
- `conf`
- `cls`
- `det_ind`
- `summary()`, `to_json()`, `to_csv()`, `save_csv()`, `save_mot()`

## OBB and native support facts

- `supports_obb` is `True` for `bytetrack`, `botsort`, `ocsort`, `occluboost`, `sfsort`, `strongsort`, `deepocsort`, `hybridsort`, and `sam2mot` in the inspected repo.
- OBB detection tensors have 7 columns; OBB output tensors have 9 columns.
- `OccluBoost` is the package-level tracker export.
- `boxmot.trackers.registry.TRACKER_MAPPING` is the registry to use when the user knows only a tracker name.

## Low-level helpers worth knowing

- `boxmot.api.functional.track(source, detector, reid=None, tracker=None, verbose=True, drawer=None)`
- `boxmot.api.functional.evaluate(data, detector=None, reid=None, tracker=None, metrics=True, speed=True, verbose=False)`
- `boxmot.trackers.common.detections.layout.get_detection_layout(is_obb)`
- `boxmot.trackers.common.detections.layout.infer_detection_layout(dets)`
- `boxmot.trackers.common.geometry.obb.xywha_to_xyxy(boxes)`

Use this page when the user wants signatures, not workflow prose.
