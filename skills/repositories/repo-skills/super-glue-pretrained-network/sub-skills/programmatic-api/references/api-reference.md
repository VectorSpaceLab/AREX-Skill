# API reference

This reference distills the Python-facing contract for the matching models and utility helpers. The bundled inspection helper prints the live signatures and defaults from the importable package.

## Model objects

### `Matching(config={})`

`Matching` composes `SuperPoint(config.get("superpoint", {}))` and `SuperGlue(config.get("superglue", {}))`.

Call `forward(data)` with at least:

- `image0`: grayscale float tensor shaped `1x1xH0xW0`
- `image1`: grayscale float tensor shaped `1x1xH1xW1`

If `keypoints0` / `keypoints1` are absent, `Matching` runs `SuperPoint` internally. If you supply local features yourself, also provide `scores0`, `scores1`, `descriptors0`, and `descriptors1`.

`Matching` stacks list or tuple values with `torch.stack`, so the safest usage is one pair at a time. If you batch more than one pair, make sure the local-feature tensors already have equal lengths across the batch.

Returned keys:

- `keypoints0`, `keypoints1`
- `scores0`, `scores1`
- `descriptors0`, `descriptors1`
- `matches0`, `matches1`
- `matching_scores0`, `matching_scores1`

For a single pair, the common extraction pattern is:

```python
matches0 = pred["matches0"][0]
valid = matches0 > -1
mkpts0 = pred["keypoints0"][0][valid]
mkpts1 = pred["keypoints1"][0][matches0[valid]]
conf = pred["matching_scores0"][0][valid]
```

### `SuperPoint(config)`

`SuperPoint.default_config`:

- `descriptor_dim: 256`
- `nms_radius: 4`
- `keypoint_threshold: 0.005`
- `max_keypoints: -1`
- `remove_borders: 4`

Notes:

- `max_keypoints = -1` keeps all points.
- `0` or any value below `-1` raises `ValueError`.
- The bundled checkpoint expects the default descriptor dimension.

`forward({"image": image})` expects a grayscale float tensor shaped `1x1xHxW` in `[0, 1]`.

It returns per-image sequences:

- `keypoints`: `N x 2` tensors in `(x, y)` image coordinates
- `scores`: detector confidence values for each keypoint
- `descriptors`: `256 x N` descriptors sampled at keypoint locations

### `SuperGlue(config)`

`SuperGlue.default_config`:

- `descriptor_dim: 256`
- `weights: "indoor"`
- `keypoint_encoder: [32, 64, 128, 256]`
- `GNN_layers: ["self", "cross"] * 9`
- `sinkhorn_iterations: 100`
- `match_threshold: 0.2`

Notes:

- `weights` must be either `"indoor"` or `"outdoor"`.
- `matches0` / `matches1` use `-1` for unmatched keypoints.
- `matching_scores0` / `matching_scores1` are zero for unmatched points.
- More Sinkhorn iterations cost more runtime but can stabilize the transport solve.

`forward(data)` expects batched tensors:

- `keypoints0`, `keypoints1`
- `scores0`, `scores1`
- `descriptors0`, `descriptors1`
- `image0`, `image1` for keypoint normalization

If either side has zero keypoints, the module returns `-1` matches and zero scores without running attention.

## Utility functions

### Image loading and preprocessing

- `process_resize(w, h, resize)` -> resized width and height, with warnings for very small or very large outputs.
- `frame2tensor(frame, device)` -> grayscale float frame to a `1x1xHxW` tensor in `[0, 1]`.
- `read_image(path, device, resize, rotation, resize_float)` -> `(image, tensor, scales)`.

### Geometry

- `estimate_pose(kpts0, kpts1, K0, K1, thresh, conf=0.99999)` -> `(R, t, inliers)` or `None` if too few matches survive.
- `compute_epipolar_error(kpts0, kpts1, T_0to1, K0, K1)` -> per-match epipolar error.
- `compute_pose_error(T_0to1, R, t)` -> translation and rotation error in degrees.
- `pose_auc(errors, thresholds)` -> AUC values for thresholds such as `[5, 10, 20]`.

### Supporting math

- `rotate_intrinsics(K, image_shape, rot)`
- `rotate_pose_inplane(i_T_w, rot)`
- `scale_intrinsics(K, scales)`
- `to_homogeneous(points)`

### Plotting

- `plot_image_pair`
- `plot_keypoints`
- `plot_matches`
- `make_matching_plot`
- `make_matching_plot_fast`
- `error_colormap`

### Internal model helpers

- SuperPoint: `simple_nms`, `remove_borders`, `top_k_keypoints`, `sample_descriptors`
- SuperGlue: `normalize_keypoints`, `log_sinkhorn_iterations`, `log_optimal_transport`, `arange_like`
