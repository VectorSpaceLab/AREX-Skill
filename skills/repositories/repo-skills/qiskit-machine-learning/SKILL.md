---
name: qiskit-machine-learning
description: "Guides public Qiskit Machine Learning workflows for quantum
  classifiers and regressors, quantum kernels, QNNs and gradients, optimizers,
  datasets, circuits, reference primitives, and PyTorch connectors."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Qiskit Machine Learning

Use this skill when a task asks how to install or use the public
`qiskit-machine-learning` package, build a quantum machine-learning model,
compute a quantum kernel, construct a QNN, select an optimizer, generate a
built-in dataset, use reference primitives, or connect a QNN to PyTorch.
This skill describes package version 1.0.0 evidence from Qiskit Machine
Learning commit `3bdcce7e39aaca0700a7a7fcfba79230a8825a41`; read
[repo-provenance.md](references/repo-provenance.md) before deciding whether a
checkout is stale.

## Install and verify

Install the public distribution rather than depending on a source checkout:

```bash
python -m pip install qiskit-machine-learning
python -c "import qiskit_machine_learning as qml; print(qml.__version__)"
```

The base package requires Python >=3.10, Qiskit >=2.0, NumPy, SciPy,
scikit-learn, and `dill`. Add only the extras needed by the requested workflow:

- `python -m pip install 'qiskit-machine-learning[torch]'` for
  `TorchConnector` and PyTorch autograd.
- `python -m pip install 'qiskit-machine-learning[sparse]'` for sparse arrays.
- Install `nlopt` separately for the NLopt optimizer family.
- Install `qiskit-aer` only when an Aer backend is explicitly selected.

Run `scripts/check_env.py` for a public import and optional-backend diagnosis;
read its `--help` output before adding `--require-*` gates. The helper does not
download data, contact a service, or require the original repository.

## Route by task

- **End-to-end fit, predict, score, save/load, VQC/VQR/QSVC/QSVR, or Bayesian
  inference:** read [algorithms](sub-skills/algorithms/SKILL.md).
- **EstimatorQNN/SamplerQNN construction, forward/backward, gradients, QFI,
  QGT, or effective dimension:** read
  [qnn-gradients](sub-skills/qnn-gradients/SKILL.md).
- **Fidelity/statevector kernels, trainable kernels, ComputeUncompute, kernel
  matrices, or kernel training:** read
  [kernels-fidelity](sub-skills/kernels-fidelity/SKILL.md).
- **COBYLA, SPSA/QNSPSA, ADAM, gradient descent, ask/tell, bounds, or NLopt:**
  read [optimizers](sub-skills/optimizers/SKILL.md).
- **Built-in datasets, circuit helpers, exact primitives, TorchConnector,
  sparse output, or optional-backend diagnosis:** read
  [data-circuits-connectors](sub-skills/data-circuits-connectors/SKILL.md).

A task may cross routes. For example, a VQC request starts in `algorithms`,
then follows `qnn-gradients` for a custom QNN and `optimizers` for detailed
noise-aware tuning. A QSVC request starts in `algorithms` but follows
`kernels-fidelity` when the kernel matrix or fidelity primitive is the issue.

## Shared operating rules

1. Treat `X` as a numeric `(n_samples, n_features)` array and check that the
   feature map, circuit parameters, and qubit count agree before fitting.
2. Choose estimator versus sampler semantics deliberately: estimators return
   expectation values; samplers return distributions or interpreted outputs.
3. For Qiskit V2 or IBM Runtime primitives, transpile with a compatible pass
   manager, add measurements before sampler transpilation, and apply a
   transpiled circuit layout to estimator observables.
4. Bound pilot optimizer iterations, set
   `qiskit_machine_learning.utils.algorithm_globals.random_seed` when
   reproducibility matters, and report the actual primitive/backend used.
5. Keep optional dependency and accelerator claims explicit. A successful CPU
   import does not prove CUDA, ROCm, cloud, or vendor-runtime behavior.
6. Treat `dill` model files as trusted executable artifacts; record package,
   primitive, circuit, preprocessing, and optimizer versions alongside them.

Read [api-surface.md](references/api-surface.md) for the public family map,
[migration-and-sharp-bits.md](references/migration-and-sharp-bits.md) for V2
migration and layout failures, and [troubleshooting.md](references/troubleshooting.md)
for cross-cutting installation, optional-dependency, and runtime recovery.
