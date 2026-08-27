# Regression workflows

Use this route when the target is numeric and the main question is whether some `y` values look corrupted.

## 1. Score numeric labels from predictions

If you already have out-of-sample predictions, score the targets directly with `cleanlab.regression.rank.get_label_quality_scores`.

```python
from cleanlab.regression.rank import get_label_quality_scores

scores = get_label_quality_scores(labels=y, predictions=y_pred, method="outre")
```

- `outre` is the default and usually the first choice.
- `residual` is the simpler alternative.
- Scores are in `[0, 1]`; lower means a more suspicious numeric target.

## 2. Use CleanLearning when you want the model to help clean the data

`CleanLearning` wraps an sklearn-compatible regressor, estimates label issues, and refits on the cleaned data.

```python
from sklearn.linear_model import LinearRegression
from cleanlab.regression.learn import CleanLearning

cl = CleanLearning(model=LinearRegression(), cv_n_folds=5)
issues = cl.find_label_issues(X, y)
cl.fit(X, y, label_issues=issues)
preds = cl.predict(X_test)
score = cl.score(X_test, y_test)
```

`find_label_issues(...)` returns a DataFrame with:
- `is_label_issue`
- `label_quality`
- `given_label`
- `predicted_label`

## 3. Handle sample weights carefully

- Pass `sample_weight` directly to `CleanLearning.fit(...)` or `CleanLearning.score(...)`.
- The wrapped model must accept `sample_weight` if you want to use it.
- The `sample_weight` array must match the number of rows in `X` and `y`.

## 4. When to switch to Datalab

Use `Datalab(..., task="regression")` when you want a broader dataset audit.
The same numeric target semantics apply, but Datalab also reports other issue types and uses `label_score` in its issue tables.

If you only need to rank or clean numeric targets, stay on the direct regression APIs in this sub-skill.

## 5. Practical reminders

- Keep regression labels numeric and 1D.
- Keep predictions and targets aligned example-for-example.
- If the model is not sklearn-compatible or not clonable, use the direct scoring helper with precomputed predictions instead of `CleanLearning`.
- If you are cleaning standard multiclass classification labels, route to `classification` instead.
