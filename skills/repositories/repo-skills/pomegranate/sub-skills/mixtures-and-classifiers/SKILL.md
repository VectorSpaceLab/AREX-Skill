---
name: mixtures-and-classifiers
description: "Guides pomegranate GeneralMixtureModel and BayesClassifier
  workflows, including heterogeneous mixture fitting, supervised probabilistic
  classification, posterior probabilities, priors, EM settings, and component
  distributions."
disable-model-invocation: true
metadata:
  disco-role: operating
license: MIT
---

# mixtures-and-classifiers

## Use this sub-skill when

Use this sub-skill for unsupervised mixture modeling with `GeneralMixtureModel` and supervised probabilistic classification with `BayesClassifier`. These models are useful when a task asks for Gaussian mixtures, heterogeneous mixtures, EM fitting, class-conditional distributions, posterior component/class probabilities, prior-weighted inference, or semi-supervised-style hard priors.

## Start here

Typical imports:

```python
from pomegranate.distributions import Normal, Exponential
from pomegranate.gmm import GeneralMixtureModel
from pomegranate.bayes_classifier import BayesClassifier
```

Read [references/api-reference.md](references/api-reference.md) for constructor signatures, fitting recipes, and priors. Run [scripts/smoke_mixtures_classifiers.py](scripts/smoke_mixtures_classifiers.py) after installation for a tiny check that both model families fit and predict.

## Core workflow

1. **Build component distributions.** Create one pomegranate distribution or probabilistic model per component/class. Use [../distributions/SKILL.md](../distributions/SKILL.md) if component selection is the hard part.
2. **Choose unsupervised vs supervised.** Use `GeneralMixtureModel(distributions, ...)` when labels are unknown; use `BayesClassifier(distributions, ...)` when class labels `y` are provided.
3. **Fit on 2D data.** Mixtures and classifiers expect feature matrices shaped `(n, d)`.
4. **Inspect posterior assignments.** Use `predict`, `predict_proba`, or `predict_log_proba` for component/class assignment probabilities.
5. **Use priors deliberately.** Priors must be probabilities with valid shape and row sums. Read [../../references/feature-guide.md](../../references/feature-guide.md) before using hard labels or soft prior weights.
6. **Tune EM only when necessary.** `max_iter`, `tol`, `init`, `random_state`, and `verbose` affect mixture fitting and initialization.

## Route elsewhere when

- The task is only about selecting or fitting a base distribution: read [../distributions/SKILL.md](../distributions/SKILL.md).
- The model is a Bayesian network or factor graph: read [../graph-models/SKILL.md](../graph-models/SKILL.md).
- The model is a Markov chain or HMM over sequences: read [../sequence-models/SKILL.md](../sequence-models/SKILL.md).
- The task is KMeans clustering or centroid initialization directly: read [../clustering/SKILL.md](../clustering/SKILL.md).

## Guardrails

- `BayesClassifier.fit` requires `y`; `GeneralMixtureModel.fit` does not.
- The order of distributions defines component/class indices, so record the mapping before interpreting predictions.
- If uninitialized component distributions are supplied to `GeneralMixtureModel`, pomegranate initializes them with KMeans before EM.
- Validate a small example before disabling `check_data` or moving to mixed precision/compiled execution.
- Read [references/troubleshooting.md](references/troubleshooting.md) when priors, labels, component initialization, or EM convergence fails.
