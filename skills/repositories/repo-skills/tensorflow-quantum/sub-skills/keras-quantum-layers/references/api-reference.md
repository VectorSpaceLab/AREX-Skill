# API Reference

Verified from the installed-package inspection artifacts and the source modules
that define `tensorflow_quantum.python.layers.*` and `tfq.layers.__init__`.

## Public export surface

`tfq.layers` exports the layer names below from the package root:
`AddCircuit`, `Expectation`, `Sample`, `SampledExpectation`, `State`,
`Unitary`, `PQC`, `ControlledPQC`, `NoisyPQC`, and `NoisyControlledPQC`.

## Layer quick reference

### AddCircuit

- Constructor: `AddCircuit(**kwargs)`
- Call: `call(inputs, *, append=None, prepend=None)`
- Purpose: append or prepend a fixed circuit, or a batch of circuits, to an
  input batch of circuits.
- Output: serialized circuit tensor with the same outer batch size as the
  input.
- Notes: exactly one of `append` or `prepend` must be provided. Use this when
  a quantum data circuit needs a small deterministic prefix/suffix before a
  readout layer or a PQC layer.

### Expectation

- Constructor: `Expectation(backend='noiseless', differentiator=None, **kwargs)`
- Call: `call(inputs, *, symbol_names=None, symbol_values=None, operators=None,
  repetitions=None, initializer=RandomUniform(0, 2π))`
- Default behavior:
  - `'noiseless'` or legacy `None` resolves to the native analytic expectation
    path.
  - `'noisy'` routes to the noisy expectation path and requires `repetitions`
    at call time.
  - `differentiator=None` uses `Adjoint()` for noiseless/`None` backends and
    `ParameterShift()` otherwise.
- Output: dense `tf.Tensor` with shape `[batch_size, n_ops]`.
- Notes: `symbol_values` may be omitted. In that case the layer creates and
  manages a trainable weight vector initialized by `initializer`.

### Sample

- Constructor: `Sample(backend='noiseless', **kwargs)`
- Call: `call(inputs, *, symbol_names=None, symbol_values=None, repetitions=None)`
- Default behavior: `'noiseless'` or legacy `None` uses the native sampler
  path; `'noisy'` uses the noisy sample path; a compatible `cirq.Sampler`
  object is also accepted.
- Output: ragged samples with shape `[batch_size, repetitions, n_qubits]`.
- Notes: `repetitions` is required and must be a positive integer or int32
  tensor.

### SampledExpectation

- Constructor: `SampledExpectation(backend='noiseless', differentiator=None, **kwargs)`
- Call: `call(inputs, *, symbol_names=None, symbol_values=None, operators=None,
  repetitions=None, initializer=RandomUniform(0, 2π))`
- Default behavior:
  - `differentiator=None` uses `ParameterShift()`.
  - `'noiseless'` or legacy `None` uses the native sampled-expectation path;
    `'noisy'` routes to the noisy sampled-expectation path.
  - A backend that is a final-state simulator but not a `cirq.Sampler`
    is rejected; use `Expectation` instead.
- Output: dense `tf.Tensor` with shape `[batch_size, n_ops]`.
- Notes: `repetitions` is required. Like `Expectation`, the layer can create
  and manage trainable symbol values when `symbol_values` is omitted.

### State

- Constructor: `State(backend=None, **kwargs)`
- Call: `call(inputs, *, symbol_names=None, symbol_values=None)`
- Default behavior: `backend=None` uses the package's native state simulator.
  A custom backend must implement `cirq.SimulatesFinalState`.
- Output: ragged tensor of state amplitudes or density-matrix values, with
  shape `[batch_size, state_size]`.
- Notes: use `cirq.DensityMatrixSimulator` when a density matrix is needed.

### Unitary

- Constructor: `Unitary(**kwargs)`
- Call: `call(inputs, *, symbol_names=None, symbol_values=None)`
- Default behavior: no backend argument is accepted.
- Output: ragged tensor of unitary matrices with shape
  `[batch_size, state_size, state_size]`.
