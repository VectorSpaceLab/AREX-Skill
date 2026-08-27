# Data and results

## Image tensor contract

- `load_image(path)` returns a `torch.float32` tensor in RGB order.
- The shape is `(3, H, W)`.
- Values are normalized to `[0, 1]`.
- Move the tensor to the same device as the extractor and matcher with `.to(device)`.

If you bypass `load_image`, keep the same contract: RGB, channel-first, floating point, and normalized.

## Feature dictionary contract

The extractor `.extract(...)` path returns a single-image feature dict with a batch dimension of 1. After `rbd(...)`, the dict is batch-free.

| field | shape before `rbd` | shape after `rbd` | meaning |
| --- | --- | --- | --- |
| `keypoints` | `(1, N, 2)` | `(N, 2)` | pixel coordinates in `(x, y)` order |
| `descriptors` | `(1, N, D)` | `(N, D)` | local descriptors |
| `keypoint_scores` | `(1, N)` | `(N,)` | detector confidence |
| `image_size` | `(1, 2)` | `(2,)` | original image size when present |

Feature-specific notes:

- `SuperPoint`, `DISK`, and `ALIKED` provide `keypoints`, `descriptors`, and `keypoint_scores`.
- `SIFT` and `DoGHardNet` also carry `scales` and `oris`, which are used by their LightGlue heads.
- `match_pair(...)` already returns batch-stripped dicts, so you only need `rbd(...)` when you use the explicit `extract -> match` flow.

## Matcher result contract

`LightGlue` consumes a dict with `image0` and `image1` keys, each mapped to one feature dict.

The output dict includes:

| field | shape before `rbd` | shape after `rbd` | meaning |
| --- | --- | --- | --- |
| `matches0` | `(1, M)` | `(M,)` | match index for each keypoint in image 0, or `-1` |
| `matches1` | `(1, N)` | `(N,)` | match index for each keypoint in image 1, or `-1` |
| `matching_scores0` | `(1, M)` | `(M,)` | per-keypoint confidence for image 0 |
| `matching_scores1` | `(1, N)` | `(N,)` | per-keypoint confidence for image 1 |
| `matches` | list with one `(K, 2)` tensor | `(K, 2)` tensor | mutual matches as index pairs |
| `scores` | list with one `(K,)` tensor | `(K,)` tensor | per-match confidence values |
| `stop` | scalar | scalar | number of layers executed |
| `prune0` | `(1, M)` | `(M,)` | pruning layer index for each image-0 keypoint |
| `prune1` | `(1, N)` | `(N,)` | pruning layer index for each image-1 keypoint |

## Batch stripping with `rbd`

`rbd(...)` removes the leading batch dimension from tensors, NumPy arrays, and lists. Other values pass through unchanged.

That means the single-pair case becomes easy to index directly:

```python
feats0, feats1, matches01 = [rbd(x) for x in (feats0, feats1, matches01)]
matches = matches01["matches"]
```

## Coordinate extraction

Once `matches` is a `(K, 2)` tensor, recover point coordinates like this:

```python
points0 = feats0["keypoints"][matches[:, 0]]
points1 = feats1["keypoints"][matches[:, 1]]
```

These coordinates are already in the original image frame because the extractor remaps keypoints after any internal resize step.

## Visualization-ready outputs

The script and notebook recipes typically use:

- `points0`, `points1` for `viz2d.plot_matches(...)`,
- `matches01["stop"]` for a summary label,
- and `matches01["prune0"]` / `matches01["prune1"]` if you want the pruning-colored overlay.
