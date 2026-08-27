# Repository Provenance

Schema: `disco.repo-provenance.v1`

This generated operating skill targets the pomegranate repository state summarized below.

| Field | Value |
| --- | --- |
| Repository | `pomegranate` |
| Remote URL | `https://github.com/jmschrei/pomegranate.git` |
| Branch | `master` |
| Commit | `e9162731f4f109b7b17ecffde768734cacdb839b` |
| Exact tag | none detected |
| Package version | `1.1.2` |
| Package distribution name | `pomegranate` |
| Primary import package | `pomegranate` |
| Backend | PyTorch-backed v1.x rewrite |

## Working tree state

The checkout was dirty when this skill was generated because `skills/` contained untracked production artifacts. The source evidence files used for package behavior were the repository files listed below, not generated skill output.

## Evidence paths

- `README.md`: project purpose, v1.x rewrite notes, install guidance, GPU/mixed precision/missing-value/prior feature summaries, and legacy API differences.
- `setup.py`, `requirements.txt`, `docs/requirements.txt`: package name, version, dependencies, and install requirements.
- `pomegranate/`: source package for public model classes, constructor signatures, common utilities, and runtime validation behavior.
- `pomegranate/distributions/`: distribution classes and distribution API behavior.
- `pomegranate/gmm.py`, `pomegranate/bayes_classifier.py`, `pomegranate/_bayes.py`: mixture, classifier, posterior, and prior behavior.
- `pomegranate/bayesian_network.py`, `pomegranate/factor_graph.py`: graph-model structure, inference, and structure-learning behavior.
- `pomegranate/markov_chain.py`, `pomegranate/hmm/`: Markov chain and HMM sequence-model behavior.
- `pomegranate/kmeans.py`: KMeans clustering and initialization behavior.
- `docs/install.rst`, `docs/api.rst`, `docs/faq.rst`, `docs/whats_new.rst`, `docs/tutorials/`: public documentation and feature/tutorial coverage.
- `examples/Bayesian_Network_Monty_Hall.ipynb`: graph-model example adapted into a self-contained bundled smoke helper.
- `tests/`: behavior evidence and native verification candidates for distributions, mixtures, classifiers, graph models, sequence models, clustering, semi-supervised priors, and utilities.

## Refresh signals

Refresh this skill when any of these change:

- `setup.py`, `requirements.txt`, or the package version.
- Public constructors or method signatures in `pomegranate/`.
- Documentation around v1.x rewrite behavior, missing values, GPU, mixed precision, out-of-core learning, priors, or model availability.
- Tests that validate public distribution/model behavior or error handling.
