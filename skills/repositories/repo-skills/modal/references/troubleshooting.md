# modAL troubleshooting

## When to read

Read this when installation, imports, dependency resolution, optional integrations, or cross-cutting runtime behavior fails before a workflow-specific sub-skill can be used.

## Install and import problems

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError: No module named 'modAL'` after installing `modal` | The unrelated lowercase `modal` distribution was installed instead of `modAL-python`. | Install the correct distribution: `python -m pip install modAL-python`, then check `import modAL`. |
| `AttributeError: module 'numpy' has no attribute 'float'` while importing `modAL.expected_error` | The `0.4.2` code uses `np.float`, removed in NumPy 1.24+. | Use a compatible NumPy for this release, for example `numpy==1.23.5`, or refresh/update the package code if using a newer fork. |
| `TypeError: check_X_y() got an unexpected keyword argument 'force_all_finite'` during `teach` or `fit` | A newer scikit-learn removed or changed the `force_all_finite` argument used by modAL. | Use a compatible scikit-learn such as `scikit-learn==1.3.2` for this snapshot, or patch/refresh the source for newer scikit-learn. |
| `ModuleNotFoundError: No module named 'pkg_resources'` from skorch | Old `skorch==0.9.0` imports `pkg_resources`, which may be absent with very new setuptools. | Install a setuptools release that still provides `pkg_resources`, for example `setuptools<81`. |
| `ImportError` from `modAL.dropout`, `torch`, or `skorch` | Optional deep-learning stack is missing. | Classical modAL workflows do not need dropout. If the task needs MC dropout, install PyTorch and skorch for the selected CPU/GPU backend, then run the deep sub-skill helper. |
| Keras or TensorFlow example import fails | Keras/TensorFlow examples are optional legacy examples, not minimum dependencies. | Install and smoke-test a compatible Keras/TensorFlow stack only when the task explicitly requires it; avoid dataset downloads unless approved. |

Known compatible dependency set for the `0.4.2` snapshot used during skill construction: Python 3.11, `numpy==1.23.5`, `scipy==1.10.1`, `pandas==1.5.3`, `scikit-learn==1.3.2`, `setuptools<81`, `skorch==0.9.0`, and CPU `torch` for optional `modAL.dropout` inspection. Treat this as a troubleshooting baseline, not as a universal pin set for all future forks.

## Environment smoke checks

Run the bundled root smoke from any current directory after installing modAL:

```bash
python path/to/modal/scripts/modal_environment_smoke.py
```

If the optional PyTorch/skorch dropout stack should be available:

```bash
python path/to/modal/scripts/modal_environment_smoke.py --include-optional-deep
python path/to/modal/sub-skills/deep-and-optional-integrations/scripts/dropout_inspection.py --list-layers
```

A passing root smoke proves only small CPU workflows. It does not prove a user's estimator, labeling oracle, Keras/TensorFlow installation, CUDA runtime, or large training loop.

## Workflow routing after install succeeds

- Shape, `teach`, `fit`, `query`, `return_metrics`, `on_transformed`, and committee voting issues: [../sub-skills/learners-and-committees/references/troubleshooting.md](../sub-skills/learners-and-committees/references/troubleshooting.md)
- Strategy, `predict_proba`, `NotFittedError`, batch cost, and multilabel selection issues: [../sub-skills/query-strategies/references/troubleshooting.md](../sub-skills/query-strategies/references/troubleshooting.md)
- BayesianOptimizer, acquisition score, `predict(return_std=True)`, and `get_max()` issues: [../sub-skills/bayesian-optimization/references/troubleshooting.md](../sub-skills/bayesian-optimization/references/troubleshooting.md)
- DeepActiveLearner, skorch, MC dropout, bad dropout layer index, and optional backend issues: [../sub-skills/deep-and-optional-integrations/references/troubleshooting.md](../sub-skills/deep-and-optional-integrations/references/troubleshooting.md)

## GPU boundary

modAL's classical scikit-learn workflows are CPU-friendly. A visible GPU does not mean modAL requires CUDA. Only claim CUDA behavior after the user's actual PyTorch/TensorFlow runtime reports a working GPU and the task-specific estimator runs a tiny device smoke. For MC dropout, CPU tensors are enough to verify the API contract; CUDA is only an accelerator choice for the user's model.
