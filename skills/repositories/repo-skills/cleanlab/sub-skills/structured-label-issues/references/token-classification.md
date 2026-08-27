# Token Classification Label Issues

Use this route for NER, POS tagging, or any task where each sentence/document contains tokens and every token has a class label.

## Inputs

Cleanlab expects parallel nested structures:

```python
labels = [
    [0, 0, 1],      # sentence 0 has 3 token labels
    [0, 1],         # sentence 1 has 2 token labels
]
pred_probs = [
    np.array([[0.9, 0.1], [0.7, 0.3], [0.05, 0.95]]),
    np.array([[0.8, 0.2], [0.8, 0.2]]),
]
tokens = [
    ["A", "valid", "sentence"],
    ["A", "bad"],
]
```

Required invariants:

- `len(labels) == len(pred_probs) == len(tokens)` if `tokens` are used.
- For every sentence `i`, `len(labels[i]) == pred_probs[i].shape[0] == len(tokens[i])`.
- `pred_probs[i].shape == (T_i, K)` where `T_i` is token count and `K` is number of classes.
- Class ids in `labels` are integers `0, 1, ..., K-1`.
- Probability columns must use the same class order as the integer labels and optional `class_names`.
- Prefer out-of-sample token probabilities, e.g. from cross-validation or a held-out model.

## Find token label issues

```python
from cleanlab.token_classification.filter import find_label_issues

issues = find_label_issues(
    labels,
    pred_probs,
    return_indices_ranked_by="self_confidence",
)
# Example return: [(sentence_index, token_index), ...]
```

`issues` is a list of `(sentence_index, token_index)` tuples sorted so the most suspicious token labels appear first. Other ranking methods are `"normalized_margin"` and `"confidence_weighted_entropy"`.

Use `low_memory=True` for large flattened token sets when memory is the bottleneck:

```python
issues = find_label_issues(labels, pred_probs, low_memory=True)
```

When `low_memory=True`, extra kwargs passed through to the normal classifier-label helper are not used and cleanlab emits warnings about them.

## Rank sentences and tokens

```python
from cleanlab.token_classification.rank import get_label_quality_scores, issues_from_scores

sentence_scores, token_scores = get_label_quality_scores(
    labels,
    pred_probs,
    tokens=tokens,
    token_score_method="self_confidence",
    sentence_score_method="min",
)

manual_issues = issues_from_scores(sentence_scores, token_scores=token_scores, threshold=0.1)
```

Interpretation:

- `sentence_scores` has shape `(N,)`; lower means the sentence is more likely to contain at least one bad token label.
- `token_scores` is a list of pandas Series; each Series is one sentence. If `tokens` was supplied, token strings are the Series index.
- `sentence_score_method="min"` uses the lowest token score in a sentence. `"softmin"` uses all token scores and accepts `sentence_score_kwargs={"temperature": value}`.
- `issues_from_scores(..., token_scores=...)` returns token tuples. Without `token_scores`, it returns sentence indices whose sentence score is below the threshold.

Use `find_label_issues` when the user wants cleanlab to estimate the issue set. Use score thresholding only when the user wants a custom precision/recall tradeoff or a limited review queue.

## Display and summarize

```python
from cleanlab.token_classification.summary import (
    display_issues,
    common_label_issues,
    filter_by_token,
)

display_issues(
    issues,
    tokens,
    labels=labels,
    pred_probs=pred_probs,
    class_names=["O", "PER", "ORG"],
    exclude=[(0, 1), (1, 0)],
    top=20,
)

summary_df = common_label_issues(
    issues,
    tokens,
    labels=labels,
    pred_probs=pred_probs,
    class_names=["O", "PER", "ORG"],
    verbose=False,
)

united_issues = filter_by_token("United", issues, tokens)
```

Display helper behavior:

- `display_issues` prints sentences and highlights issue tokens. With `labels` and `pred_probs`, it also prints the given and predicted class for the token.
- `exclude` is a list of `(given_label, predicted_label)` swaps to suppress during display or common-issue summaries.
- `class_names` must be in integer class-id order.
- `common_label_issues` returns token frequency information; with both `labels` and `pred_probs`, it returns repeated given/predicted swap patterns.
- `filter_by_token` is case-insensitive and returns only issue tuples involving that token string.

## Review interpretation

Token classification exposes both token-level and sentence-level views:

- A token tuple `(i, j)` says the `j`-th token in sentence/document `i` is suspicious.
- A low sentence score says at least one token in the sentence may be wrong; it is not itself proof that every token in the sentence is wrong.
- Common-token summaries can reveal ambiguous words or systematic annotation-policy drift.
- If many tokens share the same confusion, inspect class mapping/IOB normalization before changing labels.

## Not this route

- Span classification belongs to the sibling `experimental` sub-skill, not this token-classification route.
- Standard one-label-per-row text classification belongs to `classification`.
- Broad dataset audit/reporting belongs to `datalab`.
