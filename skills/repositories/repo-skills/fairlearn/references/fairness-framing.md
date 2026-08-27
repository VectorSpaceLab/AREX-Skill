# Fairlearn fairness framing

Fairlearn is designed for group-fairness assessment and unfairness mitigation in Python. It gives future agents implementation tools, but it does not decide what fairness means in a sociotechnical context.

## What Fairlearn can and cannot answer

Fairlearn is strongest when the user has a supervised-learning problem and wants to:

- compute metrics overall and by group;
- compare disparity metrics such as demographic parity difference/ratio or equalized odds difference/ratio;
- visualize performance and selection behavior across sensitive-feature groups;
- apply a mitigation algorithm with a stated parity constraint; or
- use educational datasets with known fairness concerns.

Fairlearn cannot, by itself, determine whether a system is socially fair, legally compliant, or ethically acceptable. Always connect metric choices to the problem domain, harms, stakeholder context, data collection process, deployment setting, and monitoring plan.

## Harms and scope

Fairlearn's documentation frames unfairness in terms of harms rather than intent or the generic word "bias". The package is most applicable to:

- **Allocation harms**: a system extends or withholds opportunities, resources, or information, such as hiring, admissions, lending, or benefit allocation.
- **Quality-of-service harms**: a system works better for some groups than others, such as differing error rates in recognition, search, recommendations, or diagnosis.

Other harms such as stereotyping, erasure, or broader institutional impacts may still matter, but Fairlearn's API surface mainly supports measurable group-metric analysis and model mitigation.

## Group fairness and sensitive features

Fairlearn's API expects group definitions through `sensitive_features`.

- `sensitive_features` can be a vector for one feature or a matrix/DataFrame for multiple features.
- Assessment can handle more than two groups and intersections of multiple sensitive features.
- Mitigation algorithms also support non-binary and multiple sensitive features, but some algorithms have data-layout and constraint-specific limits that the owning sub-skill documents.
- A feature can be sensitive even when it is not legally protected in the user's jurisdiction. Conversely, legal protected-class analysis requires human/legal review beyond the package.

Do not assume that dropping sensitive columns from `X` removes unfairness. Other columns can encode the same information, and dropping the column can make assessment harder.

## Common parity concepts

Fairlearn exposes metric helpers and mitigation constraints around common group-fairness definitions:

- **Demographic parity / statistical parity**: predictions or selections should be statistically independent of the sensitive feature. This is often used for allocation-harm analysis.
- **Equalized odds**: predictions should be conditionally independent of the sensitive feature given the true label. This is often used when both false positives and false negatives matter.
- **Equal opportunity**: a relaxed version of equalized odds focusing on positive labels.
- **Bounded group loss**: group-conditioned expected loss is constrained, commonly useful for quality-of-service or regression-style workflows.

Metric functions often report either a **difference** (`max - min`) or a **ratio** (`min / max`) across groups. A smaller difference or ratio closer to 1 can indicate less measured disparity, but the interpretation depends on the metric, harm model, and data quality.

## Assessment before mitigation

A robust Fairlearn workflow usually follows this order:

1. Define the decision problem, target, sensitive features, and likely harms.
2. Train or obtain a baseline predictor.
3. Use assessment metrics and `MetricFrame` to inspect overall and group performance.
4. Choose a mitigation family only after the relevant constraint and trade-off are clear.
5. Validate both model utility and disparity after mitigation.
6. Document limitations, monitor deployment drift, and avoid claiming the model is globally fair.

Use the root route map to choose the mitigation family:

- preprocessing when transforming features before training;
- reductions when retraining with fairness constraints;
- postprocessing when adjusting a trained predictor's scores or labels;
- adversarial when using neural networks and an adversary to reduce sensitive-feature predictability.

## Vocabulary guidance for future agents

- Prefer "fairness assessment", "unfairness mitigation", "disparity", and "sensitive features" over vague "debias this model" phrasing.
- Ask for or infer the metric target, sensitive features, prediction task, and utility metric before choosing a mitigation algorithm.
- Report both subgroup metrics and overall metrics. A mitigation method can reduce a disparity metric while changing accuracy or other utility metrics.
- When a built-in dataset raises a fairness warning, keep the warning visible instead of suppressing it silently.
