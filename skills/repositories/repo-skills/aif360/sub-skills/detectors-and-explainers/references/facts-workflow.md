# FACTS Counterfactual Subgroup Workflow

## When to read

Read this when the user asks for FACTS, fairness-aware counterfactuals,
subgroup recourse, action cost disparity, or recourse reports.

## Dependency status

FACTS is an optional AIF360 workflow. The base construction environment did not
install the `FACTS` extra, and imports can warn that FACTS is unavailable.
Install and verify the extra before claiming FACTS execution works:

```bash
pip install 'aif360[FACTS]'
```

The extra includes dependencies such as `mlxtend`, `colorama`, and `tqdm`.

## Main surfaces

- `aif360.sklearn.detectors.FACTS_bias_scan(...)` is a wrapper that runs the
  FACTS workflow from start to finish.
- `aif360.sklearn.detectors.FACTS` is an estimator-style class for more control,
  including caching intermediate rule mining results.

The wrapper expects a pandas feature DataFrame, a fitted classifier with
`predict(X)`, the protected-attribute column name, and a FACTS metric.

## FACTS metrics

The wrapper documents these metric names:

- `equal-effectiveness`
- `equal-choice-for-recourse`
- `equal-effectiveness-within-budget`
- `equal-cost-of-effectiveness`
- `equal-mean-recourse`
- `fair-tradeoff`

Choose the metric based on the policy question: equal recourse availability,
equal cost, equal effectiveness, or a trade-off.

## Typical workflow

1. Prepare a pandas DataFrame `X` with one row per instance and one column per
   feature.
2. Fit a binary sklearn classifier with a `predict(X)` method.
3. Select `prot_attr` as the protected attribute column.
4. Decide categorical features and which features are allowed or forbidden to
   change.
5. Choose the FACTS metric and support threshold.
6. Run FACTS and inspect subgroup recourse/action-cost output.

## Safety guidance

- Do not run FACTS in a no-network/no-extra environment.
- Validate categorical feature types; automatic detection is convenient but not
  always policy-safe.
- Set `feats_allowed_to_change` or `feats_not_allowed_to_change` to avoid
  recommending changes to immutable attributes.
- Treat recourse reports as decision-support artifacts, not direct policy
  prescriptions.

## Route away

If the user only needs subgroup bias by outcome/prediction residuals, use MDSS
instead. If the user only needs metric values, use the datasets/metrics or
sklearn-interface sub-skill.
