# Workflows

Assume `import numpy as np` and the relevant `cleanlab.multiannotator` imports when copying the snippets below.

## 1. Start from long-format annotations

Use this when your annotations arrive as event logs or a flat table.

1. Build a DataFrame with exactly `task`, `annotator`, and `label` columns.
2. Convert it to the wide matrix expected by the multiannotator APIs.
3. Train the classifier in the classification route to produce out-of-sample `pred_probs`.
4. Run the multiannotator analysis on the wide labels and model probabilities.

```python
wide = convert_long_to_wide_dataset(long_annotations)
majority_vote = get_majority_vote_label(wide, pred_probs)
results = get_label_quality_multiannotator(
    wide,
    pred_probs,
    consensus_method=["majority_vote", "best_quality"],
    return_weights=True,
    verbose=False,
)
```

Inspect these outputs first:

- `results["label_quality"]` for per-example consensus and quality.
- `results["detailed_label_quality"]` for per-annotator label scores.
- `results["annotator_stats"]` for per-annotator summary quality.

## 2. Compare majority vote vs best-quality consensus

Use this when you want a simple baseline and a model-aware consensus side by side.

- `majority_vote` is the quick baseline.
- `best_quality` uses the model probabilities plus the raw annotations.
- If you pass a list of consensus methods, the first method fills the base `label_quality` columns and later methods add suffixed columns such as `consensus_label_best_quality`.
- If you only want agreement-based consensus quality, set `quality_method="agreement"` and keep `return_weights=False`.

```python
results = get_label_quality_multiannotator(
    wide,
    pred_probs,
    consensus_method=["majority_vote", "best_quality"],
    quality_method="crowdlab",
    return_weights=True,
    verbose=False,
)
```

A good post-check is to compare the majority-vote labels with the model-aware consensus labels and review the lowest `consensus_quality_score` rows.

## 3. Prioritize relabeling with active learning

Use this when you want to decide which examples should get another annotation next.

```python
scores_labeled, scores_unlabeled = get_active_learning_scores(
    labels_multiannotator=wide,
    pred_probs=labeled_pred_probs,
    pred_probs_unlabeled=unlabeled_pred_probs,
)
```

Guidelines:

- Lower scores mean higher relabeling priority.
- Sort ascending and select the lowest-scoring rows for the next annotation batch.
- Re-run the workflow after collecting labels and retraining the classifier in the classification route.
- If you only have unlabeled examples, pass just `pred_probs_unlabeled`.

```python
next_batch = np.argsort(scores_unlabeled)[:batch_size]
```

## 4. Use stacked model predictions for ensembles

Use this when you have several trained classifiers and want ensemble-aware consensus or active-learning scores.

```python
pred_probs_ensemble = np.stack([pred_probs_model_1, pred_probs_model_2])
results = get_label_quality_multiannotator_ensemble(
    wide,
    pred_probs_ensemble.copy(),
    return_weights=True,
)

scores_labeled, scores_unlabeled = get_active_learning_scores_ensemble(
    wide,
    pred_probs_ensemble.copy(),
    unlabeled_pred_probs_ensemble.copy(),
)
```

Notes:

- Ensemble probabilities must have shape `(P, N, K)`.
- The ensemble helpers return per-model weights in `model_weight`.
- Pass copies if you need the original probability arrays unchanged afterward.

## 5. One tiny end-to-end pattern

1. Convert long annotations to wide form.
2. Compute a majority-vote baseline.
3. Train the classifier in the classification route and collect out-of-sample `pred_probs`.
4. Run `get_label_quality_multiannotator` for consensus and annotator stats.
5. Run `get_active_learning_scores` to choose the next items to label.
6. If you have multiple models, switch to the ensemble helpers without changing the annotation tables.
