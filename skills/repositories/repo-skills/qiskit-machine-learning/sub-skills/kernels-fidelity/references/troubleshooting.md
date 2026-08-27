# Fidelity-kernel troubleshooting

## Feature-map and input dimension errors

**Symptoms:** `ValueError` about incompatible dimensions, a feature map that
cannot be adjusted, or a trainable kernel rejecting otherwise plausible data.

**Checks and recovery:**

1. Print `X.shape`, `Y.shape` and `kernel.num_features` before evaluation.
2. Use `(N, D)` arrays; a one-dimensional `(D,)` array is interpreted as one
   sample, while an empty array or an array with more than two dimensions is
   invalid.
3. Ensure `Y.shape[1] == X.shape[1]` for asymmetric evaluation.
4. For trainable kernels, remember that `num_features` excludes training
   parameters. Bind training values separately; do not append them to each data
   row.
5. Create a feature map with an explicit, matching number of qubits and data
   parameters. Although base validation attempts to adjust `num_qubits`, a
   fixed/opaque circuit may reject that mutation. Do not mutate a shared feature
   map while another kernel is evaluating it.

## Missing feature map

**Symptom:** constructing a kernel with no feature map raises
`QiskitMachineLearningError`.

**Recovery:** provide a concrete parameterized `QuantumCircuit` or a public
feature-map circuit such as `zz_feature_map(feature_dimension=D)`. The current
source's constructor annotations may show `feature_map=None`, but the base class
requires a map; explicit construction is the compatible choice.

## Wrong precomputed matrix shape

**Symptoms:** sklearn's precomputed SVC/SVR rejects `fit`/`predict`, or a model
runs but produces nonsensical results.

**Recovery:** for `N` training points and `M` query points, use:

```python
K_train = kernel.evaluate(X_train)           # (N, N)
K_query = kernel.evaluate(X_query, X_train)  # (M, N)
```

The columns of `K_query` must be in the exact training-sample order used by
`K_train`. Do not use `kernel.evaluate(X_query)` as a test matrix. Add explicit
shape assertions and retain the sample-order metadata in your own pipeline.
This catches the difficult synthetic case where a query matrix is square but
still has the wrong columns.

## Unexpected asymmetry or diagonal values

**Symptoms:** `K` is not symmetric, the diagonal is not exactly one, or duplicate
entries differ under shot noise.

**Checks:**

- `evaluate(X)` is the symmetric path; `evaluate(X, Y)` is asymmetric unless
  arrays are exactly equal. A transpose relationship is expected only when the
  corresponding sample sets and fidelity execution are equivalent.
- For `FidelityQuantumKernel`, inspect `evaluate_duplicates`. `all` measures
  diagonal and duplicate entries; `off_diagonal` forces only the symmetric
  diagonal to one; `none` forces all equal-sample pairs to one.
- For statevector kernels, equal statevector arrays are left at one. This is not
  the same named duplicate policy as the primitive kernel.
- Check whether a custom fidelity returns one value per requested pair and that
  `max_circuits_per_job` chunking preserves ordering.

## Negative eigenvalues or PSD failures

**Symptom:** a symmetric noisy matrix has negative eigenvalues or a downstream
precomputed kernel method rejects it.

**Recovery:** use `enforce_psd=True` for symmetric evaluation. The implementation
projects negative eigenvalues to zero. This does not repair an asymmetric matrix;
check that the intended training call was `evaluate(X)` and that no pair-order
bug exists. Keep `enforce_psd=False` only when the raw noise is itself the object
of study, and report the eigenvalue behavior explicitly.

## Statevector cache and shot noise problems

**Symptoms:** memory grows, repeated evaluations appear stale, or matrices vary
between calls.

**Recovery:**

- `auto_clear_cache=True` clears at each evaluation. With `False`, use
  `clear_cache()` after circuit changes or between unrelated workloads.
- `cache_size` bounds entries but does not make statevector simulation cheap for
  large circuits. Monitor the cache and memory.
- `shots=None` is exact. A finite `shots` value adds binomial sampling and can
  make a matrix non-PSD; enable PSD projection if required.
- Set the package's documented random seed facility when a reproducible shot
  smoke is needed, but do not expect a noisy result to equal an exact reference.

## Unbound or invalid trainable parameters

**Symptoms:** `QiskitMachineLearningError` says a training parameter is not
bound, or `assign_training_parameters` raises `ValueError`.

**Recovery:**

```python
kernel.assign_training_parameters(values)       # exact-length sequence
# or
kernel.assign_training_parameters({parameter: value})
```

A sequence length must equal the number of training parameters. A mapping key
must be one of `training_parameters`; mappings can update a subset, but every
parameter must have a value before `evaluate`. Verify
`kernel.parameter_values` and `kernel.num_training_parameters`. Do not confuse
feature `Parameter`s with training `Parameter`s.

## Trainer does not start or behaves unexpectedly

**Symptoms:** `fit` raises because there are no user parameters, loss selection
fails, or optimization is prohibitively slow.

**Recovery:**

- Add at least one training parameter to the circuit and pass it in
  `training_parameters`; a plain non-trainable kernel cannot be fitted.
- Use one of `svc_loss`, `svr_loss`, `msr_loss`, `mar_loss`, `huber_loss`, or pass
  a `KernelLoss` object. Use an explicit loss instance for non-default sklearn
  options.
- Ensure `initial_point` has exactly one entry per training parameter. If omitted,
  the trainer samples an initial point.
- Prefer derivative-free optimization (the default is `SPSA`); kernel losses do
  not expose an analytical gradient and each objective evaluation computes a
  kernel matrix and fits an sklearn model.
- Start with few samples and bounded iterations. `fit` mutates the supplied
  trainable kernel; preserve the result's `optimal_parameters` if a later run
  must be reproducible.

## ComputeUncompute input/result errors

**Symptoms:** circuit-list length mismatch, parameter-value errors, fidelity
result length mismatch, or a sampler job wrapped in `AlgorithmError`.

**Recovery:**

- Pass equal-length circuit lists, or one circuit on each side. Verify the two
  circuits have equal qubit counts.
- Supply values for every free circuit parameter. Use a 2-D value list when
  passing multiple circuit pairs; left/right values are concatenated internally.
- Check `len(result.fidelities)` equals the number of circuit pairs. Use the
  public truncated `fidelities` for bounded values and inspect
  `raw_fidelities` only when error mitigation or custom processing requires it.
- Retrieve the underlying sampler job's exception and confirm sampler result
  support when `AlgorithmError("Sampler job failed!")` is raised.

## Runtime pass-manager/layout mismatch

**Symptoms:** submission rejects a transpiled circuit, measurement keys do not
match, all fidelities are zero, or an identical-state test is not near one.

**Recovery:**

1. Generate the pass manager for the same backend target and qubit count used by
   the sampler; do not reuse one from a different backend.
2. Pass it at fidelity construction time:
   `ComputeUncompute(sampler=sampler, pass_manager=pass_manager)`.
3. Inspect the resulting fidelity circuit's `layout`, physical qubits,
   measurements, and classical register mapping.
4. Run an identical pair and a known orthogonal/simple pair before a matrix.
5. If a runtime transpiler strips or rewrites layout metadata, use the provider's
   documented pass-manager path or a compatible sampler configuration rather
   than patching bitstring interpretation in user code.

The implementation uses layout metadata, when available, to determine the input
virtual-qubit count during V2 post-processing. A circuit can submit successfully
and still produce wrong post-processing if virtual/physical measurement mapping
is inconsistent.
