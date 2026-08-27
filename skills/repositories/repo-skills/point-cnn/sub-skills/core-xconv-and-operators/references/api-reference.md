# PointCNN core API reference

Read this file when changing a graph, adapting a setting module, or diagnosing
an operator shape error. The signatures below are distilled from the legacy
`pointcnn`, `pointfly`, model-head, and sampling modules in the supported
PointCNN implementation contract. They describe TensorFlow 1.x graph-mode
behavior without requiring a source-document link at runtime.

## Tensor conventions

- `N` is the batch size.
- A point tensor is `[N, M, 3]`, where `M` is the number of points.
- A feature tensor is `[N, M, F]`. `None` means that no input features are
  supplied.
- An X-Conv query tensor is `[N, P, 3]`; its output is `[N, P, C]` unless the
  optional final global feature is concatenated.
- Gather indices for `tf.gather_nd` are integer tensors `[N, P, 2]` whose last
  coordinate is `[batch_index, point_index]`.
- The graph uses static or partially known ranks but dynamic batch dimensions.
  Preserve the final coordinate/channel dimensions when creating placeholders.

## `pointcnn.xconv`

```python
xconv(pts, fts, qrs, tag, N, K, D, P, C, C_pts_fts,
      is_training, with_X_transformation, depth_multiplier,
      sorting_method=None, with_global=False)
```

Inputs:

- `pts`: source points `[N, M, 3]`.
- `fts`: source features `[N, M, F]` or `None`.
- `qrs`: representative/query points `[N, P, 3]`.
- `tag`: unique string prefix used for graph operation and variable names.
- `N`: batch-size tensor, normally `tf.shape(points)[0]`.
- `K`, `D`, `P`, `C`, `C_pts_fts`: integer graph settings. The source
  neighborhood request is `K * D`; the returned dilation slice has `K`
  neighbors.
- `is_training`: boolean scalar used by batch normalization.
- `with_X_transformation`: whether the learned `[K, K]` X matrix is applied.
- `depth_multiplier`: depthwise/separable convolution multiplier.
- `sorting_method`: `None`, `l2`, or a string beginning with `c` followed by a
  permutation of `xyz`, such as `cyxz`.
- `with_global`: when true, two dense projections of `qrs` add `C // 4`
  channels to the final local feature. The source uses this only on the final
  X-Conv layer.

Output: `[N, P, C]` normally, or `[N, P, C + C // 4]` with global features.
The implementation first calls `pointfly.knn_indices_general(qrs, pts, K * D,
True)`, keeps every `D`-th neighbor, gathers and centers points, optionally
learns an X transform, and applies a separable convolution over the neighbor
axis.

## `pointcnn.PointCNN`

```python
PointCNN(points, features, is_training, setting)
```

The constructor builds the entire graph and exposes:

- `layer_pts`: input/query point tensors, including the initial points and any
  X-DeConv query tensors.
- `layer_fts`: corresponding feature tensors. `layer_fts[0]` is `None` when
  input features are absent; otherwise features are reshaped to
  `[N, M, data_dim - 3]` and projected to half of the first X-Conv channel
  count.
- `fc_layers`: final pointwise dense/dropout stack.
- `fc_layers[-1]`: pooled later by the classification head only at inference;
  retained pointwise by segmentation.

`setting` must expose at least `xconv_params`, `fc_params`,
`with_X_transformation`, `sorting_method`, and `sampling`. Segmentation
settings additionally expose `xdconv_params`. If `sampling` is `fps`, graph
construction imports the sampling wrapper and therefore expects a sibling
`tf_sampling_so.so` shared library before the graph can be built.

## Model heads

```python
pointcnn_cls.Net(points, features, is_training, setting)
pointcnn_seg.Net(points, features, is_training, setting)
```

Both subclass `PointCNN` and create `self.logits` with a final dense projection
using `setting.num_class`, without batch normalization or an ELU activation.

- Classification uses `tf.cond(is_training, identity, reduce_mean over axis 1)`
  on the final FC tensor. Training logits are therefore shaped like
  `[N, P, num_class]`; inference logits are `[N, 1, num_class]`.
- Segmentation does not pool and returns `[N, P, num_class]`.
- `tf.nn.softmax` and `tf.argmax` are consumers in the outer workflows, not
  part of either `Net` constructor.

## `pointfly` geometry and sampling APIs

