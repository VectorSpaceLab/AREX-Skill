# Dataset Utils API Reference

Verified key signatures:

- `frame_utils.parse_range_image_and_camera_projection(frame)` returns `(range_images, camera_projections, seg_labels, range_image_top_pose)`.
- `frame_utils.convert_range_image_to_cartesian(frame, range_images, range_image_top_pose, ri_index=0, keep_polar_features=False)` returns a dictionary of per-lidar cartesian range images.
- `frame_utils.convert_range_image_to_point_cloud(frame, range_images, camera_projections, range_image_top_pose, ri_index=0, keep_polar_features=False)` returns `points` and `cp_points` lists ordered by sorted laser calibrations.
- `frame_utils.convert_frame_to_dict(frame)` returns latency-style numpy arrays keyed by sensor/data field name.
- `range_image_utils.extract_point_cloud_from_range_image(range_image, extrinsic, inclination, pixel_pose=None, frame_pose=None, dtype=tf.float32, scope=None)` converts polar range-image values.
- `box_utils.is_within_box_3d(point, box, name=None)` and related box utilities operate on TensorFlow tensors.

## Recommended call order for point clouds

1. Parse a serialized `dataset_pb2.Frame`.
2. Call `parse_range_image_and_camera_projection(frame)`.
3. Call `convert_range_image_to_point_cloud(...)` for first return (`ri_index=0`) or second return (`ri_index=1`).
4. If downstream code needs intensity/elongation, pass `keep_polar_features=True` and account for six point features instead of three.

The TOP lidar uses `range_image_top_pose` and frame pose for per-pixel pose correction; do not discard it when converting top-lidar points.
