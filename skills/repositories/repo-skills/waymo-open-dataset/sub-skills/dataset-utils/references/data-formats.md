# Dataset Utility Data Formats

## Frame proto

A v1 `Frame` stores context, pose, laser calibrations, camera calibrations, lidar range images, camera projections, labels, and optional segmentation/keypoint fields. Compressed range images and projections are decoded from zlib-compressed proto payloads before becoming tensors.

## Lidar arrays

`convert_frame_to_dict` and latency utilities use field names such as:

- `POSE`: `4x4` float32 vehicle pose.
- `TIMESTAMP`: int64 scalar timestamp in microseconds.
- `<LIDAR_NAME>_RANGE_IMAGE_FIRST_RETURN` and `_SECOND_RETURN`: `H x W x 6` float32 arrays containing range, intensity, elongation, x, y, z.
- `<LIDAR_NAME>_CAM_PROJ_FIRST_RETURN` and `_SECOND_RETURN`: camera projection arrays.
- `<LIDAR_NAME>_BEAM_INCLINATION` and `<LIDAR_NAME>_LIDAR_EXTRINSIC`.
- `TOP_RANGE_IMAGE_POSE` for the top lidar.

## Camera arrays

Common camera keys include `<CAMERA_NAME>_IMAGE`, `<CAMERA_NAME>_INTRINSIC`, `<CAMERA_NAME>_EXTRINSIC`, `<CAMERA_NAME>_WIDTH`, `<CAMERA_NAME>_HEIGHT`, camera pose/timing fields, and rolling-shutter metadata.

## Keypoints and boxes

Keypoint metric utilities use WOD keypoint protos and helper tensor containers such as `KeypointsTensors` and `BoundingBoxTensors`. Box tensors usually encode center, size, heading, and optional batch dimensions. Read the metric or keypoint helper reference before mixing 2D and 3D boxes.
