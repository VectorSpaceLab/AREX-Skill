# Supervised model troubleshooting

Use this when a River supervised classifier, regressor, wrapper, optimizer, or compatibility bridge behaves unexpectedly.

## Incompatible metric errors

Symptoms:

- A model-selection constructor raises that a metric cannot evaluate a model.
- Progressive validation fails when a metric receives probabilities but expects labels, or receives labels but expects probabilities.
- Regression metrics are used with classifiers or classification metrics with regressors.

Fix:

1. Match task type first: classifier with classification metric, regressor with regression metric, multioutput estimator with multioutput metric wrappers.
2. If the metric requires labels, the model must expose `predict_one` and produce scalar labels/values.
3. If the metric requires probabilities, the classifier must expose `predict_proba_one` and return a class-probability dictionary.
4. For `model_selection.SuccessiveHalvingClassifier`, the selector uses `predict_one` when its metric requires labels and `predict_proba_one` otherwise. Every candidate must support the required method.
5. For a selector over several pipelines, validate the outer pipeline's final estimator, not just the inner model.

Safe replacement examples:

- Binary or multiclass classifier labels: `metrics.Accuracy()`, `metrics.MacroF1()`.
- Probabilistic classification: `metrics.LogLoss()`, `metrics.CrossEntropy()`, `metrics.ROCAUC()` when target/prediction shape matches the metric.
- Regression: `metrics.MAE()`, `metrics.MSE()`, `metrics.RMSE()`, `metrics.R2()`.
- Multioutput: wrap an appropriate base metric with `metrics.multioutput.MicroAverage(...)` or another multioutput metric strategy.

Route metric update-loop mechanics to `streaming-evaluation`.

## Binary versus multiclass targets

Symptoms:

- A binary classifier receives labels such as `"red"`, `"green"`, `"blue"` and later fails or returns unsuitable probabilities.
- `LogisticRegression` is chosen for a three-class problem without a wrapper.
- A scikit-learn compatibility wrapper complains that only binary classification is supported.

Fix:

- Use `linear_model.LogisticRegression` for binary labels, commonly booleans or two values that wrappers can map to booleans.
- Use `linear_model.SoftmaxRegression`, naive Bayes, trees, or forests for native multiclass behavior.
- Wrap a binary classifier with `multiclass.OneVsRestClassifier`, `OneVsOneClassifier`, or `OutputCodeClassifier` when native multiclass is not available or not desired.
- When converting a River classifier to scikit-learn, remember that non-multiclass River classifiers are checked as binary in the sklearn wrapper.
- When converting a scikit-learn classifier to River, pass all possible `classes` to `convert_sklearn_to_river` at conversion time.

Quick decision:

```python
from river import linear_model, multiclass

binary = linear_model.LogisticRegression()
native_multiclass = linear_model.SoftmaxRegression()
wrapped_multiclass = multiclass.OneVsRestClassifier(linear_model.LogisticRegression())
```

## Missing or absent `predict_proba_one`

Symptoms:

- A metric or wrapper calls `predict_proba_one` and the estimator does not have it.
- A probability dictionary is empty early in the stream.
- A wrapped sklearn classifier works for labels but fails for probabilities.

Fix:

1. Choose a probabilistic classifier such as `LogisticRegression`, `SoftmaxRegression`, naive Bayes, many tree/forest classifiers, or a wrapper that exposes probabilities.
2. For margin-only or label-only estimators, use a label metric or wrap/replace the model.
3. Warm up the model before relying on every class key. Online classifiers only know classes they have seen.
4. For `compat.convert_sklearn_to_river`, choose an sklearn classifier with `predict_proba`, such as `SGDClassifier(loss="log_loss")`; `partial_fit` alone is not enough for probability metrics.
5. For multiclass wrappers, check whether the base classifier's `predict_proba_one(x)` includes a `True` probability for binary wrappers.

Do not fabricate missing probabilities for evaluation unless the metric and downstream task explicitly define a cold-start default.

## Sample-weight parameter failures

Symptoms:

- `learn_one()` raises an unexpected keyword argument for `w` or `sample_weight`.
- A wrapper or ensemble silently ignores a weight-like keyword or passes it to a base model that cannot accept it.
- Weighted and unweighted runs produce identical state because weights never reached the final estimator.

Fix:

- Use `w=` for River GLM single-instance methods such as `LinearRegression.learn_one` and `LogisticRegression.learn_one`.
- Use `w=` for River Hoeffding tree variants and stochastic gradient trees that declare keyword-only weights.
- Use `learn_many(..., w=...)` for GLM mini-batch methods when using scalar or per-row weights.
- Do not use sklearn-style `sample_weight=` with River estimators unless the concrete wrapper explicitly accepts it.
- For wrappers and ensembles, inspect whether the outer `learn_one` accepts `**kwargs` and whether the inner model accepts `w=`. If either side does not, remove weights or choose a compatible model.

