# Object Detection Label Issues

Use this route for image datasets where each image has zero or more annotated bounding boxes, and each box has one class label.

## Inputs

Cleanlab uses labels and detector predictions, not the raw images, for scoring. Raw images are only needed for visualization.

```python
labels = [
    {
        "bboxes": np.array([[12, 20, 48, 90], [100, 30, 160, 120]]),
        "labels": np.array([0, 2]),
        "image_name": "image_0001.jpg",  # optional; extra keys may be kept for lookup
    },
]

predictions = [
    np.array(
        [
            np.array([[12, 20, 48, 90, 0.98]]),      # class 0 predictions
            np.empty((0, 5), dtype=float),           # class 1 predictions
            np.array([[98, 32, 158, 120, 0.91]]),    # class 2 predictions
        ],
        dtype=object,
    )
]
```

Required invariants:

- `labels` is a list of length `N`; `labels[i]` is a dictionary.
- Required label keys are `"bboxes"` and `"labels"`.
- `labels[i]["bboxes"]` has shape `(L_i, 4)` in `[x1, y1, x2, y2]` order.
- `labels[i]["labels"]` has shape `(L_i,)`, with class ids `0, 1, ..., K-1`.
- `predictions` is a list of length `N`; `predictions[i]` has length/shape `K`.
- `predictions[i][k]` is an array of shape `(M_ik, 5)` with columns `[x1, y1, x2, y2, pred_prob]` for predicted boxes of class `k`.
- Empty class predictions should be `np.empty((0, 5), dtype=float)`, not `None`.
- Coordinates use the image matrix convention: `(x1, y1)` top-left and `(x2, y2)` bottom-right.

## Find image-level issues

```python
from cleanlab.object_detection.filter import find_label_issues

issue_mask = find_label_issues(labels, predictions)
ranked_issue_indices = find_label_issues(
    labels,
    predictions,
    return_indices_ranked_by_score=True,
)
```

Interpretation:

- Default return is a Boolean mask of length `N`; `True` means the image is suspected to contain at least one object-label issue.
- With `return_indices_ranked_by_score=True`, the return is a shorter array of image indices sorted from most to least suspicious.
- Cleanlab considers three issue subtypes: overlooked objects, swapped class labels, and badly located boxes.
- `overlapping_label_check=True` penalizes very similar annotated boxes with conflicting classes. Set it to `False` only when duplicate overlapping labels are expected by the dataset policy.

## Rank images and inspect subtype scores

```python
from cleanlab.object_detection.rank import (
    get_label_quality_scores,
    issues_from_scores,
    compute_overlooked_box_scores,
    compute_badloc_box_scores,
    compute_swap_box_scores,
    pool_box_scores_per_image,
)

scores = get_label_quality_scores(labels, predictions, verbose=False)
review_indices = issues_from_scores(scores, threshold=0.5)

overlooked = compute_overlooked_box_scores(labels=labels, predictions=predictions)
badloc = compute_badloc_box_scores(labels=labels, predictions=predictions)
swap = compute_swap_box_scores(labels=labels, predictions=predictions)
badloc_image_scores = pool_box_scores_per_image(badloc)
```

Interpretation:

- `scores` has shape `(N,)`; lower means the image annotation is less likely correct.
- `issues_from_scores` is manual thresholding. It does not estimate the number of label errors.
- `compute_overlooked_box_scores` returns one score per predicted box; low scores suggest high-confidence predictions that may have been omitted from annotations.
- `compute_badloc_box_scores` returns one score per annotated box; low scores suggest the annotated box may be misplaced.
- `compute_swap_box_scores` returns one score per annotated box; low scores suggest the class label should be another class.
- `aggregation_weights={"overlooked": w1, "swap": w2, "badloc": w3}` can emphasize an issue subtype in image-level quality scores. The weights must be nonnegative and sum to 1.

## Visual review and summaries

```python
from cleanlab.object_detection.summary import (
    visualize,
    object_counts_per_image,
    bounding_box_size_distribution,
    class_label_distribution,
    get_sorted_bbox_count_idxs,
)

idx = int(ranked_issue_indices[0])
visualize(
    image=image_array_or_path,
    label=labels[idx],
    prediction=predictions[idx],
    class_names={"0": "car", "1": "person", "2": "dog"},
    overlay=False,
)

label_counts, pred_counts = object_counts_per_image(labels, predictions)
label_freq, pred_freq = class_label_distribution(labels, predictions)
label_sizes, pred_sizes = bounding_box_size_distribution(labels, predictions, sort=True)
sorted_label_counts, sorted_pred_counts = get_sorted_bbox_count_idxs(labels, predictions)
```

Visual helper behavior:

- `visualize` accepts an image path, numpy image array, or PIL image object.
- Given labels are drawn in red; predictions are drawn in blue.
- `overlay=False` shows labels and predictions side by side; `overlay=True` overlays both on one image.
- `prediction_threshold` hides predicted boxes below the confidence threshold.
- `save_path` can save a figure; use a non-interactive matplotlib backend such as `Agg` in scripts/CI.
- `class_names` should be a dictionary whose keys are stringified integer class ids, e.g. `{"0": "cat"}`.

Summary helper behavior:

- Object count and class/box-size distributions are exploratory review aids; they do not replace label-quality scores.
- Use unusually high/low box counts, rare classes, or abnormal box sizes to prioritize visual review.
- Per-class metric helpers compare predictions and labels across IoU thresholds; use them to interpret model behavior, not to directly edit labels.

## Review interpretation

Object detection issue outputs are image-level unless you explicitly compute subtype box scores:

- A flagged image means at least one box may be missing, mislabeled, or poorly located.
- A low image score does not identify the exact box by itself; use subtype scores and `visualize`.
- Low overlooked score: inspect a predicted box that may need a new annotation.
- Low badloc score: inspect the corresponding annotated box coordinates.
- Low swap score: inspect whether the annotated class conflicts with a high-confidence overlapping prediction.

## Not this route

- Image-level classification label issues use `classification` or `datalab`, not object detection.
- Broad image audit workflows involving many issue types should route to `datalab`.
- Semantic segmentation masks route to [`segmentation.md`](segmentation.md).
