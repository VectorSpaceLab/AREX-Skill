# Semantic Segmentation Label Issues

Use this route for image datasets where each pixel has a class label in a segmentation mask.

## Inputs

Cleanlab requires integer masks and per-pixel class probabilities:

```python
labels = np.array([
    [[0, 0, 1],
     [0, 1, 1]],
])
# shape: (N, H, W)

pred_probs = np.zeros((1, 2, 2, 3), dtype=float)
pred_probs[:, 0, :, :] = 0.9  # probability of class 0 at each pixel
pred_probs[:, 1, :, :] = 0.1  # probability of class 1 at each pixel
# shape: (N, K, H, W)
```

Required invariants:

- `labels.shape == (N, H, W)`.
- `pred_probs.shape == (N, K, H, W)`.
- `labels` and `pred_probs` must match on `N`, `H`, and `W`.
- Class ids in `labels` are integers `0, 1, ..., K-1`.
- The `K` dimension of `pred_probs` must use the same class order as the integer labels and optional `class_names`.
- If labels are one-hot encoded as `(N, K, H, W)`, convert with `labels = np.argmax(labels_one_hot, axis=1)` before calling cleanlab.
- Prefer out-of-sample pixel probabilities, e.g. from cross-validation or a held-out model.

Large arrays can be memory-mapped (`np.load(..., mmap_mode=...)`) as long as they preserve these shapes and dtypes.

## Find pixel-level issues

```python
from cleanlab.segmentation.filter import find_label_issues

issues = find_label_issues(
    labels,
    pred_probs,
    downsample=1,
    batch_size=10000,
    n_jobs=1,
    verbose=False,
)
# issues.shape == (N, H, W), dtype bool
```

Interpretation:

- `issues[i, r, c] == True` means pixel `(r, c)` in image `i` is suspected to be mislabeled.
- The returned mask is pixel-level; summarize by image with `issues.sum(axis=(1, 2))` or by class with summary helpers.
- `batch_size` controls streaming batches for memory/runtime; larger values are faster when memory allows.
- `n_jobs` controls multiprocessing on supported platforms. If a multiprocessing run fails with a scoped variable/import error, retry with `n_jobs=1`.
- `downsample` can accelerate issue finding by shrinking masks/probabilities first. It must evenly divide both `H` and `W`; use `downsample=1` for maximum accuracy.

## Rank images and pixels

```python
from cleanlab.segmentation.rank import get_label_quality_scores, issues_from_scores

image_scores, pixel_scores = get_label_quality_scores(
    labels,
    pred_probs,
    method="softmin",
    verbose=False,
)

score_issues = issues_from_scores(image_scores, pixel_scores, threshold=0.5)
image_review_order = issues_from_scores(image_scores, threshold=0.5)
```

Interpretation:

- `image_scores` has shape `(N,)`; lower means the image mask is more likely to contain label issues.
- `pixel_scores` has shape `(N, H, W)`; lower means the pixel label is less likely correct.
- `issues_from_scores(image_scores, pixel_scores, threshold=...)` returns a Boolean pixel mask where pixel scores are below threshold.
- `issues_from_scores(image_scores, threshold=...)` returns image indices sorted by image score.
- `method="softmin"` is the default. It is efficient for ranking images from pixel scores.
- `method="num_pixel_issues"` computes image scores from the number of pixels flagged by `find_label_issues`; use this when the user wants ranking tied to estimated issue counts.

## Display and summarize masks

```python
from cleanlab.segmentation.summary import (
    display_issues,
    common_label_issues,
    filter_by_class,
)

display_issues(
    issues,
    labels=labels,
    pred_probs=pred_probs,
    class_names=["background", "object"],
    top=5,
)

issue_df = common_label_issues(
    issues,
    labels,
    pred_probs,
    class_names=["background", "object"],
    verbose=False,
)

car_issues = filter_by_class(class_index=1, issues=issues, labels=labels, pred_probs=pred_probs)
```

Display helper behavior:

- `display_issues` ranks images by number of issue pixels and highlights suspected pixels in red.
- Supplying `labels` shows the given mask; supplying `pred_probs` shows argmax predictions; supplying both gives side-by-side context.
- `class_names` must match the integer class order.
- `exclude=[class_id, ...]` hides issue pixels whose given label is in the excluded classes; `labels` is required when using `exclude`.
- Use a non-interactive matplotlib backend, such as `Agg`, in scripts or headless CI.

Summary helper behavior:

- `common_label_issues` returns a DataFrame with `given_label`, `predicted_label`, and `num_pixel_issues` columns.
- `filter_by_class` returns issue pixels where either the given label or predicted argmax is the requested class. This helps review all confusions involving a class.

## Review interpretation

Segmentation has pixel-level and image-level views:

- A `True` pixel in `issues` is a proposed mislabeled pixel, not necessarily a full object/mask boundary error.
- A low `image_score` prioritizes images for review, but it does not localize the wrong class without `pixel_scores` or `issues`.
- `issues.sum(axis=(1, 2))` gives issue-pixel counts per image; it is often the easiest way to choose top masks to display.
- Downsampling can broaden or miss small patches. Use low/no downsampling when investigating small mislabeled regions.

## Not this route

- Object-detection bounding boxes route to [`object-detection.md`](object-detection.md).
- Image-level classification label issues route to `classification` or `datalab`.
- Broad dataset audits and reporting wrappers route to `datalab`.
