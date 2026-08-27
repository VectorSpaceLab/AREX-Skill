# Shared model API reference

This reference distills the shared TensorFlow layer/model API surface used by PointNet2. It is intended to be usable without reopening the source checkout.

## Environment assumptions

- Source code targets TensorFlow 1.x. Verified inspection facts for this production run included a Python 2 inspection environment with TensorFlow 1.15.0 CPU and scientific-stack imports.
- `utils/tf_util.py` uses `tf.contrib.layers.xavier_initializer()` and `tf.contrib.layers.batch_norm(...)`; TF2-only installs fail even when `import tensorflow` succeeds.
- PointNet++ layers in `utils/pointnet_util.py` import custom-op wrappers from `tf_ops/sampling`, `tf_ops/grouping`, and `tf_ops/3d_interpolation`. Those wrappers load `.so` files at import time.
- The CPU baseline `models/pointnet_cls_basic.py` depends on `tf_util.py` but not on PointNet++ custom ops.

## `utils/tf_util.py` layer helpers

All helpers create variables under the supplied TensorFlow variable scope. Most wrappers use CPU-placed variables through `_variable_on_cpu(...)`, add optional L2 weight decay to the `losses` collection, then apply optional batch norm and activation.

### Variable helpers

| Function | Contract |
| --- | --- |
| `_variable_on_cpu(name, shape, initializer, use_fp16=False)` | Creates a `tf.get_variable` on `/cpu:0`; dtype is `float16` when `use_fp16=True`, else `float32`. |
| `_variable_with_weight_decay(name, shape, stddev, wd, use_xavier=True)` | Creates a variable with Xavier init via `tf.contrib.layers.xavier_initializer()` when `use_xavier=True`, otherwise truncated normal. If `wd` is not `None`, adds `tf.nn.l2_loss(var) * wd` to collection `losses`. |

### Convolution / FC wrappers

| Function | Input shape | Important parameters | Output |
| --- | --- | --- | --- |
| `conv1d(inputs, num_output_channels, kernel_size, scope, stride=1, padding='SAME', data_format='NHWC', use_xavier=True, stddev=1e-3, weight_decay=None, activation_fn=tf.nn.relu, bn=False, bn_decay=None, is_training=None)` | `B x L x C` for NHWC-like path; `B x C x L` for NCHW | Uses `tf.nn.conv1d`; batch norm via `batch_norm_for_conv1d` if `bn=True`. | 3-D tensor with `num_output_channels`. |
| `conv2d(inputs, num_output_channels, kernel_size, scope, stride=[1,1], padding='SAME', data_format='NHWC', use_xavier=True, stddev=1e-3, weight_decay=None, activation_fn=tf.nn.relu, bn=False, bn_decay=None, is_training=None)` | `B x H x W x C` (`NHWC`) or `B x C x H x W` (`NCHW`) | `kernel_size=[kh,kw]`; `stride=[sh,sw]`; source constructs `tf.nn.conv2d` strides as `[1, sh, sw, 1]`. | 4-D tensor. |
| `conv2d_transpose(inputs, num_output_channels, kernel_size, scope, stride=[1,1], padding='SAME', use_xavier=True, stddev=1e-3, weight_decay=None, activation_fn=tf.nn.relu, bn=False, bn_decay=None, is_training=None)` | `B x H x W x C` | Computes static output shape from input shape, stride, kernel, and padding. | 4-D tensor with `num_output_channels`. |
| `conv3d(inputs, num_output_channels, kernel_size, scope, stride=[1,1,1], padding='SAME', use_xavier=True, stddev=1e-3, weight_decay=None, activation_fn=tf.nn.relu, bn=False, bn_decay=None, is_training=None)` | `B x D x H x W x C` | Uses `tf.nn.conv3d`. | 5-D tensor. |
| `fully_connected(inputs, num_outputs, scope, use_xavier=True, stddev=1e-3, weight_decay=None, activation_fn=tf.nn.relu, bn=False, bn_decay=None, is_training=None)` | `B x N` | Optional FC batch norm and activation. | `B x num_outputs`. |

### Pooling and normalization wrappers