Minimal check:

```python
from river import linear_model, optim

model = linear_model.LogisticRegression(optimizer=optim.SGD(0.1))
model.learn_one({"x": 1.0}, True, w=2.0)
```

If this pattern works in isolation but fails in a pipeline or ensemble, the issue is parameter forwarding. Route pipeline parameter mechanics to `pipelines-and-features`.

## Optimizer/loss instability or no learning

Symptoms:

- Weights become huge, predictions saturate at 0/1, or regression predictions explode.
- A linear model appears not to learn.
- Changing loss changes target interpretation.
- L1 and L2 are both set and initialization fails.

Fix:

1. Scale dense numeric features before SGD-like optimizers.
2. Start with `optim.SGD(0.01)` or `optim.Adam(0.01)` and tune one order of magnitude at a time.
3. Reduce learning rate or use `clip_gradient` when predictions explode.
4. Match loss type to task: binary, multiclass, or regression.
5. Use `intercept_lr=0` only when you intentionally fix the intercept.
6. Do not set both `l1` and `l2` on GLM estimators.
7. For quantile regression, remember that the model predicts a quantile, not the conditional mean.
8. For `Poisson` loss, target values should be count-like and predictions are exponentiated through the loss mean function.
9. For factorization machines, set seeds/initializers for reproducibility and tune `n_factors`, learning rates, and regularization together.

## Optional sklearn, pandas, and dataframe dependencies

Symptoms:

- `river.compat` exposes no conversion functions or import fails with a missing scikit-learn module.
- `learn_many`/`predict_many` fails because no supported dataframe/series backend is available.
- Converting an sklearn estimator raises because it lacks `partial_fit`.
- A sklearn-to-River classifier raises because `classes` was not provided.

Fix:

- Install scikit-learn before using `river.compat`.
- Use sklearn estimators with `partial_fit` for sklearn-to-River conversion.
- Pass `classes=[...]` when converting sklearn classifiers to River.
- Install a supported dataframe backend before using mini-batch methods; pandas is the common optional dependency and River's pandas extra installs it.
- If mini-batch behavior is not required, use `learn_one`/`predict_one` to avoid dataframe dependency issues.
- For sklearn-to-River dictionaries, keep feature names stable; later frames must include the features seen by the first call.

## Tree and forest memory or growth surprises

Symptoms:

- A Hoeffding tree does not split in a small sample.
- A tree grows larger than expected.
- A memory cap seems to make accuracy worse.
- Adaptive forests consume much more CPU or memory than a single tree.

Fix:

1. Lower `grace_period` only for smoke tests or fast adaptation; larger values are normal in real streams.
2. Use `max_depth` to cap depth when model size must be predictable.
3. Use `max_size` and `memory_estimate_period` to let the tree deactivate less promising leaves under memory pressure.
4. Set `stop_mem_management=True` only if you prefer stopping growth over active/inactive leaf management.
5. Use `remove_poor_attrs=True` to reduce split-stat tracking for weak attributes when supported.
6. Mark categorical features through `nominal_attributes` instead of forcing a numeric splitter to treat categorical IDs as ordered values.
7. Choose splitters based on feature type and memory trade-offs; histogram/quantizer splitters can be more bounded than exhaustive statistics.
8. For forests, reduce `n_models`, cap base-tree depth/size, and choose metrics that match the task.
9. Remember that adaptive trees and forests can maintain alternate/background trees, warning detectors, and drift detectors, all of which increase state.

## Wrapper and ensemble method mismatches

Symptoms:

- `VotingClassifier` fails because a base model lacks probabilities.
- `StackingClassifier` behaves like a binary-only stack.
- An ensemble forwards a keyword unsupported by a base learner.
- A model-selection wrapper picks the first model forever.

Fix:

- Set `VotingClassifier(use_probabilities=False)` only when probability aggregation is not required and label voting is acceptable.
- Use an odd number of hard-voting classifiers to reduce ties.
- For stacking, use base classifiers and a compatible meta-classifier; verify target type before using multiclass tasks.
- For model selection, give enough observations and `budget` for candidates to separate.
- For bandit selectors, choose a policy and metric consistent with the exploration/exploitation trade-off.

## Cold-start predictions

Online models often predict before they have learned anything. Common cold-start outputs include `None`, `0`, an empty probability dictionary, a uniform probability dictionary, or a default first class depending on the estimator/wrapper. In progressive validation, update the metric only when the metric supports the cold-start value or after applying a task-approved fallback. Route loop-level policy to `streaming-evaluation`.
