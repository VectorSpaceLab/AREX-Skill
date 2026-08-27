# Cross-Cutting Troubleshooting

Use this page for package-level failures before moving to sub-skill-specific troubleshooting.

## Import or installation failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: No module named 'pomegranate'` | Package is not installed in the active Python. | Install with `python -m pip install pomegranate` or, from a local checkout, `python -m pip install -e .`; then run `python scripts/check_env.py`. |
| `ImportError` for `torch`, `numpy`, `scipy`, `sklearn`, `apricot`, or `networkx` | Core dependency is missing or installed in a different environment. | Run `python -m pip check`, reinstall pomegranate in the target environment, and ensure the command uses the intended Python. |
| Top-level imports such as `from pomegranate import Normal` fail | v1.x exposes most classes from submodules, not from top-level `pomegranate`. | Import from `pomegranate.distributions`, `pomegranate.gmm`, `pomegranate.hmm`, `pomegranate.bayesian_network`, etc.; see [model-catalog.md](model-catalog.md). |
| Old code uses `NormalDistribution`, `HiddenMarkovModel`, `State`, `Node`, `bake`, `NaiveBayes`, or `MarkovNetwork` | Pre-v1 Cython-era API or old tutorial code. | Rewrite for v1.x: use `Normal`, `GeneralMixtureModel`, `DenseHMM`/`SparseHMM`, direct distribution objects, and no bake step. `NaiveBayes` and `MarkovNetwork` are not current v1.x models. |

## Shape, dtype, and value checks

Pomegranate validates many inputs unless `check_data=False` is set. Common issues:

- Use 2D data `(n, d)` for distributions, mixtures, classifiers, KMeans, Bayesian networks, and factor graphs.
- Use 3D data `(n, length, d)` or supported variable-length sequence lists for HMMs and Markov chains.
- Use integer tensors for categorical graph and sequence variables.
- Probability vectors/matrices must be nonnegative and sum to 1 where required.
- `sample_weight` must match the model-specific accepted shape and must be nonnegative.

If validation fails, keep `check_data=True` while reducing the input to a tiny example. Only disable checks after a tested path works.

## Missing values and masked tensors

`torch.masked.MaskedTensor` is the supported missing-value representation. Remember that `mask=True` means observed. If a model unexpectedly ignores, propagates, or rejects missing values:

1. Confirm the input is a `torch.masked.MaskedTensor`, not only a tensor with `NaN` values.
2. Confirm the model family supports missing values for the exact distribution and covariance type.
3. Avoid Bernoulli, categorical, full-covariance `Normal`, and `Uniform` missing-value claims unless the exact path is locally verified.
4. For Bayesian networks and factor graphs, use masked tensors for inference over discrete missing values; observed values must remain valid category indices.

## CUDA, devices, and mixed precision

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Expected all tensors to be on the same device` | Model parameters and input tensors are split between CPU and GPU. | Move both model and data: `model = model.cuda(); X = X.cuda()`, or keep both on CPU. |
| `torch.cuda.is_available()` is false | CPU-only torch install or unavailable GPU runtime. | Use CPU guidance or install a CUDA-capable PyTorch build that matches the host driver. |
| Mixed precision produces unstable values | Probabilistic linear algebra or categorical operations may not be robust in low precision. | Validate in full precision first, then wrap only safe sections in autocast. |
| `torch.compile` fails with opaque graph errors | Data validation or nested composite methods are not compile-friendly. | Start with leaf distribution methods and set `check_data=False` only after manual validation. |
| `torch.load` raises `Weights only load failed` or says a pomegranate class is not an allowed global | Newer PyTorch defaults to safer `weights_only=True` loading for full-object pickle files. | For trusted pomegranate model files only, call `torch.load(path, weights_only=False)` or allowlist the exact class with `torch.serialization.safe_globals`; do not disable safe loading for untrusted files. |

## No CLI entry points

This package is API-first. If a user asks for a command-line workflow, provide a small Python script using the relevant sub-skill rather than searching for a package CLI.

## Where to go next

- Distribution-specific failures: [../sub-skills/distributions/references/troubleshooting.md](../sub-skills/distributions/references/troubleshooting.md)
- Mixture/classifier failures: [../sub-skills/mixtures-and-classifiers/references/troubleshooting.md](../sub-skills/mixtures-and-classifiers/references/troubleshooting.md)
- Graph-model failures: [../sub-skills/graph-models/references/troubleshooting.md](../sub-skills/graph-models/references/troubleshooting.md)
- Sequence-model failures: [../sub-skills/sequence-models/references/troubleshooting.md](../sub-skills/sequence-models/references/troubleshooting.md)
- KMeans failures: [../sub-skills/clustering/references/troubleshooting.md](../sub-skills/clustering/references/troubleshooting.md)
