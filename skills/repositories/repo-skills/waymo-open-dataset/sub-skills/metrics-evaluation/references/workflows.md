# Metrics Workflows

## Inspect breakdown names

```python
from waymo_open_dataset.protos import breakdown_pb2, metrics_pb2
from waymo_open_dataset.metrics.python import config_util_py
config = metrics_pb2.Config()
config.breakdown_generator_ids.append(breakdown_pb2.Breakdown.ONE_SHARD)
config.difficulties.add()
print(config_util_py.get_breakdown_names_from_config(config))
```

Use this before filtering metric names or interpreting output arrays.

## TensorFlow metric wrappers

1. Build the appropriate metric config proto.
2. Create tensors with the exact shapes and dtypes expected by the wrapper.
3. Call the wrapper to get a dictionary of metric name to `(value_op, update_op)`.
4. Initialize local variables, run update ops, then read value ops. In TF2, use `tf.compat.v1` graph/session style when following the original metric-op pattern.

## C++/Bazel tools and fake fixtures

The repository also contains C++ metric executables and fake binary fixtures. Use those paths for maintainer validation or official tool parity, but prefer Python wrappers for in-process model evaluation. Full C++ tool execution requires a Bazel-built binary and is not a lightweight runtime check.

## Keypoint and pose metrics

Keypoint APIs include OKS-like similarity, MPJPE/PCK-style metrics, matching helpers, visibility precision/recall, and the Pose Estimation Metric concepts documented in WOD. Keep 2D camera keypoints and 3D laser keypoints separate and preserve visibility masks.