| API | Signature | Contract |
|---|---|---|
| `get_indices` | `(batch_size, sample_num, point_num, pool_setting=None)` | NumPy `[batch_size, sample_num, 2]` indices for `tf.gather_nd`; samples without replacement when possible and repeats when a pool is smaller than `sample_num`. `point_num` may be a scalar or per-example NumPy array. |
| `get_xforms` | `(xform_num, rotation_range=(0,0,0,'u'), scaling_range=(0.,0.,0.,'u'), order='rxyz')` | NumPy `(xforms, rotations)`, each `[xform_num, 3, 3]`; scalar ranges use clipped Gaussian (`'g'`) or uniform (`'u'`), iterable ranges choose one item. |
| `augment` | `(points, xforms, range=None)` | Graph output from `tf.matmul(points, xforms)`; with `range`, adds clipped normal jitter in `[-5*range, 5*range]`. |
| `distance_matrix` | `(A)` | For rank-2 `[M,C]`, returns `[M,M]`. |
| `batch_distance_matrix` | `(A)` | For `[N,M,C]`, returns `[N,M,M]`. |
| `batch_distance_matrix_general` | `(A, B)` | For `[N,PA,C]` and `[N,PB,C]`, returns `[N,PA,PB]`. |
| `knn_indices` | `(points, k, sort=True, unique=True)` | Returns distances `[N,M,k]` and indices `[N,M,k,2]`; `k <= M` is required. |
| `knn_indices_general` | `(queries, points, k, sort=True, unique=True)` | Returns distances `[N,P,k]` and indices `[N,P,k,2]`; `k <= M` for the source `points`. |
| `sort_points` | `(points, indices, sorting_method)` | Reorders `[N,P,K,2]` neighbor indices by `l2` or canonical coordinate order (`cxyz`, `cyxz`, etc.). |
| `inverse_density_sampling` | `(points, k, sample_num)` | Builds `[N,sample_num,2]` indices using `tf.py_func`; `k <= M`, and the NumPy choice path needs enough eligible points. |
| `curvature_based_sample` | `(nn_pts, k)` | For `[N,P,K,3]`, returns `[N,P,2]` indices selected by local curvature. |
| `compute_curvature` | `(nn_pts)` | For `[N,P,K,3]`, returns `[N,P]` curvature estimates from covariance eigenvalues. |
| `conv2d` | `(input, output, name, is_training, kernel_size, reuse=None, with_bn=True, activation=tf.nn.elu)` | `tf.layers.conv2d`, `VALID` padding, then legacy batch normalization by default. |
| `separable_conv2d` | `(input, output, name, is_training, kernel_size, depth_multiplier=1, reuse=None, with_bn=True, activation=tf.nn.elu)` | `tf.layers.separable_conv2d`, `VALID` padding, then batch normalization by default. |
| `depthwise_conv2d` | `(input, depth_multiplier, name, is_training, kernel_size, reuse=None, with_bn=True, activation=tf.nn.elu)` | `tf.contrib.layers.separable_conv2d` with no pointwise output (`num_outputs=None`), then batch normalization by default. |
| `dense` | `(input, output, name, is_training, reuse=None, with_bn=True, activation=tf.nn.elu)` | `tf.layers.dense`, then batch normalization by default. |

`batch_normalization` uses `tf.layers.batch_normalization` with momentum `0.99`
and legacy L2 regularizers from `tf.contrib.layers`. Do not replace these
calls with TensorFlow 2 Keras APIs without treating the change as a port.

## `sampling.tf_sampling` custom operators

The wrapper loads `tf_sampling_so.so` at import time and exposes:

```python
prob_sample(inp, inpr)
gather_point(inp, idx)
farthest_point_sample(npoint, inp)
```

Contracts from the C++ shape functions and Python wrapper:

| Operator | Inputs | Output | Backend |
|---|---|---|---|
| `prob_sample` | `inp` float32 `[B,num_choices]`, `inpr` float32 `[B,num_points]` | int32 `[B,num_points]` | GPU only |
| `gather_point` | float32 `[B,num_dataset,3]`, int32 `[B,num_result]` | float32 `[B,num_result,3]` | GPU only |
| `farthest_point_sample` | `npoint` positive integer and float32 `[B,num_dataset,3]` | int32 `[B,npoint]` | GPU only |
| `gather_point_grad` | source float32 `[B,num_dataset,3]`, indices `[B,num_result]`, gradient `[B,num_result,3]` | source gradient `[B,num_dataset,3]` | GPU only |

The wrapper registers no gradient for probability or FPS sampling and a custom
gradient for `GatherPoint`. The implementation registers kernels only with
`DEVICE_GPU`; there is no CPU fallback. Loading a shared object is not the
same as executing a kernel successfully.

## Minimal shape checks

Before a full model build, assert the following with a graph-mode test or a
settings linter:

```text
points: [N, M, 3]
features: [N, M, data_dim - 3] or None
qrs: [N, P, 3]
K * D <= M for every xconv/xdconv source tensor
P <= M for random/ids/fps query selection, except P == -1
C > 0 and every referenced link points to an existing layer
num_class > 0
```

If a `P` value is `-1`, the layer uses all current source points. If a later
`P` equals the previous X-Conv `P`, the current query tensor is reused.
