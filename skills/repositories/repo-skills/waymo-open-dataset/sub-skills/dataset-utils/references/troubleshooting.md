# Dataset Utils Troubleshooting

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Decompression or parse error | The field is absent, not a WOD Frame, or compressed payload is empty | Check `HasField`/payload length before decoding and confirm the TFRecord contains serialized `Frame` protos. |
| Empty point cloud | Range image values are zero or wrong return index was selected | Inspect first/second returns and the valid range mask before blaming calibration. |
| TOP lidar points are misaligned | `range_image_top_pose` or frame pose was dropped | Use `parse_range_image_and_camera_projection` output and pass it into conversion. |
| Camera projections do not match points | Lidar calibration order or return index mismatch | Sort by calibration as the helper does and keep `ri_index` consistent for range images and projections. |
| TensorFlow `.numpy()` fails | Running graph mode or non-eager tensors | Use eager execution for utility workflows or evaluate tensors in the correct session/graph context. |
| Box/keypoint shapes fail | Mixing batched/unbatched or 2D/3D tensors | Check helper docstrings and construct matching `BoundingBoxTensors`/keypoint tensor shapes. |
