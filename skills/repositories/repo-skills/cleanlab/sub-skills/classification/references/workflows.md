# Workflows

## Workflow 1: train a robust binary or multiclass classifier

Use this when the user wants to fit a model on noisy labels and then predict on new data.

```python
from sklearn.linear_model import LogisticRegression
from cleanlab.classification import CleanLearning

clf = LogisticRegression(solver="liblinear", max_iter=200, random_state=0)
cl = CleanLearning(
    clf=clf,
    seed=0,
    cv_n_folds=5,
    find_label_issues_kwargs={"min_examples_per_class": 1, "n_jobs": 1},
)
cl.fit(X_train, noisy_labels)
issues = cl.get_label_issues()
preds = cl.predict(X_test)
probs = cl.predict_proba(X_test)
```

Use `validation_func(X_val, y_val)` if the estimator needs validation kwargs during each fold.
If the user already has out-of-sample `pred_probs`, pass them into `fit(..., pred_probs=pred_probs)` or `find_label_issues(...)`.

## Workflow 2: find and rank suspect labels directly from `pred_probs`

Use this when a model has already produced out-of-sample probabilities.

```python
from cleanlab.filter import find_label_issues
from cleanlab.count import num_label_issues
from cleanlab.rank import get_label_quality_scores

scores = get_label_quality_scores(labels, pred_probs)
num_issues = num_label_issues(labels, pred_probs)
issue_mask = find_label_issues(
    labels,
    pred_probs,
    filter_by="confident_learning",
    min_examples_per_class=1,
    n_jobs=1,
)
ranked_issue_idx = find_label_issues(
    labels,
    pred_probs,
    filter_by="confident_learning",
    min_examples_per_class=1,
    n_jobs=1,
    return_indices_ranked_by="self_confidence",
)
```

Good defaults:

- use `self_confidence` for outlier-like or ambiguous bad labels
- use `normalized_margin` for class-conditional flips
- use `confidence_weighted_entropy` when uncertainty matters more than the margin

## Workflow 3: summarize dataset health

Use this when the user wants to understand class-level quality or class overlap.

```python
from cleanlab.dataset import health_summary

summary = health_summary(labels=labels, pred_probs=pred_probs, verbose=False)
score = summary["overall_label_health_score"]
classes_df = summary["classes_by_label_quality"]
overlap_df = summary["overlapping_classes"]
```

If the user wants a dataset audit that spans multiple issue types, route them to `datalab` instead.

## Workflow 4: estimate latent noise structure

Use this when the user wants the confident joint, class priors, or noise matrices.

```python
from cleanlab.count import estimate_py_noise_matrices_and_cv_pred_proba

py, noise_matrix, inverse_noise_matrix, confident_joint, pred_probs = (
    estimate_py_noise_matrices_and_cv_pred_proba(
        X_train,
        noisy_labels,
        clf=clf,
        cv_n_folds=5,
        seed=0,
    )
)
```

Variants:

- already have `pred_probs` -> use `estimate_py_and_noise_matrices_from_probabilities`
- already have `confident_joint` -> use `estimate_latent`
- want only out-of-sample `pred_probs` -> use `estimate_cv_predicted_probabilities`

## Workflow 5: benchmark synthetic label noise

Use this when the user wants a safe deterministic fixture or a benchmark dataset.

```python
from cleanlab.benchmarking.noise_generation import generate_noise_matrix_from_trace, generate_noisy_labels

noise_matrix = generate_noise_matrix_from_trace(
    K=3,
    trace=2.2,
    py=np.array([0.3, 0.4, 0.3]),
    valid_noise_matrix=True,
    seed=0,
)
noisy_labels = generate_noisy_labels(true_labels, noise_matrix)
```

Always check `noise_matrix_is_valid` when the user is debugging synthetic noise.

## Workflow 6: low-memory batch label checking

Keep this as a cross-link, not the main route.

```python
from cleanlab.experimental.label_issues_batched import find_label_issues_batched

issues = find_label_issues_batched(
    labels=labels,
    pred_probs=pred_probs,
    return_mask=True,
    verbose=False,
)
```

Use this only when memory is the bottleneck or the user explicitly asks for batch-mode checking.

## Workflow 7: classify by data value

Use `data_shapley_knn` when the user asks which examples help or hurt a classifier.

```python
from cleanlab.data_valuation import data_shapley_knn

scores = data_shapley_knn(labels=labels, features=features, k=3)
```

If the user already has a KNN graph, pass it directly instead of recomputing it.