| Function | Contract |
| --- | --- |
| `max_pool2d(inputs, kernel_size, scope, stride=[2,2], padding='VALID')` | 2-D max pool on `B x H x W x C`. |
| `avg_pool2d(inputs, kernel_size, scope, stride=[2,2], padding='VALID')` | 2-D average pool on `B x H x W x C`. |
| `max_pool3d(inputs, kernel_size, scope, stride=[2,2,2], padding='VALID')` | 3-D max pool on `B x D x H x W x C`. |
| `avg_pool3d(inputs, kernel_size, scope, stride=[2,2,2], padding='VALID')` | 3-D average pool on `B x D x H x W x C`. |
| `batch_norm_template(inputs, is_training, scope, moments_dims_unused, bn_decay, data_format='NHWC')` | Calls `tf.contrib.layers.batch_norm(..., center=True, scale=True, is_training=is_training, decay=bn_decay or 0.9, updates_collections=None, data_format=data_format)`. |
| `batch_norm_for_fc(inputs, is_training, bn_decay, scope)` | Batch norm for `B x C`. |
| `batch_norm_for_conv1d(inputs, is_training, bn_decay, scope, data_format)` | Batch norm for 1-D conv maps. |
| `batch_norm_for_conv2d(inputs, is_training, bn_decay, scope, data_format)` | Batch norm for 2-D conv maps. |
| `batch_norm_for_conv3d(inputs, is_training, bn_decay, scope)` | Batch norm for 3-D conv maps. |
| `dropout(inputs, is_training, scope, keep_prob=0.5, noise_shape=None)` | Uses `tf.cond(is_training, lambda: tf.nn.dropout(inputs, keep_prob, noise_shape), lambda: inputs)`. |

**Gotcha:** when `bn=True`, pass an `is_training` boolean tensor. Omitting it may build an invalid batch norm path.

## PointNet++ set-abstraction and feature-propagation APIs

These APIs live in `utils/pointnet_util.py`. They are the shared layer blocks consumed by the PointNet++ models.

### Low-level grouping helpers

| Function | Inputs | Outputs / notes |
| --- | --- | --- |
| `sample_and_group(npoint, radius, nsample, xyz, points, knn=False, use_xyz=True)` | `xyz: (B, ndataset, 3)`; `points: (B, ndataset, C)` or `None`; samples `npoint` centroids. | Returns `new_xyz: (B,npoint,3)`, `new_points: (B,npoint,nsample,3+C or C)`, `idx: (B,npoint,nsample)`, `grouped_xyz: (B,npoint,nsample,3)` normalized by subtracting centroid. Uses `farthest_point_sample`, `gather_point`, `query_ball_point` or `knn_point`, and `group_point`. |
| `sample_and_group_all(xyz, points, use_xyz=True)` | `xyz: (B, ndataset, 3)`, optional `points`. | Returns one all-cloud region: `new_xyz: (B,1,3)` at zero, `new_points: (B,1,ndataset,3+C or C)`, `idx`, `grouped_xyz`. |

### Set abstraction modules

```python
pointnet_sa_module(
    xyz, points, npoint, radius, nsample, mlp, mlp2, group_all,
    is_training, bn_decay, scope, bn=True, pooling='max',
    knn=False, use_xyz=True, use_nchw=False)
```

- `xyz`: `(B, ndataset, 3)`.
- `points`: `(B, ndataset, C)` or `None`.
- `mlp`: list of output channels for pointwise MLP applied to grouped local points.
- `mlp2`: optional list of output channels for post-pooling processing.
- `group_all=True` overrides `npoint`, `radius`, and `nsample` and groups the whole cloud.
- `pooling` supports `max`, `avg`, `weighted_avg`, and `max_and_avg`.
- Returns `(new_xyz, new_points, idx)` where `new_points` is `(B, npoint, mlp[-1] or mlp2[-1])` after squeeze.
- `use_nchw=True` transposes grouped points to NCHW before conv2d; source notes higher GPU memory usage for some later layers.

```python
pointnet_sa_module_msg(
    xyz, points, npoint, radius_list, nsample_list, mlp_list,
    is_training, bn_decay, scope, bn=True, use_xyz=True, use_nchw=False)
```

- Multi-scale grouping variant.
- `radius_list`, `nsample_list`, and `mlp_list` have matching lengths.
- For each scale, groups local regions, applies the scale-specific MLP, max-pools, then concatenates scale outputs.
- Returns `(new_xyz, new_points_concat)` with `new_points_concat` shape `(B, npoint, sum(mlp_list[k][-1]))`.

### Feature propagation module

```python
pointnet_fp_module(xyz1, xyz2, points1, points2, mlp, is_training, bn_decay, scope, bn=True)
```

- `xyz1`: dense target points `(B, ndataset1, 3)`.
- `xyz2`: sparse source points `(B, ndataset2, 3)`.
- `points1`: existing dense features `(B, ndataset1, C1)` or `None`.
- `points2`: sparse features `(B, ndataset2, C2)`.
- Uses `three_nn` and inverse-distance weights for 3-NN interpolation, concatenates `points1` if available, then applies `tf_util.conv2d` layers from `mlp`.
- Returns `new_points: (B, ndataset1, mlp[-1])`.

## Custom-op wrapper APIs

The wrapper modules import `.so` files at module import time. See `custom-ops.md` before importing them.

