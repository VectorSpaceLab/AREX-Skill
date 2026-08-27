# pomegranate Model Catalog

Use this catalog to map a requested model or API name to the owning sub-skill. Pomegranate v1.x does not re-export all classes from top-level `pomegranate`; import from the submodules shown here.

## Distribution family

Read [../sub-skills/distributions/SKILL.md](../sub-skills/distributions/SKILL.md) for fitting, scoring, sampling, weighting, freezing, missing values, and composition of these classes.

| Class | Import | Primary use |
| --- | --- | --- |
| `Normal` | `from pomegranate.distributions import Normal` | Continuous multivariate normal with `covariance_type='full'`, `'diag'`, or `'sphere'`. |
| `Exponential` | `from pomegranate.distributions import Exponential` | Positive continuous data parameterized by `scales`. |
| `Gamma` | `from pomegranate.distributions import Gamma` | Positive continuous data with `shapes` and `rates`; fitted iteratively. |
| `LogNormal`, `HalfNormal`, `StudentT` | `from pomegranate.distributions import ...` | Heavy-tailed or constrained continuous distributions. |
| `Bernoulli` | `from pomegranate.distributions import Bernoulli` | Binary features. |
| `Categorical` | `from pomegranate.distributions import Categorical` | Discrete categorical features; used as graph marginals. |
| `ConditionalCategorical` | `from pomegranate.distributions import ConditionalCategorical` | Discrete conditional probability tables; used by Bayesian networks and Markov chains. |
| `JointCategorical` | `from pomegranate.distributions import JointCategorical` | Joint discrete probability tables; used as factor-graph factors. |
| `DiracDelta` | `from pomegranate.distributions import DiracDelta` | Degenerate mass at a fixed value. |
| `Poisson` | `from pomegranate.distributions import Poisson` | Count data parameterized by `lambdas`. |
| `Uniform` | `from pomegranate.distributions import Uniform` | Independent continuous intervals via `mins` and `maxs`. |
| `IndependentComponents` | `from pomegranate.distributions import IndependentComponents` | One distribution per feature for heterogeneous independent columns. |
| `ZeroInflated` | `from pomegranate.distributions import ZeroInflated` | Wrapper for excess-zero data; verify supported methods for the intended scoring/training path. |

## Mixtures and classifiers

Read [../sub-skills/mixtures-and-classifiers/SKILL.md](../sub-skills/mixtures-and-classifiers/SKILL.md).

| Class | Import | Primary use |
| --- | --- | --- |
| `GeneralMixtureModel` | `from pomegranate.gmm import GeneralMixtureModel` | Unsupervised mixture models over any pomegranate distributions; supports EM, priors, sampling, and posterior assignments. |
| `BayesClassifier` | `from pomegranate.bayes_classifier import BayesClassifier` | Supervised probabilistic classifier that fits one distribution or probabilistic model per class. |

## Graph models

Read [../sub-skills/graph-models/SKILL.md](../sub-skills/graph-models/SKILL.md).

| Class | Import | Primary use |
| --- | --- | --- |
| `BayesianNetwork` | `from pomegranate.bayesian_network import BayesianNetwork` | Directed categorical dependency models; supports manual structures, structure learning, likelihoods, and missing-value inference through factor graphs. |
| `FactorGraph` | `from pomegranate.factor_graph import FactorGraph` | Direct bipartite factor/marginal inference using `Categorical` and `JointCategorical` objects. |

## Sequence models

Read [../sub-skills/sequence-models/SKILL.md](../sub-skills/sequence-models/SKILL.md).

| Class | Import | Primary use |
| --- | --- | --- |
| `MarkovChain` | `from pomegranate.markov_chain import MarkovChain` | k-th order categorical sequence distribution. |
| `DenseHMM` | `from pomegranate.hmm import DenseHMM` | Hidden Markov model with dense transition matrix; good for dense state graphs. |
| `SparseHMM` | `from pomegranate.hmm import SparseHMM` | Hidden Markov model with explicit sparse edges; good for sparse state graphs. |

## Clustering

Read [../sub-skills/clustering/SKILL.md](../sub-skills/clustering/SKILL.md).

| Class | Import | Primary use |
| --- | --- | --- |
| `KMeans` | `from pomegranate.kmeans import KMeans` | Standalone clustering and initialization helper for mixture/HMM training. |

## Cross-cutting support

Read [feature-guide.md](feature-guide.md) for `torch.masked.MaskedTensor`, GPU/CUDA, mixed precision, out-of-core learning via `summarize`/`from_summaries`, prior probabilities, serialization, and `torch.compile` notes.
