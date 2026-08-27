# Dataset Utility Workflows

## Parse a TFRecord frame

```python
import tensorflow as tf
from waymo_open_dataset import dataset_pb2
from waymo_open_dataset.utils import frame_utils

dataset = tf.data.TFRecordDataset(['segment.tfrecord'])
frame = dataset_pb2.Frame()
frame.ParseFromString(next(iter(dataset)).numpy())
range_images, camera_projections, seg_labels, range_image_top_pose = frame_utils.parse_range_image_and_camera_projection(frame)
points, cp_points = frame_utils.convert_range_image_to_point_cloud(frame, range_images, camera_projections, range_image_top_pose)
```

Use `ri_index=1` for second returns. Use `keep_polar_features=True` if later code expects range/intensity/elongation along with xyz.

## Convert a frame to numpy fields

```python
from waymo_open_dataset.utils import frame_utils
arrays = frame_utils.convert_frame_to_dict(frame)
print(sorted(arrays))
```

This is the same field vocabulary used by the latency challenge; use `latency-submissions` for validating a submitted model module.

## Map and geometry use

For map visualization or lane/neighborhood reasoning, combine `dataset_pb2` map features with `utils.plot_maps` and geometry helpers. Keep coordinate frames explicit: vehicle frame, global frame, camera frame, and box-local frame are not interchangeable.