### `tf_ops/sampling/tf_sampling.py`

| Function | Input | Output |
| --- | --- | --- |
| `prob_sample(inp, inpr)` | `inp: (B, ncategory) float32`; `inpr: (B, npoints) float32` | `(B, npoints) int32`; no gradient. |
| `gather_point(inp, idx)` | `inp: (B, ndataset, 3) float32`; `idx: (B, npoints) int32` | `(B, npoints, 3) float32`; gradient registered as `GatherPoint`. |
| `farthest_point_sample(npoint, inp)` | `npoint: int`; `inp: (B, ndataset, 3) float32` | `(B, npoint) int32`; no gradient. |

### `tf_ops/grouping/tf_grouping.py`

| Function | Input | Output |
| --- | --- | --- |
| `query_ball_point(radius, nsample, xyz1, xyz2)` | `xyz1: (B, ndataset, 3)` input points; `xyz2: (B, npoint, 3)` query points | `idx: (B,npoint,nsample) int32`, `pts_cnt: (B,npoint) int32`; no gradient. |
| `select_top_k(k, dist)` | `dist: (B, M, N) float32` | indices/distances with first `k` entries as smallest. |
| `group_point(points, idx)` | `points: (B, ndataset, C)`; `idx: (B,npoint,nsample)` | `(B,npoint,nsample,C)`; gradient registered as `GroupPoint`. |
| `knn_point(k, xyz1, xyz2)` | TensorFlow fallback that tiles inputs and calls `select_top_k`. | `(val, idx)` each `(B,npoint,k)`; source prints debug tensors during graph construction. |

### `tf_ops/3d_interpolation/tf_interpolate.py`

| Function | Input | Output |
| --- | --- | --- |
| `three_nn(xyz1, xyz2)` | unknown points `xyz1: (B,N,3)`, known points `xyz2: (B,M,3)` | `dist: (B,N,3)`, `idx: (B,N,3)`; no gradient. |
| `three_interpolate(points, idx, weight)` | known features `points: (B,M,C)`, `idx: (B,N,3)`, `weight: (B,N,3)` | interpolated features `(B,N,C)`; gradient registered as `ThreeInterpolate`. |

## Baseline model: `models/pointnet_cls_basic.py`

### Public API

| Function | Contract |
| --- | --- |
| `placeholder_inputs(batch_size, num_point)` | Returns `pointclouds_pl: tf.float32 (batch_size, num_point, 3)` and `labels_pl: tf.int32 (batch_size)`. |
| `get_model(point_cloud, is_training, bn_decay=None)` | Input `point_cloud: (B,N,3)`. Builds PointNet v1-style classification with 1x3/1x1 conv2d layers, global max pool, FC layers, dropout, and final logits. Returns `(net, end_points)` where `net: (B,40)` and `end_points` is empty in this baseline. |
| `get_loss(pred, label, end_points)` | Sparse softmax CE over `pred: (B,40)` and `label: (B)`, adds scalar `classify loss` summary, adds loss to collection `losses`, returns mean classify loss. |

### Verified graph smoke

This production run had an installed-package fact that the baseline graph built with shape `[2, 40]` in the TF1.15 CPU inspection environment. Re-run with:

```bash
python scripts/smoke_pointnet_baseline.py --repo-root /path/to/pointnet2 --batch-size 2 --num-point 16
```

## PointNet++ model consumers

| Model | Input | Shared APIs consumed | Output / loss |
| --- | --- | --- | --- |
| `models/pointnet2_cls_ssg.py` | `(B,N,3)` | `pointnet_sa_module` with layers `(512,0.2,32)->(128,0.4,64)->group_all`; `tf_util.fully_connected/dropout`. | logits `(B,40)`; sparse softmax CE. |
| `models/pointnet2_cls_msg.py` | `(B,N,3)` | `pointnet_sa_module_msg` at radii `[0.1,0.2,0.4]` then `[0.2,0.4,0.8]`; group-all SA. | logits `(B,40)`; sparse softmax CE. |
| `models/pointnet2_part_seg.py` | `(B,N,6)` with XYZ + normals | SA layers, FP layers, `tf_util.conv1d`. | per-point logits `(B,N,50)`; sparse softmax CE. |
| `models/pointnet2_part_seg_msg_one_hot.py` | `(B,N,6)` plus class label | MSG SA and FP with class-conditioning path. | per-point logits for ShapeNetPart. |
| `models/pointnet2_sem_seg.py` | `(B,N,3)` | Four SA layers and four FP layers. | per-point logits `(B,N,num_class)`; weighted sparse softmax CE. |

Use these model-consumer rows to explain dependencies and shapes, but route workflow-specific training/data questions to the appropriate workflow sub-skill.
