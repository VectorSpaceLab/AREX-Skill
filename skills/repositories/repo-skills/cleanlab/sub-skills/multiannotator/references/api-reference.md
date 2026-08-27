# API Reference

## Input contracts

- **Wide multiannotator labels**: 2D `pd.DataFrame` or `np.ndarray` with shape `(N, M)`.
  - Rows are examples.
  - Columns are annotators.
  - Labels must be integer class IDs `0..K-1`.
  - Missing annotations must be `NaN` or `pd.NA`.
- **Long multiannotator labels**: `pd.DataFrame` with columns exactly `task`, `annotator`, and `label`.
- **Model probabilities**:
  - Single-model APIs expect `pred_probs` with shape `(N, K)`.
  - Ensemble APIs expect `pred_probs` with shape `(P, N, K)`.
- If you pass a `pd.DataFrame` of labels, its column names become annotator IDs in downstream outputs.

## `convert_long_to_wide_dataset`

```python
convert_long_to_wide_dataset(labels_multiannotator_long: pd.DataFrame) -> pd.DataFrame
```

- Pivots a long annotation table into the wide matrix expected by the other multiannotator APIs.
- Uses `task` as the row index, `annotator` as columns, and `label` as values.
- Missing task/annotator pairs become `NaN`.
- The returned DataFrame is ready to pass into `get_majority_vote_label`, `get_label_quality_multiannotator`, or the active-learning helpers.

## `get_majority_vote_label`

```python
def get_majority_vote_label(
    labels_multiannotator: pd.DataFrame | np.ndarray,
    pred_probs: np.ndarray | None = None,
    verbose: bool = True,
) -> np.ndarray
```

- Returns one consensus label per example.
- Tie-breaking order:
  1. Highest model probability from `pred_probs` if provided.
  2. Class frequency in the full annotation table.
  3. Annotator-quality fallback.
  4. Random choice if a tie still remains.
- Use this as a quick baseline before running the full label-quality workflow.
- If you need the classifier that produced `pred_probs`, use the classification route for training and cross-validation.

## `get_label_quality_multiannotator`

```python
def get_label_quality_multiannotator(
    labels_multiannotator: pd.DataFrame | np.ndarray,
    pred_probs: np.ndarray,
    *,
    consensus_method: str | list[str] = "best_quality",
    quality_method: str = "crowdlab",
    calibrate_probs: bool = False,
    return_detailed_quality: bool = True,
    return_annotator_stats: bool = True,
    return_weights: bool = False,
    verbose: bool = True,
    label_quality_score_kwargs: dict = {},
) -> dict[str, object]
```

### Main return keys

| Key | Returned when | Meaning |
| --- | --- | --- |
| `label_quality` | always | Per-example consensus table. |
| `detailed_label_quality` | `return_detailed_quality=True` | Per-annotator label-quality scores. |
| `annotator_stats` | `return_annotator_stats=True` | Per-annotator summary statistics. |
| `model_weight` | `return_weights=True` and `quality_method="crowdlab"` | Single-model trust weight used in the crowdlab calculation. |
| `annotator_weight` | `return_weights=True` and `quality_method="crowdlab"` | Length-`M` annotator trust weights. |

### `label_quality` columns

- `consensus_label`
- `consensus_quality_score`
- `annotator_agreement`
- `num_annotations`
- If `consensus_method` is a list, the first method fills the base columns and later methods add suffixed columns such as `consensus_label_majority_vote` and `consensus_label_best_quality`.

### `detailed_label_quality`

- One column per annotator.
- Column names are prefixed with `quality_annotator_`.
- Values are `NaN` for examples that that annotator did not label.

### `annotator_stats`

- Indexed by annotator ID when labels are passed as a DataFrame.
- Columns:
  - `annotator_quality`
  - `agreement_with_consensus`
  - `worst_class`
  - `num_examples_labeled`
- Sorted from lowest annotator quality to highest.

### Behavior notes

- `quality_method="crowdlab"` combines raw annotations with the trained classifier's probabilities.
- `quality_method="agreement"` uses consensus agreement only.
- `calibrate_probs=True` temperature-scales the classifier probabilities before consensus scoring.
- `return_weights=True` only works with `quality_method="crowdlab"` in the single-model API.
- `label_quality_score_kwargs` is forwarded to `cleanlab.rank.get_label_quality_scores`.

## `get_label_quality_multiannotator_ensemble`

```python
def get_label_quality_multiannotator_ensemble(
    labels_multiannotator: pd.DataFrame | np.ndarray,
    pred_probs: np.ndarray,
    *,
    calibrate_probs: bool = False,
    return_detailed_quality: bool = True,
    return_annotator_stats: bool = True,
    return_weights: bool = False,
    verbose: bool = True,
    label_quality_score_kwargs: dict = {},
) -> dict[str, object]
```

- Same output structure as the single-model API.
- `pred_probs` must have shape `(P, N, K)`.
- `model_weight` is an array of shape `(P,)` with one weight per model in the ensemble.
- `annotator_weight` still has one entry per annotator.
- The ensemble helper uses the stacked model predictions directly; do not pass a 2D array here.
- If you need the model-training side for the ensemble, keep that in the classification route.

## `get_active_learning_scores`

```python
def get_active_learning_scores(
    labels_multiannotator: pd.DataFrame | np.ndarray | None = None,
    pred_probs: np.ndarray | None = None,
    pred_probs_unlabeled: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]
```

- Returns two arrays:
  - `active_learning_scores` for already-labeled examples.
  - `active_learning_scores_unlabeled` for unlabeled examples.
- Lower scores mean a row should be prioritized sooner for additional annotation.
- Pass both labeled and unlabeled probabilities when you want one ranked pool.
- Labeled examples with no annotations should not be included in `labels_multiannotator`.
- The function also supports the degenerate single-annotator case, but the main noisy-label workflow for a single annotator belongs in the classification route.

## `get_active_learning_scores_ensemble`

```python
def get_active_learning_scores_ensemble(
    labels_multiannotator: pd.DataFrame | np.ndarray | None = None,
    pred_probs: np.ndarray | None = None,
    pred_probs_unlabeled: np.ndarray | None = None,
) -> tuple[np.ndarray, np.ndarray]
```

- Same return contract as the single-model active-learning API.
- `pred_probs` and `pred_probs_unlabeled` must have shape `(P, N, K)`.
- The returned scores are directly comparable between labeled and unlabeled rows from the same call.
- This helper temperature-scales the model arrays it receives, so pass copies if you need the originals unchanged afterward.

## Tiny call pattern

```python
from cleanlab.multiannotator import (
    convert_long_to_wide_dataset,
    get_label_quality_multiannotator,
    get_majority_vote_label,
    get_active_learning_scores,
)

wide = convert_long_to_wide_dataset(long_annotations)
majority_vote = get_majority_vote_label(wide, pred_probs)
results = get_label_quality_multiannotator(wide, pred_probs)
label_quality = results["label_quality"]
labeled_scores, unlabeled_scores = get_active_learning_scores(wide, pred_probs, pred_probs_unlabeled)
```
