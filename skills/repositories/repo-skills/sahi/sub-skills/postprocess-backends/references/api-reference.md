# Direct API and class reference

SAHI postprocessing has two public layers:

- Direct array functions for small custom pipelines or assertions.
- Postprocess classes that operate on `ObjectPrediction` lists and are used by higher-level prediction flows.

This reference covers the algorithms and call contracts only. Use `../sliced-inference/SKILL.md` for where to pass these options in `get_sliced_prediction`, `predict`, or CLI commands.

## Array input contract

Direct functions consume a numpy array with shape `(N, 6)` and columns:

| Column | Meaning |
| --- | --- |
| `0` | `x1` left coordinate |
| `1` | `y1` top coordinate |
| `2` | `x2` right coordinate |
| `3` | `y2` bottom coordinate |
| `4` | confidence score |
| `5` | category id |

Use `dtype=np.float32` for predictable behavior. Category ids are used only by `batched_*` functions, which run per category.

```python
import numpy as np
from sahi.postprocess.backends import set_postprocess_backend
from sahi.postprocess.combine import batched_nms, greedy_nmm, nmm, nms

set_postprocess_backend("numpy")

predictions = np.array(
    [
        [0, 0, 10, 10, 0.90, 1],
        [1, 1, 9, 9, 0.80, 1],
        [0, 0, 10, 10, 0.70, 2],
        [30, 30, 40, 40, 0.60, 1],
    ],
    dtype=np.float32,
)

print(nms(predictions, match_metric="IOU", match_threshold=0.5))
print(batched_nms(predictions, match_metric="IOU", match_threshold=0.5))
print(greedy_nmm(predictions, match_metric="IOU", match_threshold=0.5))
print(nmm(predictions, match_metric="IOU", match_threshold=0.5))
```

## Direct functions

| Function | Class behavior | Return value | Use when |
| --- | --- | --- | --- |
| `nms(predictions, match_metric="IOU", match_threshold=0.5)` | Class-agnostic; all category ids compete together. | `list[int]` kept indices sorted by score descending. | Duplicate boxes should be discarded. |
| `batched_nms(predictions, ...)` | Class-aware; runs `nms` independently per category and remaps indices. | `list[int]` kept global indices sorted by score descending. | Different categories must not suppress each other. |
| `greedy_nmm(predictions, ...)` | Class-agnostic. | `dict[int, list[int]]` mapping keeper index to directly merged indices. | Overlapping boxes should merge instead of being discarded, without transitive expansion. |
| `batched_greedy_nmm(predictions, ...)` | Class-aware. | `dict[int, list[int]]` with global indices. | Per-category greedy merging. |
| `nmm(predictions, ...)` | Class-agnostic. | `dict[int, list[int]]` mapping keeper index to merged indices after transitive matching. | A chain of overlapping boxes should collapse under the best keeper. |
| `batched_nmm(predictions, ...)` | Class-aware. | `dict[int, list[int]]` with global indices. | Per-category transitive merging. |

### NMS versus NMM

| Need | Prefer | Why |
| --- | --- | --- |
| Remove duplicate detections and keep the highest score only. | NMS | Lower-scored overlapping boxes are suppressed. |
| Preserve evidence from duplicates by expanding box/mask coverage. | GreedyNMM or NMM | Merged predictions can combine bounding boxes, masks, scores, and categories at the class layer. |
| Avoid transitive over-merging across a chain of boxes. | GreedyNMM | Each keeper merges direct neighbors only. |
| Treat A-overlaps-B and B-overlaps-C as one object even if A barely touches C. | NMM | Full NMM allows transitive merge propagation. |

## Match metrics

| Metric | Meaning | Good fit | Common failure if wrong |
| --- | --- | --- | --- |
| `"IOU"` | Intersection area divided by union area. | Similar-size duplicate boxes. | Nested small boxes may not match because union is dominated by the large box. |
| `"IOS"` | Intersection area divided by the smaller box area. | Small object nested inside a larger duplicate or tile-boundary box. | Nearby different objects with containment-like geometry can merge or suppress too aggressively. |

Nested-box example:

```python
import numpy as np
from sahi.postprocess.combine import nms

nested = np.array(
    [
        [0, 0, 100, 100, 0.90, 1],
        [10, 10, 20, 20, 0.80, 1],
    ],
    dtype=np.float32,
)

print(nms(nested, match_metric="IOU", match_threshold=0.5))  # keeps both
print(nms(nested, match_metric="IOS", match_threshold=0.5))  # keeps only the larger, higher-scored box
```

Use uppercase `"IOU"` or `"IOS"`. Do not pass arbitrary metric strings; low-level backend functions are optimized around these two choices.

## Class-aware versus class-agnostic behavior

Direct low-level functions:

- `nms`, `greedy_nmm`, and `nmm` ignore the category id for matching. A car and a person can suppress or merge if geometry and score order say they match.
- `batched_nms`, `batched_greedy_nmm`, and `batched_nmm` split by category id first. Categories do not compete.

Postprocess classes:

- `class_agnostic=True` uses the global functions.
- `class_agnostic=False` uses the corresponding `batched_*` function.

Class-aware example:

```python
from sahi.postprocess.combine import NMSPostprocess

postprocessor = NMSPostprocess(
    match_threshold=0.5,
    match_metric="IOU",
    class_agnostic=False,
)
filtered_predictions = postprocessor(object_predictions)
```

## Postprocess classes

| Class | Algorithm | Main arguments | Output |
| --- | --- | --- | --- |
| `NMSPostprocess` | Suppression. | `match_threshold`, `match_metric`, `class_agnostic`. | Selected `ObjectPrediction` objects. |
| `GreedyNMMPostprocess` | Direct-neighbor merging. | Same. | Merged `ObjectPrediction` objects. |
| `NMMPostprocess` | Transitive merging. | Same. | Merged `ObjectPrediction` objects. |

Class usage pattern:

```python
from sahi.postprocess.combine import GreedyNMMPostprocess

postprocessor = GreedyNMMPostprocess(
    match_threshold=0.5,
    match_metric="IOS",
    class_agnostic=False,
)
merged_predictions = postprocessor(object_predictions)
```

For NMM classes, the merge step can combine bounding boxes, masks, scores, and category metadata. If both predictions have masks, mask geometry is unioned. If masks are absent, only box/score/category data are merged.

## Edge behavior to remember

- Empty direct input returns `[]` for NMS and `{}` for NMM variants.
- A single input box is kept as `[0]` or `{0: []}`.
- `match_threshold <= 0` means every pair is considered a match because IOU/IOS are non-negative; use positive thresholds unless intentionally collapsing all boxes.
- Higher `match_threshold` keeps more boxes; lower `match_threshold` suppresses or merges more boxes.
- Equal-score tie-breaking is deterministic in the numpy/numba implementations. If exact cross-backend tie order matters, force `"numpy"` and write assertions around the expected order.
