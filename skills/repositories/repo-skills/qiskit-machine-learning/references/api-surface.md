# Public API Surface

Use this index to choose the nearest sub-skill. Signatures below were checked
against the 1.0.0 package during construction; detailed parameter behavior
belongs in each sub-skill's `api-reference.md`.

## End-to-end algorithms

- `qiskit_machine_learning.algorithms.VQC`: sampler-based variational
  classifier; accepts `num_qubits`, `feature_map`, `ansatz`, `loss`,
  `optimizer`, `warm_start`, `initial_point`, `callback`, and keyword
  `sampler`, `interpret`, `output_shape`, `pass_manager`.
- `VQR`: estimator-based variational regressor with `observable`, `estimator`,
  and `pass_manager` variants.
- `NeuralNetworkClassifier` and `NeuralNetworkRegressor`: fit scikit-learn-like
  models around a supplied QNN.
- `QSVC`, `QSVR`, and `PegasosQSVC`: kernel-facing classifier/regressor APIs;
  pass a kernel with the keyword `quantum_kernel`.
- `QBayesian`: `QBayesian(circuit, *, limit=10, threshold=0.9, sampler=None,
  pass_manager=None)` for circuit-based Bayesian inference.

## QNNs and gradients

- `EstimatorQNN(*, circuit, estimator=None, observables=None, input_params=None,
  weight_params=None, gradient=None, input_gradients=False,
  default_precision=0.015625, pass_manager=None)`.
- `SamplerQNN(*, circuit, sampler=None, input_params=None, weight_params=None,
  sparse=False, interpret=None, output_shape=None, gradient=None,
  input_gradients=False, pass_manager=None)`.
- `ParamShiftEstimatorGradient(estimator, options=None,
  derivative_type=DerivativeType.REAL, pass_manager=None)` and
  `ParamShiftSamplerGradient(sampler, options=None, pass_manager=None)`.
- `LinCombEstimatorGradient`, `LinCombSamplerGradient`,
  `SPSAEstimatorGradient`, `SPSASamplerGradient`, `QFI`, `LinCombQGT`, and
  effective-dimension classes are available from their public subpackages.

## Kernels and fidelities

- `FidelityQuantumKernel(*, feature_map=None, fidelity=None, enforce_psd=True,
  evaluate_duplicates='off_diagonal', max_circuits_per_job=None)`.
- `FidelityStatevectorKernel(*, feature_map=None, statevector_type=Statevector,
  cache_size=None, auto_clear_cache=True, shots=None, enforce_psd=True)`.
- Trainable kernel variants add training parameters; `QuantumKernelTrainer`
  optimizes a trainable kernel with a kernel loss.
- `ComputeUncompute(sampler, *, options=None, local=False, pass_manager=None)`
  constructs fidelity circuits and post-processes sampler results.

## Primitives, circuits, data, connectors

- `QMLEstimator(*, default_precision=0.0, seed=None, **kwargs)` and
  `QMLSampler(shots=None, **kwargs)` provide exact/reference behavior as well
  as delegated sampler/estimator execution.
- `qnn_circuit(num_qubits=None, feature_map=None, ansatz=None)` combines or
  creates QNN circuits; `raw_feature_vector(feature_dimension)` creates an
  amplitude-encoding circuit with that feature dimension.
- `ad_hoc_data(...)` returns class-separated training/test feature and label
  arrays; `phase_of_matter_data(...)` returns statevector or array features and
  labels; `entanglement_concentration_data(...)` provides entanglement data.
- `TorchConnector(neural_network, initial_weights=None, sparse=None)` wraps a
  QNN as a PyTorch module. Install `torch`; install `sparse` when sparse output
  is used.

## Optimizers and utilities

- Public optimizers include `COBYLA`, `SPSA`, `QNSPSA`, `ADAM`, `AQGD`,
  `GradientDescent`, SciPy wrappers, steppable optimizers, and optional NLopt
  classes. See [optimizers](../sub-skills/optimizers/SKILL.md).
- `algorithm_globals.random_seed` controls package-level reproducibility;
  `validate_initial_point`, `validate_bounds`, loss functions, and circuit
  cache helpers support model setup and diagnostics.
