# Data Formats for Structured Label Issues

Use this file to validate inputs before calling cleanlab. Most structured-label failures come from shape, nesting, or class-order mistakes.

## Token classification format

```python
# N sentences/documents, variable token counts, K classes.
tokens = [["Hello", "world"], ["Cleanlab", "rocks"]]
labels = [[0, 0], [1, 0]]
pred_probs = [
    np.array([[0.95, 0.05], [0.90, 0.10]]),
    np.array([[0.05, 0.95], [0.80, 0.20]]),
]
```

Checklist:

- `labels` is a nested list or list of arrays: `labels[i][j]` is the class id for token `j` in sentence/document `i`.
- `pred_probs` is a list of arrays: `pred_probs[i].shape == (len(labels[i]), K)`.
- Optional `tokens[i]` has exactly `len(labels[i])` strings.
- Class ids are zero-indexed integers in `0..K-1`.
- Probability rows are ordered by the same class ids.
- If using `class_names`, `class_names[k]` names class id `k`.

Returns to expect:

- `find_label_issues` returns `[(sentence_i, token_j), ...]`.
- `get_label_quality_scores` returns `sentence_scores` with shape `(N,)` and token-score Series per sentence.
- Display/common helpers consume the same tuple issue format.

## Object detection format

```python
# N images, K classes, variable annotated/predicted boxes per image/class.
labels = [
    {
        "bboxes": np.array([[0, 0, 10, 10], [20, 20, 40, 40]], dtype=float),
        "labels": np.array([0, 1], dtype=int),
    }
]

predictions = [
    np.array(
        [
            np.array([[0, 0, 10, 10, 0.99]], dtype=float),    # predicted class 0 boxes
            np.array([[22, 20, 42, 41, 0.88]], dtype=float),  # predicted class 1 boxes
        ],
        dtype=object,
    )
]
```

Label dictionary checklist:

- `labels` is a list of dictionaries, one per image.
- Required keys: `"bboxes"` and `"labels"`.
- `labels[i]["bboxes"].shape == (L_i, 4)`.
- `labels[i]["labels"].shape == (L_i,)`.
- Extra keys such as `"image_name"` or dataset-specific image filename fields may be retained for lookup/visual review; cleanlab scoring uses the boxes/classes.

Prediction checklist:

- `predictions` is a list with the same length as `labels`.
- `predictions[i]` has length `K`.
- `predictions[i][k]` contains predicted boxes for class `k` only.
- Each class array has shape `(M_ik, 5)` with columns `[x1, y1, x2, y2, pred_prob]`.
- Use `np.empty((0, 5), dtype=float)` for classes with no predictions.
- `pred_prob` is confidence/probability for the class represented by the containing `k` index.

Bounding-box coordinate checklist:

- Coordinates are `[x1, y1, x2, y2]`.
- `(x1, y1)` is top-left; `(x2, y2)` is bottom-right.
- Width/height should be nonnegative: `x2 >= x1`, `y2 >= y1`.
- Keep the coordinate system consistent with the image array/path used in `visualize`.

Returns to expect:

- `find_label_issues` returns a Boolean image mask by default, or ranked image indices when requested.
- `get_label_quality_scores` returns image scores with shape `(N,)`.
- Per-box subtype helpers return lists of arrays; array lengths depend on the number of annotated or predicted boxes in each image.
- `visualize` takes one `labels[i]`, one `predictions[i]`, and optionally an image path/array/PIL image.

## Semantic segmentation format

```python
# N images, K classes, fixed H/W per array.
labels = np.array([
    [[0, 0, 1],
     [0, 1, 1]],
], dtype=int)                   # shape (N, H, W)

pred_probs = np.array([
    [
        [[0.9, 0.8, 0.2], [0.9, 0.1, 0.1]],  # class 0 probabilities
        [[0.1, 0.2, 0.8], [0.1, 0.9, 0.9]],  # class 1 probabilities
    ]
], dtype=float)                 # shape (N, K, H, W)
```

Checklist:

- `labels.ndim == 3` and `labels.shape == (N, H, W)`.
- `pred_probs.ndim == 4` and `pred_probs.shape == (N, K, H, W)`.
- The `N`, `H`, and `W` dimensions match between `labels` and `pred_probs`.
- Class ids in `labels` are zero-indexed integers in `0..K-1`.
- The second axis of `pred_probs` is class id order.
- One-hot masks must be converted: `labels = np.argmax(labels_one_hot, axis=1)` for one-hot shape `(N, K, H, W)`.
- `downsample` values for issue finding must divide both `H` and `W`.

Returns to expect:

- `find_label_issues` returns a Boolean pixel mask with shape `(N, H, W)`.
- `get_label_quality_scores` returns `(image_scores, pixel_scores)` where `image_scores.shape == (N,)` and `pixel_scores.shape == (N, H, W)`.
- `issues_from_scores` returns a Boolean pixel mask if `pixel_scores` is supplied, otherwise image indices.
- Display/common helpers consume the Boolean mask format.

## Cross-family distinctions

| Family | Example unit | Issue granularity | Summary granularity |
|---|---|---|---|
| Token classification | sentence/document of tokens | `(sentence_i, token_j)` | sentence scores and repeated token/label-swap summaries |
| Object detection | image with boxes | image mask/indices; optional per-box subtype scores | image scores, box-count/class/size distributions |
| Semantic segmentation | image mask | Boolean pixel mask `(N,H,W)` | image scores, pixel-score masks, class-swap summaries |

If the user only has one scalar label per row, this sub-skill is the wrong route. Use `classification`, `tabular-label-issues`, or `datalab` depending on the task.
