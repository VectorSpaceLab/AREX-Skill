# AIF360 Cross-Cutting Troubleshooting

## Base import succeeds but optional warnings appear

AIF360 imports some optional modules lazily or with warning messages. Missing
TensorFlow, fairlearn, torch, cvxpy, BlackBoxAuditing, POT, FACTS, rpy2, or
inFairness warnings usually mean an optional workflow is unavailable, not that
base datasets and metrics are broken.

Recovery:

1. Identify the selected workflow.
2. Install only its named extra from [install-data-and-optional-deps.md](install-data-and-optional-deps.md).
3. Run a tiny workflow-specific smoke before using real data.
4. If the user does not need the optional workflow, proceed with base metrics or
   route to a base-supported alternative.

## scikit-learn dependency conflicts

AIF360 0.6.1 constrains scikit-learn to `<1.6`. If a target environment already
has a newer scikit-learn, install AIF360 in an isolated environment or resolve a
compatible version before debugging AIF360 behavior.

## Raw dataset files are missing

AIF360 standard dataset wrappers may expect raw public benchmark files or fetch
from public sources. Missing raw files are expected in a fresh package install.

Recovery:

- Use synthetic data for API demonstrations and no-network smokes.
- Ask for approval before downloading benchmark data.
- Store raw data/cache paths in the user's project context, not in this skill.
- For MEPS, expect data terms and extra preparation steps.

## Legacy and sklearn APIs are mixed

Symptoms:

- Passing `BinaryLabelDataset` objects to `aif360.sklearn.metrics`.
- Passing pandas `Series` directly to `ClassificationMetric`.
- Protected attributes disappear after an sklearn pipeline step.

Recovery:

- Use legacy sub-skills for `BinaryLabelDataset` and `aif360.algorithms`.
- Use the sklearn sub-skill for pandas DataFrame/Series workflows.
- Convert deliberately and validate row order, labels, protected attributes, and
  weights after conversion.

## Fairness metrics look wrong

Likely causes:

- Privileged/unprivileged groups are reversed.
- Favorable label or `pos_label` does not match the policy definition.
- A group has zero positives/negatives, causing undefined ratios.
- Predictions are not aligned to the true dataset rows.

Recovery:

1. Print group counts and label counts by protected group.
2. Check `favorable_label`, `unfavorable_label`, `pos_label`, and `priv_group`.
3. Rebuild prediction datasets by copying the true dataset or preserving pandas
   indexes.
4. Report undefined metrics explicitly instead of converting them to zero.

## Postprocessing or detector workflows need scores

Some postprocessors and MDSS modes need probabilities/scores, not only hard
labels. If the model has no `predict_proba` or decision score:

- Choose a classifier that exposes calibrated probabilities.
- Use a metric route that only needs hard labels.
- Do not fabricate probability columns.

## R, notebooks, and MLOps samples are outside the base path

The Python package is the verified primary scope. R wrapper, notebook demos,
Kubeflow, and NiFi samples require additional runtimes, raw data, or platform
services. Read [r-and-mlops-notes.md](r-and-mlops-notes.md) and verify those
environments explicitly before claiming execution support.

## Safe diagnostics

Run the root base smoke:

```bash
python scripts/check_aif360_env.py --json
```

Then route to a sub-skill-specific smoke if needed:

```bash
python sub-skills/datasets-and-metrics/scripts/metric_report_smoke.py --pretty
python sub-skills/mitigation-algorithms/scripts/reweighing_smoke.py --json
python sub-skills/sklearn-interface/scripts/sklearn_metric_smoke.py --compact
python sub-skills/detectors-and-explainers/scripts/mdss_smoke.py --json
python sub-skills/detectors-and-explainers/scripts/explainer_smoke.py --json
```
