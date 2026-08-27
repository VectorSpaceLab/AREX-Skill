# Latency Data Formats

Input directories contain `.npy` arrays keyed by field name. Common fields include `POSE`, `TIMESTAMP`, lidar range images/projections/extrinsics/beam inclinations, top-lidar pose, camera RGB images, camera intrinsics/extrinsics, image width/height, camera pose and timing fields, and rolling-shutter metadata.

For previous frames, append `_1` or `_2` to a field name, for example `TOP_RANGE_IMAGE_FIRST_RETURN_1`.

Output result directories contain:

```text
<context_name>/<timestamp_micros>/
  boxes.npy
  scores.npy
  classes.npy
  input_fields.txt   # written by evaluator; required for 2D conversion checks
```

For 2D results, `input_fields.txt` must identify exactly one camera image field ending in `_IMAGE` so the converter can set the object camera name.
