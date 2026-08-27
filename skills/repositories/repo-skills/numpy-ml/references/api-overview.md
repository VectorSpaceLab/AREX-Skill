# API Overview

Use this reference to choose a module family before reading a focused
sub-skill. The root package imports the major module namespaces under
`numpy_ml`.

| Namespace | Main capability | Focused route |
| --- | --- | --- |
| `numpy_ml.linear_models` | linear, ridge, logistic, Bayesian regression, GLM, Gaussian NB | `supervised-and-tabular-models` |
| `numpy_ml.trees` | CART, random forest, gradient boosting | `supervised-and-tabular-models` |
| `numpy_ml.nonparametric` | KNN, kernel regression, GP regression | `supervised-and-tabular-models` |
| `numpy_ml.factorization` | regularized ALS and NMF | `supervised-and-tabular-models` |
| `numpy_ml.gmm`, `hmm`, `lda` | mixture, hidden-state, and topic models | `probabilistic-and-sequence-models` |
| `numpy_ml.ngram` | MLE, additive, and Good-Turing n-gram models | `probabilistic-and-sequence-models` |
| `numpy_ml.neural_nets` | activations, layers, modules, losses, optimizers, schedulers, toy models | `neural-network-components` |
| `numpy_ml.preprocessing` | general, NLP, DSP, interpolation, feature transforms | `preprocessing-and-utilities` |
| `numpy_ml.utils` | kernels, distances, graph/data structures, samplers, testing helpers | `preprocessing-and-utilities` |
| `numpy_ml.bandits` | bandit environments, policies, trainers | `bandits-and-reinforcement-learning` |
| `numpy_ml.rl_models` | Gym-backed agents, tile coding, environment utilities | `bandits-and-reinforcement-learning` |

The package also contains plotting helpers, but they are optional reference
demos rather than required runtime routes.
