---
name: fairlearn
description: "Use Fairlearn to assess group fairness, compute disparity metrics,
  visualize subgroup performance, and mitigate unfairness with preprocessing,
  reductions, postprocessing, or adversarial learning."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# Fairlearn

Use this repo skill when a task names `fairlearn`, asks for the Fairlearn Python package, or uses Fairlearn vocabulary such as `MetricFrame`, `sensitive_features`, demographic parity, equalized odds, `CorrelationRemover`, `ExponentiatedGradient`, `GridSearch`, `ThresholdOptimizer`, `AdversarialFairnessClassifier`, or Fairlearn dataset fetchers.

Fairlearn is API-first. This checkout does not define a Fairlearn-specific command-line interface, so route future agents to Python APIs, bundled references, and the smoke scripts in this skill.

## Install and quick verification

For normal package use:

```bash
python -m pip install fairlearn
```

Add optional plotting and adversarial-learning dependencies only when the workflow needs them:

```bash
python -m pip install matplotlib        # group plots and threshold-optimizer plots
python -m pip install torch             # PyTorch adversarial backend
# TensorFlow is an alternative adversarial backend, but was not verified in this skill run.
```

From this skill directory, run the bundled root check when you need a safe import and optional-backend smoke test:

```bash
python scripts/check_install.py --include-optional
```

Read [`references/installation.md`](references/installation.md) for version and optional dependency details, [`references/troubleshooting.md`](references/troubleshooting.md) for cross-cutting failures, and [`references/repo-provenance.md`](references/repo-provenance.md) before deciding whether this skill is stale for a newer Fairlearn checkout.

## Route map

| Task signal | Read this sub-skill | Why |
| --- | --- | --- |
| Group metrics, `MetricFrame`, `selection_rate`, demographic parity/equalized odds metrics, intersections, bootstrapped confidence intervals, model comparison plots, ROC-by-group plots | [`sub-skills/assessment/SKILL.md`](sub-skills/assessment/SKILL.md) | Assessment owns Fairlearn metrics, grouped outputs, CIs, and plotting helpers. |
| Remove linear correlation with sensitive columns, fair representation learning, `CorrelationRemover`, `PrototypeRepresentationLearner`, preprocessing before a downstream estimator | [`sub-skills/preprocessing/SKILL.md`](sub-skills/preprocessing/SKILL.md) | Preprocessing owns transformations applied before model training. |
| Fairness-constrained training with sklearn-compatible estimators, `ExponentiatedGradient`, `GridSearch`, `DemographicParity`, `EqualizedOdds`, `BoundedGroupLoss`, `sample_weight_name` | [`sub-skills/reductions/SKILL.md`](sub-skills/reductions/SKILL.md) | Reductions owns algorithms that reduce fairness constraints to weighted supervised-learning problems. |
| Adjust a trained predictor with group-specific thresholds, `ThresholdOptimizer`, `plot_threshold_optimizer`, `prefit`, `predict_method`, post-fit parity constraints | [`sub-skills/postprocessing/SKILL.md`](sub-skills/postprocessing/SKILL.md) | Postprocessing owns prediction-time threshold/interpolation mitigation. |
| Neural adversarial fairness, PyTorch or TensorFlow backends, callbacks, CUDA, `AdversarialFairnessClassifier`, `AdversarialFairnessRegressor` | [`sub-skills/adversarial/SKILL.md`](sub-skills/adversarial/SKILL.md) | Adversarial workflows have backend-specific model, optimizer, and training pitfalls. |
| Built-in datasets, `fetch_adult`, `fetch_acs_income`, `fetch_boston`, `return_X_y`, `as_frame`, `data_home`, dataset fairness caveats | [`sub-skills/datasets/SKILL.md`](sub-skills/datasets/SKILL.md) | Dataset loaders have network/cache behavior and dataset-specific schemas. |
| Installing, checking versions, optional extras, missing matplotlib/torch/tensorflow, `show_versions`, import/runtime diagnostics | [`sub-skills/installation/SKILL.md`](sub-skills/installation/SKILL.md) | Installation owns environment and dependency recovery paths. |

## Operating rules

- Treat Fairlearn as a sociotechnical fairness toolkit, not an automated fairness oracle. Metric choices and mitigation goals must be tied to the user's problem context.
- Keep row alignment explicit. `X`, `y_true`/`y`, predictions, and `sensitive_features` must describe the same samples in the same order.
- Use `sensitive_features` for group definitions even when those columns are also present in `X`. Do not assume ignoring sensitive features is enough to assess or mitigate unfairness.
- Start with assessment before mitigation unless the user already gives a constrained mitigation algorithm and metric target.
- Prefer tiny synthetic smoke checks or cached data before networked dataset downloads. Fairlearn dataset fetchers use OpenML-style downloads and cache under a data home.
- Make optional dependencies explicit. Plotting requires matplotlib; adversarial mitigation requires either PyTorch or TensorFlow. The PyTorch CPU path and optional CUDA acceleration were verified for this skill; TensorFlow was only documented as an alternative.
- The generated references and scripts are self-contained. Do not instruct future agents to open this repo's original docs, tests, examples, or source scripts for normal operation.

## Shared runtime files

- [`references/fairness-framing.md`](references/fairness-framing.md) summarizes Fairlearn's group-fairness framing, sensitive features, parity constraints, disparity metrics, and limits.
- [`references/installation.md`](references/installation.md) covers install commands, optional dependencies, import checks, and version inspection.
- [`references/troubleshooting.md`](references/troubleshooting.md) covers package-wide import, plotting, backend, data-shape, and stale-version failures.
- [`references/repo-provenance.md`](references/repo-provenance.md) records source revision, package version, evidence paths, backend verification, and refresh signals.
- [`references/repo-routing-metadata.json`](references/repo-routing-metadata.json) is structured metadata consumed by DisCo's managed repo-skills router import transaction.
- [`scripts/check_install.py`](scripts/check_install.py) validates the installed Fairlearn package, stable public submodules, and optional plotting/adversarial dependencies.

## Good first branch decisions

- If the prompt says "is my model fair?", "compare groups", or names a metric, start with assessment.
- If it asks to transform features before training, start with preprocessing.
- If it asks to train a fair model from scratch with a sklearn estimator, start with reductions.
- If it already has a fitted predictor or score function and wants fair thresholds, start with postprocessing.
- If it names neural networks, PyTorch, TensorFlow, callbacks, or CUDA, start with adversarial.
- If it asks for Adult, ACSIncome, Boston, diabetes, bank, or credit-card sample data, start with datasets.
- If imports, missing extras, or version questions block the task, start with installation and root troubleshooting.
