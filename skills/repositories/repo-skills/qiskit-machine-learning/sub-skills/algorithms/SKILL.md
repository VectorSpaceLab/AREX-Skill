---
name: algorithms
description: "Train, evaluate, persist, and troubleshoot Qiskit Machine Learning
  classifiers, regressors, and quantum Bayesian inference with public
  scikit-learn-like APIs."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Algorithms

Use this route for end-to-end model work: choose a classifier or regressor,
prepare compatible `X`/`y`, attach a primitive and optimizer, call `fit`,
`predict`, and `score`, observe callbacks, continue with warm starts, persist a
model, or run `QBayesian` inference. Read the focused references progressively:

- [api-reference.md](references/api-reference.md) for public constructors,
  shapes, outputs, and loss choices.
- [workflows.md](references/workflows.md) for classification, regression,
  kernel-model, Bayesian, primitive, callback, and warm-start procedures.
- [model-persistence.md](references/model-persistence.md) before saving,
  loading, or changing a primitive after loading.
- [troubleshooting.md](references/troubleshooting.md) when validation,
  primitive, layout, shape, or convergence errors occur.
- [`scripts/vqc_smoke.py`](scripts/vqc_smoke.py) for a tiny deterministic
  VQC/ad-hoc-data check that is safe to invoke from any current directory.

## Scope and routing

- **Own here:** `VQC`, `VQR`, `NeuralNetworkClassifier`,
  `NeuralNetworkRegressor`, `QSVC`, `QSVR`, `PegasosQSVC`, `QBayesian`,
  `TrainableModel`, objective/loss selection, `fit`/`predict`/`score`,
  callbacks, warm starts, and dill persistence.
- **Route raw QNN construction, parameter ordering, forward/backward, or
  gradient design** to `qnn-gradients`.
- **Route direct fidelity/statevector-kernel construction, matrix policy,
  trainable kernels, and kernel trainers** to `kernels-fidelity`. This route
  only explains the model-facing QSVC/QSVR contract.
- **Route optimizer catalog, support levels, SPSA/QNSPSA, and detailed
  optimizer tuning** to `optimizers`; choose only the model attachment here.
- **Route dataset generation, circuit helpers, and TorchConnector/PyTorch**
  to `data-circuits-connectors`.

## Operating procedure

1. Install the public package in the target environment with
   `python -m pip install qiskit-machine-learning`; add only required public
   optional extras. Do not assume a source checkout or a private import path.
2. Make `X` a numeric two-dimensional array `(n_samples, n_features)` and
   make its feature dimension match the feature-map data parameters/qubits.
   Keep a separate held-out set for a meaningful score.
3. Select the output representation before choosing the loss: sampler-based
   VQC produces class probabilities; estimator-based VQR produces observable
   expectations. Use the exact label/output shapes in `api-reference.md`.
4. Choose a bounded optimizer budget for a smoke or pilot run. Set
   `algorithm_globals.random_seed` when deterministic initialization or
   sampling matters. A successful `fit` returns `self`; inspect `weights` or
   `fit_result` only after fitting.
5. For V2/runtime primitives, use a compatible `pass_manager` for circuits that
   require ISA transpilation. Preserve measurements for sampler circuits and
   keep observables layout-aligned for estimator circuits; see the migration
   sharp bits in `troubleshooting.md`.
6. Validate on `score` and inspect prediction shape/content, not only an
   optimizer objective. Classification score is mean accuracy; regression
   score is the coefficient of determination (`R^2`).
7. Before persistence, record package/runtime versions, data preprocessing,
   feature map/ansatz or kernel, primitive/backend, pass manager, seed, loss,
   optimizer settings, and callback behavior. Treat dill files as trusted
   executable artifacts.

## Fast decisions

| Need | First choice | Critical contract |
|---|---|---|
| Variational classification | `VQC` | one-hot class probabilities; default `cross_entropy` |
| Variational scalar regression | `VQR` | estimator expectation target; default `squared_error` |
| Kernel classification | `QSVC` | pass `quantum_kernel=...`, never `kernel=...` |
| Kernel regression | `QSVR` | raw features or correctly shaped precomputed matrices |
| Large-step binary kernel classification | `PegasosQSVC` | binary labels; `num_steps` has no early stopping |
| Conditional probabilities | `QBayesian` | one-qubit named registers and binary evidence |

For a concrete recipe and recovery actions, read the references rather than
copying private implementation details. Do not claim a statevector smoke
proves a vendor backend, shot noise, cloud session, or optional dependency.
