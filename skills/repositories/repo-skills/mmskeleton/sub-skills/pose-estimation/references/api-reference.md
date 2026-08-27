# Pose API and output contract

Return to [SKILL.md](../SKILL.md) for routing and to
[compatibility.md](compatibility.md) before attempting the optional detector
stack. Route emitted JSON to [data-preparation](../../data-preparation/SKILL.md)
and then validated skeleton data to [recognition](../../recognition/SKILL.md).
This reference records the public API exposed by the installed
`mmskeleton.apis` package and its documented pose workflow.

## High-level image API

The intended pattern is:

```python
import mmcv
from mmskeleton.apis import init_pose_estimator, inference_pose_estimator

cfg = mmcv.Config.fromfile("path/to/pose-estimator-config.yaml")
model = init_pose_estimator(**cfg, device=0)
result = inference_pose_estimator(model, image)
```

`init_pose_estimator(detection_cfg, estimation_cfg, device=None)` constructs a
person detector with `mmdet.apis.init_detector`, constructs the HRNet-based
2-D estimator through the package's two-dimensional estimator initializer,
loads both checkpoints, and returns a tuple containing the two models and the
two configuration objects. `device=None` leaves both models on CPU during
initialization; a supplied device causes the implementation to set
`CUDA_VISIBLE_DEVICES` to that value and move both models to CUDA. Treat
`device` as a GPU selection for the documented path, not as a guarantee that
CPU detector inference is supported.

`inference_pose_estimator(pose_estimator, image)` runs detector inference,
keeps person-class boxes whose score is at least `detection_cfg.bbox_thre`,
preprocesses each box to the HRNet input, and returns a dictionary:

- `joint_preds`: predicted keypoint coordinates for each retained person, or
  `None` when no person box passes the threshold;
- `joint_scores`: per-keypoint confidence values, or `None` when no person is
  retained;
- `meta`: affine-transform metadata (`scale`, `rotation`, `center`, `score`),
  or `None` when no person is retained;
- `has_return`: boolean indicating whether any person was retained;
- `person_bbox`: retained detector boxes, including their detector score.

The implementation receives image arrays in the detector's expected frame
format. The pose preprocessing path reverses the final image channel order
before HRNet preprocessing, applies the configured affine crop, scales pixels
to `[0, 1]`, subtracts `image_mean`, divides by `image_std`, and transposes to
`(C, H, W)`. Do not casually mix RGB/BGR conventions; preserve the format used
by the detector and the package path.

The source's inference helper uses CUDA for the flip-augmented HRNet branch.
This is another reason to treat the API as optional and environment-gated,
even if model construction on CPU appears possible.

## Configuration fields

A caller-provided pose-estimator configuration contains two sections:

- `detection_cfg.model_cfg`: Cascade-RCNN detector config;
- `detection_cfg.checkpoint_file`: detector checkpoint path or an
  `mmskeleton://mmdet/...` alias;
- `detection_cfg.bbox_thre`: person-box score threshold;
- `estimation_cfg.model_cfg`: HRNet pose config;
- `estimation_cfg.checkpoint_file`: HRNet checkpoint path or an
  `mmskeleton://pose_estimation/...` alias;
- `estimation_cfg.data_cfg.image_size`: `[192, 256]` in the supplied example,
  represented as width then height by the preprocessing code;
- `estimation_cfg.data_cfg.pixel_std`: `200` in the example;
- `estimation_cfg.data_cfg.image_mean` and `image_std`: three-channel
  normalization constants;
- `estimation_cfg.data_cfg.post_process`: retained in the config for the
  estimator pipeline.

The pose demo config adds `gpus`, `worker_per_gpu`, `video_file`, and `save_dir`.
The dataset builder additionally takes `video_dir`, `out_dir`,
`category_annotation`, and `tracker_cfg`.

## Handoff output

The dataset builder converts each successful frame/person result into a JSON
file. Its `info` object includes `video_name`, `resolution`, `num_frame`,
`num_keypoints`, `keypoint_channels: ["x", "y", "score"]`, and `version:
"1.0"`. Each annotation includes `frame_index`, `id`, `person_id` (normally
`null`), `person_bbox`, and `keypoints`, where each keypoint is `[x, y, score]`.
The top-level `category_id` comes from the optional category annotation file,
or is `-1` when no category is supplied.

The builder uses a per-frame person index as `id`; it does not implement
tracking. A missing detection frame is omitted (`has_return` is false). This
means downstream consumers must handle sparse frame annotations and must not
interpret `id` as a persistent identity. Route every generated JSON file to
`data-preparation` for schema and consistency validation. Only after that
validation should `recognition` select a compatible graph/layout and model.
