# X-Conv architecture and settings

Read this file before editing a model setting or translating a PointCNN graph.
It records the graph algebra and the tuple semantics used by the legacy
classification and segmentation settings.

## Settings schema

The source constructs dictionaries from these tuple names:

```python
xconv_param_name = ('K', 'D', 'P', 'C', 'links')
xdconv_param_name = ('K', 'D', 'pts_layer_idx', 'qrs_layer_idx')
fc_param_name = ('C', 'dropout_rate')
```

Each `xconv_params` item is `(K, D, P, C, links)`:

- `K`: number of retained neighbors per query.
- `D`: dilation stride. The implementation first asks for `K * D` nearest
  points and then takes `indices[:, :, ::D, :]`, leaving `K` neighbors.
- `P`: number of output query/representative points. `-1` means all current
  source points. On layers after the first, a `P` equal to the immediately
  preceding X-Conv `P` reuses the current query points.
- `C`: output channels of the local separable convolution.
- `links`: Python layer indices used for DenseNet-style concatenation. Negative
  indices such as `[-1, -2]` refer to recent `layer_fts` entries. The source
  slices linked features to `P` points before concatenation.

Each `xdconv_params` item is `(K, D, pts_layer_idx, qrs_layer_idx)`:

- `pts_layer_idx` selects the coarse/source X-Conv output used as `pts` and,
  for the first X-DeConv only, as `fts`.
- `qrs_layer_idx` selects the finer query point and skip feature to fuse.
- `P` and `C` are inherited from `xconv_params[qrs_layer_idx]`.
- `C_pts_fts` is `xconv_params[pts_layer_idx]['C'] // 4`; its depth multiplier
  is `1`.
- After an X-DeConv, the output is concatenated with the skip feature and
  projected back to `C` with `pf.dense`.

`fc_params` items are `(C, dropout_rate)`. The final FC tensor is not
necessarily a single vector until the classification head pools it at
inference time.

## X-Conv data flow

For one layer, let `pts` be `[N,M,3]` and `qrs` be `[N,P,3]`.

1. `knn_indices_general(qrs, pts, K*D, True)` produces `[N,P,K*D,2]`.
2. Slicing every `D`-th index produces `[N,P,K,2]`. Optional `sort_points`
   changes neighbor order but not rank.
3. Gathering gives `nn_pts` `[N,P,K,3]`; subtracting the query gives
   `nn_pts_local` `[N,P,K,3]`.
4. Two dense projections of local points make `nn_fts_from_pts` with
   `C_pts_fts` channels. If `fts` exists, gather it with the same indices and
   concatenate it on the final channel axis.
5. With X transformation enabled:
   - `conv2d(..., K*K, kernel=(1,K))` and reshape create `[N,P,K,K]`;
   - two depthwise convolutions over `(1,K)` refine the matrix;
   - matrix multiplication with neighborhood features transforms each
     `[K, channels]` neighborhood.
6. A separable convolution over `(1,K)` outputs `[N,P,1,C]`; squeezing axis 2
   returns `[N,P,C]`.
7. If `with_global` is enabled for the final X-Conv, two dense projections of
   `qrs` contribute `C//4` channels, so the returned channels are
   `C + C//4` at that point. The later head must tolerate this widened tensor.

At layer zero, the source chooses `C_pts_fts = C//2` when no input features
exist and `C//4` otherwise, and uses `depth_multiplier=4`. Later X-Conv layers
use `C_prev//4` point-feature channels and
`ceil(C / C_prev)` as the depth multiplier. X-DeConv uses `C_prev//4` and
`depth_multiplier=1`.

## Query selection and layer indices

`PointCNN` supports four setting values:

- `random`: when downsampling, takes the first `P` points with `tf.slice`.
  This is deterministic for a fixed input order and does not randomize inside
  the layer. `links` are permitted only with this setting in the source.
- `ids`: calls inverse-density sampling, which uses a TensorFlow Python
  callback and NumPy random choice. It needs `K <= M` and enough eligible
  points.
- `fps`: calls `farthest_point_sample(P, pts)` and gathers query coordinates.
  It imports the GPU custom-op wrapper during graph construction.
- any other value: the source exits with an unknown-sampling error.

For FPS, the source creates `[batch_index, sampled_index]` pairs and gathers
`qrs` as `[N,P,3]`. The custom operator requires a positive `npoint`; keep
`P <= M` even though the low-level kernel's shape function only records the
requested output size.

`links` are rejected when `sampling != 'random'`. A link must resolve through
Python list indexing and have enough query rows for the current `P`; otherwise
`tf.slice` or the concatenation raises a shape error. Validate link indices and
channel totals before building a large graph.

## Canonical setting examples

A compact classification-style stack is conceptually:

```text
(8, 1, -1, 16*x, [])
(12, 2, 384, 32*x, [])
(16, 2, 128, 64*x, [])
(16, 3, 128, 128*x, [])
```

A segmentation-style stack commonly uses FPS and a decoder, for example:

```text
xconv:  (8, 1, -1, 32*x, [])
         (12, 2, 768, 32*x, [])
         (16, 2, 384, 64*x, [])
         (16, 6, 128, 128*x, [])
xdconv: (16, 6, 3, 2)
         (12, 6, 2, 1)
         (8,  6, 1, 0)
```

These are shape examples, not benchmark recommendations. Recompute all
`K*D <= M` checks for the actual input and layer point counts. Do not infer
accuracy or runtime from these settings.

## Sorting and geometric augmentation

`sorting_method=None` preserves the top-k order. `l2` sorts by local distance
from the neighborhood mean. A canonical method must start with `c` and have
exactly one `x`, `y`, and `z`, for example `cxyz` or `cyxz`; invalid strings
call `exit()` during graph construction.

The outer data graph usually calls:

```python
xforms, rotations = pf.get_xforms(batch_size, rotation_range,
                                   scaling_range, order=rotation_order)
points_augmented = pf.augment(points, xforms, jitter_range)
```

`get_xforms` returns NumPy matrices, while `augment` is a TensorFlow op. When
normal features are enabled, rotate the first three feature channels with
`rotations` and leave remaining non-normal channels unchanged. The model
expects coordinates in the first three channels and `data_dim - 3` feature
channels thereafter.

## Head contracts

Classification uses the final FC stack and applies a conditional mean over the
point axis for inference. Use `[N, P, num_class]` during training and
`[N, 1, num_class]` for inference when checking logits. Segmentation keeps
`[N,P,num_class]` at both phases. The outer workflows tile classification
labels over the point axis for training and use sampled labels pointwise for
segmentation.

## Safe graph adaptation sequence

1. Start with `with_X_transformation=False`, `sampling='random'`, and a small
   point count only to verify ranks and channel arithmetic.
2. Add input features and verify `data_dim`, `use_extra_features`, and the
   first-layer `C_pts_fts` branch.
3. Turn on sorting or X transformation and inspect the named operations under
   the supplied `tag` values.
4. Add decoder layers with one valid skip pair at a time.
5. Only then switch to `ids` or `fps`. For FPS, run
   `inspect_sampling_build.py` and a bounded GPU operator test separately.

This sequence isolates graph-shape failures from legacy custom-op and driver
failures.