- Notes: every symbol in the circuit must be resolved before the unitary is
  meaningful.

### PQC

- Constructor: `PQC(model_circuit, operators, *, repetitions=None,
  backend='noiseless', differentiator=None,
  initializer=RandomUniform(0, 2π), regularizer=None, constraint=None, **kwargs)`
- Call: `call(inputs)`
- Default behavior:
  - `repetitions=None` selects the analytic expectation path.
  - A positive `repetitions` value selects sampled expectation.
  - `backend='noisy'` is rejected here; use `NoisyPQC` instead.
  - `backend=None` is legacy-accepted and behaves like the default path.
  - `differentiator=None` is routed through the underlying executor choice.
- Output: dense `tf.Tensor` with shape `[batch_size, n_operators]`.
- Notes: the layer creates trainable managed parameters from the symbols in
  `model_circuit`. The `symbols` property returns the ordered symbol list, and
  `symbol_values()` returns the current symbol-to-value mapping.

### ControlledPQC

- Constructor: `ControlledPQC(model_circuit, operators, *, repetitions=None,
  backend='noiseless', differentiator=None, **kwargs)`
- Call: `call(inputs)` where `inputs` is `[quantum_data, control_values]`.
- Default behavior:
  - `repetitions=None` selects the analytic expectation path.
  - A positive `repetitions` value selects sampled expectation.
  - `backend='noisy'` is rejected here; use `NoisyControlledPQC` instead.
  - `backend=None` is legacy-accepted and behaves like the default path.
- Output: dense `tf.Tensor` with shape `[batch_size, n_operators]`.
- Notes: the first input is the symbol-free quantum data batch. The second
  input must contain control values ordered to match `layer.symbols`.

### NoisyPQC

- Constructor: `NoisyPQC(model_circuit, operators, *, repetitions=None,
  sample_based=None, differentiator=None,
  initializer=RandomUniform(0, 2π), regularizer=None, constraint=None, **kwargs)`
- Call: `call(inputs)`
- Default behavior:
  - `repetitions` is required and must be a positive integer.
  - `sample_based` is required and must be a boolean.
  - `differentiator=None` uses `ParameterShift()`.
  - No custom `backend` argument is accepted.
- Output: dense `tf.Tensor` with shape `[batch_size, n_operators]`.
- Notes: use this instead of `PQC` when the model circuit itself contains noise
  and the desired behavior is noisy training.

### NoisyControlledPQC

- Constructor: `NoisyControlledPQC(model_circuit, operators, *, repetitions=None,
  sample_based=None, differentiator=None, **kwargs)`
- Call: `call(inputs)` where `inputs` is `[quantum_data, control_values]`.
- Default behavior:
  - `repetitions` is required and must be a positive integer.
  - `sample_based` is required and must be a boolean.
  - `differentiator=None` uses `ParameterShift()`.
  - No custom `backend` argument is accepted.
- Output: dense `tf.Tensor` with shape `[batch_size, n_operators]`.
- Notes: use this instead of `ControlledPQC` when the circuit being controlled
  already includes noise.

## Shared input rules

- `symbol_names` may be strings or `sympy.Symbol` objects and must be unique.
- `symbol_values` must resolve to rank-2 float tensors when provided.
- A single operator or flat operator list may be tiled across a circuit batch;
  nested lists/tensors are used when each circuit needs its own operator batch.
- `AddCircuit` accepts a single circuit, a list, or a circuit tensor for each
  side of the append/prepend contract.
- `ControlledPQC` and `NoisyControlledPQC` always consume two inputs in order:
  circuit batch first, control values second.
- `Sample`, `Expectation`, and `SampledExpectation` treat `repetitions` as the
  shot or trajectory count. `Sample` requires it at call time; the noisy path in
  `Expectation` and `SampledExpectation` also requires it.
