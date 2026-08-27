# Mixtures and Classifiers API Reference

This reference covers `GeneralMixtureModel` and `BayesClassifier`. Both use a list of component distributions and expose posterior-assignment methods through the shared Bayes-style implementation.

## Constructor signatures verified from the package

```python
GeneralMixtureModel(
    distributions,
    priors=None,
    init='random',
    max_iter=1000,
    tol=0.1,
    inertia=0.0,
    frozen=False,
    random_state=None,
    check_data=True,
    verbose=False,
)

BayesClassifier(
    distributions,
    priors=None,
    inertia=0.0,
    frozen=False,
    check_data=True,
)
```

## Shared inference methods

| Method | Meaning |
| --- | --- |
| `probability(X, priors=None)` | Probability per example after marginalizing over components/classes. |
| `log_probability(X, priors=None)` | Numerically stable log probability per example. |
| `predict(X, priors=None)` | Most likely component/class index. |
| `predict_proba(X, priors=None)` | Posterior probability matrix with shape `(n, k)`. |
| `predict_log_proba(X, priors=None)` | Log posterior matrix with shape `(n, k)`. |

## `GeneralMixtureModel` workflow

Use `GeneralMixtureModel` for unsupervised component discovery.

```python
import torch
from pomegranate.distributions import Normal
from pomegranate.gmm import GeneralMixtureModel

X = torch.tensor([[0.0, 0.2], [0.3, 0.1], [5.0, 4.9], [5.2, 5.1]])
model = GeneralMixtureModel(
    [Normal(covariance_type="diag"), Normal(covariance_type="diag")],
    init="first-k",
    max_iter=20,
    random_state=0,
)
model.fit(X)
labels = model.predict(X)
posteriors = model.predict_proba(X)
```

Important details:

- Components can be heterogeneous pomegranate distributions, not only normals.
- Components may be initialized or uninitialized; uninitialized components are initialized with KMeans before EM.
- `priors` passed at construction are component priors; `priors` passed to inference/fitting are per-example assignment priors.
- `init` can be `'random'`, `'first-k'`, `'submodular-facility-location'`, or `'submodular-feature-based'`.

## `BayesClassifier` workflow

Use `BayesClassifier` for supervised class-conditional probabilistic classification.

```python
import torch
from pomegranate.distributions import Normal
from pomegranate.bayes_classifier import BayesClassifier

X = torch.tensor([[0.0, 0.2], [0.3, 0.1], [5.0, 4.9], [5.2, 5.1]])
y = torch.tensor([0, 0, 1, 1])
model = BayesClassifier([
    Normal(covariance_type="diag"),
    Normal(covariance_type="diag"),
])
model.fit(X, y)
pred = model.predict(X)
class_prob = model.predict_proba(X)
```

Important details:

- `y` must contain integer class labels in `0..k-1`, where `k` is the number of component distributions.
- Each component is fit to examples assigned to its class.
- The order of `distributions` defines class indices; keep a separate label-name map if class names matter.
- Components can themselves be richer probabilistic models when they implement the required distribution-like methods.

## Priors and hard labels

Per-example priors should have shape `(n, k)` and rows summing to 1. A one-hot row can force a component/class assignment for that example during prior-aware inference. Soft priors bias assignment estimates; they are not loss targets.

```python
priors = torch.tensor([
    [1.0, 0.0],
    [0.5, 0.5],
    [0.0, 1.0],
])
posteriors = model.predict_proba(X[:3], priors=priors)
```

## Chunked learning

For models with large inputs, use `summarize`/`from_summaries` just as with distributions. For a mixture model, pass compatible per-example priors to each `summarize` call if they are part of the training design.
