# Algorithms troubleshooting

Start by recording the model class, package version, primitive, circuit qubit
count, `X.shape`, `y.shape`, loss, optimizer, seed, and whether the input is a
raw feature matrix or a precomputed kernel matrix. Then apply the narrowest
recovery below.

## Construction and shape failures

- **Missing problem size or feature mismatch:** `X` is `(N, D)`, while the
  feature map must encode `D` values and the circuits must use the selected
  qubit count. Pass explicit `num_qubits`, `feature_map`, and `ansatz` rather
  than relying on deprecated circuit adjustment. Check `feature_map.parameters`
  and ansatz weights before fitting.
- **Target shape mismatch:** VQC default labels are one-hot `(N, C)`. Every row
  must contain only `0/1` and exactly one active class. For scalar-output
  classifiers use a 1D target with two unique classes. VQR scalar targets are
  normally `(N,)`, while a forward result may be `(N, 1)`; that is a model output
  contract, not permission to silently duplicate labels.
- **Changing class count with warm start:** stop the continuation, keep a
  consistent `(N, C)` encoding, or construct a new VQC. A prior two-class fit
  cannot warm-start a three-class output.
- **Predict before fit / absent state:** call `fit` first and check that it
  completed. Inspect `fit_result` and `weights` only after fitting.
- **Unsupported loss:** use `absolute_error`, `squared_error`,
  `cross_entropy`, or an instance of public `Loss`. Cross entropy needs
  probability-like predictions and shape-identical targets; it is not a generic
  regression loss.

## Optimizer, callback, and convergence issues

- **No progress or excessive runtime:** bound `maxiter`/`num_steps`, reduce
  qubits and dataset size for a smoke, set a seed, and use a callback to record
  objective values. Route algorithm-specific optimizer selection to
  `optimizers` rather than increasing iterations blindly.
- **Callback `TypeError`:** model callbacks receive `(weights, value)`. Qiskit
  optimizer callbacks may have another arity; attach the callback at the
  correct layer and inspect that optimizer's public contract.
- **Initial-point error:** make `initial_point` a 1D numeric array with exactly
  the ansatz/QNN trainable-weight count. Warm start uses the prior fitted
  point, not a new random point.
- **Noisy objective:** expectation values and sampled probabilities can vary.
  Use an optimizer intended for noise, a fixed seed where applicable, bounded
  budgets, and report the primitive's shots/precision. Do not compare a noisy
  objective from different primitive configurations as if it were a score.

## Kernels and precomputed matrices

- **QSVC/QSVR rejects or mispredicts:** pass `quantum_kernel=...`, not
  `kernel=...`. In callable mode use raw `X` `(N, D)` for fit and `(M, D)` for
  prediction. In `quantum_kernel="precomputed"` mode use `K_train (N, N)` and
  `K_test (M, N)`; the second axis must align to training samples.
- **Pegasos validation failure:** `precomputed=True` requires
  `quantum_kernel=None`, a square training matrix, and exactly two unique
  labels. Prediction matrices have shape `(M, N_train)`. It has no early stop;
  lower `num_steps` for a bounded trial.
- **Kernel dimension/PSD problems:** validate the kernel object and matrix in
  `kernels-fidelity`. Do not repair a non-square or misaligned matrix by
  reshaping it.

## V2 primitive and layout sharp bits

- **Runtime primitive rejects a circuit:** use a backend-compatible public
  `pass_manager` and pass it consistently. Add measurements to sampler
  circuits before transpilation. Stable classical register names such as
  `meas` or `c` avoid dynamic attribute issues in Sampler V2.
- **Estimator observable mismatch:** the observable must be a `BaseOperator` and
  match the circuit. After `isa_qc = pass_manager.run(qc)`, use
  `isa_observable = observable.apply_layout(isa_qc.layout)` before submitting
  an estimator QNN. VQR handles its own supplied observable path, but custom
  estimator/QNN composition follows this explicit rule.
- **Gradient-generated circuit failure:** if the underlying gradient creates
  circuits for a runtime primitive, give the gradient the same pass manager;
  route detailed gradient construction to `qnn-gradients`.
- **V1/V2 import confusion:** use public current imports from
  `qiskit_machine_learning` for optimizers, gradients, state fidelities, and
  utilities. Do not copy old `qiskit_algorithms` imports into a V2 workflow.

## QBayesian failures and interpretation

- **Invalid register:** every named quantum register must contain exactly one
  qubit. Use one register per binary variable; evidence/query keys must match
  register names exactly.
- **Unexpected bit-string order:** the circuit's last qubit is the most
  significant bit in returned keys. Use `format_res=True` when interpreting
  results by variable name.
- **`inference` says evidence is missing:** call
  `inference(query, evidence={...})`, or call `rejection_sampling` first and
  then reuse its samples. `evidence=None` does not mean unconditional.
- **`converged` is false:** the threshold was not met within the amplification
  limit. Increase `limit` only after checking cost, lower `threshold` only as an
  explicit accuracy trade-off, and report the unconverged status.
- **V2 result counts unavailable:** confirm the sampler result exposes a
  measured data register and that the circuit has classical measurements.
  Pass a compatible pass manager for a backend requiring ISA circuits.

## Optional dependencies and persistence

The base install is `python -m pip install qiskit-machine-learning`. PyTorch,
Sparse, and NLopt are optional; install the public extras only for workflows
that need them. Missing NLopt does not invalidate CPU optimizers—choose a
supported built-in fallback. Missing PyTorch affects TorchConnector, not VQC,
VQR, QSVC, QSVR, or QBayesian.

For dill failures, verify the file is trusted, the corresponding class is used,
and the Python/package environment is compatible. Re-run a fixed prediction
probe after load. A saved model retains referenced primitive objects, so a
successful local load does not prove a cloud session or a different backend is
available.
