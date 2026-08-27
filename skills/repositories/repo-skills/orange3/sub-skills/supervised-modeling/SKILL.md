---
name: supervised-modeling
description: "Fit, predict with, score, and route supervised Orange3
  classification/regression learners, models, evaluation routines, and
  supervised model/evaluate widgets."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# supervised-modeling

Use this sub-skill when the Orange3 task is about supervised learning: choosing a classifier or regressor, fitting a learner to an `Orange.data.Table`, calling a fitted model for predictions, evaluating learners with `Orange.evaluation`, or wiring supervised model/evaluate widgets.

Do **not** use it for exploratory plotting, projections, clustering, unsupervised visualization, generic file/SQL loading, or widget-framework development except where those surfaces are needed to feed or evaluate supervised models.

## Fast routing

1. **Classify the target.** Use `data.domain.has_discrete_class` for classification and `data.domain.has_continuous_class` for regression. Most learners require exactly one target variable; if `len(data.domain.class_vars) > 1`, select one target before fitting.
2. **Choose the learner layer.**
   - `Orange.classification.*` for categorical targets.
   - `Orange.regression.*` for numeric targets.
   - `Orange.modelling.*` fitters such as `RandomForestLearner`, `TreeLearner`, `KNNLearner`, `SVMLearner`, `GBLearner`, and `ConstantLearner` when one object should dispatch to classification or regression based on the domain.
3. **Fit and predict.** `learner(data)` returns a model. `model(data)` returns predicted values; for classification use `model(data, ret=model.Probs)` or `model(data, ret=model.ValueProbs)` when probabilities are required.
4. **Evaluate.** Use `Orange.evaluation.CrossValidation`, `ShuffleSplit`, `TestOnTestData`, or `TestOnTrainingData` with a list of learners, then call score classes such as `CA`, `AUC`, `F1`, `RMSE`, and `R2` on the `Results` object.
5. **For widgets.** Model widgets emit a `Learner` and, when valid training data is supplied, a fitted `Model`. `Test and Score` consumes Data/Test Data/Learner(s)/Preprocessor and emits `Evaluation Results`; `Predictions` consumes Data plus fitted Models.

## Read next

- `references/api-reference.md` for learner/model/evaluation API contracts, return shapes, score families, fitters, and widget signal surfaces.
- `references/workflows.md` for compact classification, regression, dispatch, evaluation, and widget workflows.
- `references/troubleshooting.md` for target, sparse-data, fitting, domain-compatibility, empty-results, and memory failure modes.

## Guardrails

- Validate the target before modeling. Classification learners raise errors such as `Categorical class variable expected`; regression learners raise `Numeric target variable expected`; model widgets show equivalent data errors.
- Do not ask for probabilities from regression models: Orange raises `ValueError: cannot predict continuous distributions` for probability returns on continuous targets.
- Treat `Results.failed` as first-class evidence. Orange evaluation suppresses learner exceptions by default; rerun with `suppresses_exceptions=False` when debugging a failed learner.
- Use the bundled references above for runtime guidance; do not rely on hidden local files or absolute paths when helping a future agent.
