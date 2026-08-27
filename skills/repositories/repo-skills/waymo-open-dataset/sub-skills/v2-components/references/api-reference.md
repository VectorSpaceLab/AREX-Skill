# V2 API Reference

## Verified imports

```python
from waymo_open_dataset import v2
from waymo_open_dataset.v2 import component
```

Important verified signatures:

- `component.create_column(arrow_type=None, is_repeated=False, **kwargs)` creates dataclass fields with WOD metadata. Leaf fields should set `arrow_type`; nested dataclass fields normally leave it `None`.
- `component.Component.from_dict(columns: dict[str, Any]) -> Component` reconstructs a component instance from a flat dictionary.
- `Component.to_flatten_dict() -> dict[str, Any]` emits flat component columns.
- `Component.schema() -> pyarrow.Schema` emits an Arrow schema for the component class.
- `v2.merge(left, right, left_nullable=False, right_nullable=False, left_group=False, right_group=False, key_prefix='key.')` joins Pandas or Dask tables on common key columns.

## Component tags

The V2 API exports component classes and tags through `v2.TAG_BY_COMPONENT`, `v2.ALL_COMPONENTS`, and `v2.ALL_TAGS`. Verified tags include:

`camera_box`, `camera_calibration`, `camera_hkp`, `camera_image`, `camera_segmentation`, `camera_to_lidar_box_association`, `lidar_box`, `lidar_calibration`, `lidar_camera_projection`, `lidar_camera_synced_box`, `lidar`, `lidar_hkp`, `lidar_pose`, `lidar_segmentation`, `projected_lidar_box`, `stats`, `vehicle_pose`, `object_asset_auto_label`, `object_asset_camera_sensor`, `object_asset_lidar_sensor`, `object_asset_refined_pose`, `object_asset_ray`, `object_asset_ray_compressed`.

## Column naming rules

- Key columns use the `key.` prefix, such as `key.segment_context_name` or `key.frame_timestamp_micros`.
- Component payload columns include a component prefix like `[CameraImageComponent].image`.
- Repeated nested fields include `[*]`, for example `[MyComponent].bar[*].foo.value`.
- Do not strip prefixes before merging; `v2.merge` discovers common keys by prefix.

## Object asset notes

Object asset components model auto labels, camera/lidar sensor payloads, refined poses, and compressed rays. Use the object-asset codec utilities for compressed ray payloads instead of treating them as plain numeric arrays. If a task is about image/camera challenge semantics rather than V2 object-asset component storage, route to `camera-and-segmentation`.
