# Shared StarDist API conventions

## Axes and arrays

2D spatial axes are `Y,X`; common channels-last input is `YXC`. 3D spatial axes are `Z,Y,X`; common channels-last input is `ZYXC`. A channel axis is part of the input but never part of the returned instance-label spatial shape. Labels are integer, non-negative instance IDs with 0 as background. Images are normally floating point for model input.

## Prediction and thresholds

Both `StarDist2D.predict_instances` and `StarDist3D.predict_instances` use the verified signature:

```text
(img, axes=None, normalizer=None, sparse=True, prob_thresh=None,
 nms_thresh=None, scale=None, n_tiles=None, show_tile_progress=True,
 verbose=False, return_labels=True, predict_kwargs=None, nms_kwargs=None,
 overlap_label=None, return_predict=False)
```

Default prediction returns labels and details. Probability threshold filters candidates; NMS threshold controls overlap suppression. `n_tiles` is dimension-specific (2-tuple or 3-tuple). `return_predict=True` and dense mode can multiply memory use.

## Models and metadata

Use a valid local model directory with `StarDist2D(None, name=...)`/`StarDist3D(None, name=...)`, or call `from_pretrained(name)` when the registry/cache/network is available. Model configuration determines input channels, rays/grid, axes, and optional classes. Preserve model source, version, normalization, thresholds, axes, grid, ray JSON, and anisotropy with results.

## Geometry conventions

2D points are `(y,x)` and 3D points/ray vertices are `(z,y,x)`. A 2D distance tensor ends in `n_rays`; a 3D tensor ends in `len(rays)`. Grid values describe the prediction-point spacing and must be propagated to NMS/rendering. CPU compiled geometry is required; OpenCL is optional.
