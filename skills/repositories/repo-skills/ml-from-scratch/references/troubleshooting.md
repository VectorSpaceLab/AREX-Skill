# Package-wide troubleshooting

Use this reference for install, import, dependency, plotting, and package-wide compatibility failures. Use sub-skill troubleshooting for estimator-specific shape, label, clustering, neural-network, or DQN model-builder failures.

## Install and import checks

Run from this skill root after installing `mlfromscratch` in the active user environment:

```bash
python scripts/check_install.py
python scripts/check_install.py --include-rl
```

If the root check passes, continue with the focused sub-skill smoke script that matches the user's workflow.

## Dependency matrix

| Symptom | Likely cause | Action |
| --- | --- | --- |
| Install fails with a message that the `sklearn` PyPI package is deprecated. | Legacy metadata names the deprecated shim package instead of the real `scikit-learn` distribution. | Install `scikit-learn` explicitly. If a legacy install path requires the shim, allow it only as a compatibility step, then verify `import sklearn`. |
| `ModuleNotFoundError: No module named 'sklearn'` after installing the legacy `sklearn` shim. | The shim installed metadata but not a working scikit-learn import in the environment. | Install `scikit-learn`; rerun `python scripts/check_install.py`. |
| Importing `mlfromscratch.supervised_learning` fails with `No module named 'cvxopt'`. | `SupportVectorMachine` imports `cvxopt`, and the supervised package exports SVM during package import. | Install `cvxopt` if supervised imports or SVM are needed. If only other subpackages are needed, import them directly and avoid package-level supervised import until dependencies are fixed. |
| Missing `terminaltables` or `progressbar`. | Deep-learning summaries and training loops depend on `terminaltables` and `progressbar33`. | Install `terminaltables` and `progressbar33`; then rerun the relevant smoke. |
| Matplotlib import or display failure. | Plotting libraries selected an interactive backend or the session has no display. | Set `MPLBACKEND=Agg` before importing plotting modules. Prefer bundled smoke scripts that avoid plots. |
| `gym` import warning says Gym is unmaintained. | Upstream Gym deprecation notice. | Warning is expected for this package. Treat as context unless a real exception follows. |
| `module 'numpy' has no attribute 'bool8'` in a Gym/DQN path. | Older Gym passive checker with NumPy 2.x. | Prefer `gym==0.25.x` plus NumPy `<2` for this package's DQN workflow, or use a local process-only alias/wrapper as shown in `sub-skills/reinforcement-learning/references/troubleshooting.md`. |

## Installation baseline

A practical CPU environment contains:

```bash
python -m pip install mlfromscratch
python -m pip install scikit-learn cvxopt progressbar33 terminaltables matplotlib pandas scipy
python -m pip install "numpy<2" "gym==0.25.2"
```

For an editable checkout, install the package after dependency pins. If a resolver upgrades NumPy to 2.x, retest the DQN path before claiming reinforcement-learning compatibility.

## Package import strategy

Import only the package family needed by the task:

```python
from mlfromscratch.supervised_learning import LogisticRegression
from mlfromscratch.unsupervised_learning import KMeans
from mlfromscratch.deep_learning import NeuralNetwork
from mlfromscratch.reinforcement_learning import DeepQNetwork
```

If one family import fails, isolate it rather than assuming all families are broken. For example, missing `cvxopt` can break supervised imports while unsupervised and deep-learning imports still work.

## Headless plotting and slow examples

Many educational demonstrations plot or run for many epochs. In automated or server-side work:

1. Set `MPLBACKEND=Agg` before any plotting imports.
2. Avoid `plt.show()`.
3. Use one epoch, small sample counts, small hidden units/filters, and bounded iterations.
4. Use the bundled smoke helpers rather than long demonstrations.
5. Write plots only to a caller-approved artifact path when the user explicitly asks for images.

## Current-runtime compatibility notes

- Tree-family supervised models may hit current NumPy shape strictness through the package's split helper. Use `sub-skills/supervised-learning/references/troubleshooting.md` for diagnosis and workarounds.
- Gym 0.26+ and Gymnasium changed reset/step outputs. Use `sub-skills/reinforcement-learning/` for wrappers and no-render checks.
- The package does not provide production-grade device backends or GPU-specific code paths. CPU import and smoke checks are the expected baseline.
- The package is educational; failing benchmark expectations are not necessarily API failures. Validate imports, shapes, target encodings, and finite losses before tuning accuracy.

## Escalation path

1. Run `scripts/check_install.py --include-rl`.
2. If import/dependency failures remain, fix the dependency named in the error.
3. If root imports pass but a workflow fails, run the nearest sub-skill smoke.
4. If the smoke passes but user data fails, apply the sub-skill troubleshooting checklist for shapes, labels, scaling, or compatibility.
5. If both the bundled smoke and user data fail after dependency fixes, treat it as a package/runtime compatibility issue and document the exact failing constructor, input shapes, dependency versions, and traceback.
