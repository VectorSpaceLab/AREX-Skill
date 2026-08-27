# API reference

Evidence used for this sub-skill:

- Installed package inspection for the public core tensor-conversion and
  execution getters.
- Source modules and source tests that establish the remaining helper semantics,
  shapes, and error messages.
- The package's design notes, distilled into this reference, for the primitive
  tensor and execution model.

The installed inspection artifact captured the public core tensor-conversion and execution getters; the remaining low-level helpers below are source/test-verified from the repository and tests.

## Top-level shape of the API

`tensorflow_quantum.__init__` reexports the core execution ops, tensor helpers,
noise namespace, `tfq.util`, and the package version. `tensorflow_quantum.core`
reexports the same raw execution helpers from `tensorflow_quantum.core.ops`.
This sub-skill focuses on those low-level tensor and execution entry points,
not on Keras layers or differentiators.

## Tensor conversion

### `tfq.convert_to_tensor(items_to_convert, deterministic_proto_serialize=False)`

- Recursively converts nested Python lists, tuples, or NumPy arrays of
  `cirq.Circuit`, `cirq.PauliSum`, or `cirq.PauliString` objects into TFQ
  string tensors.
- Serialization is only defined for circuits and Pauli objects built on
  `cirq.GridQubit`s.
- Inputs must stay rectangular and homogeneous; mixed circuit/Pauli batches or
  incompatible nesting raise `TypeError`.
- Use when a Cirq object batch must become model input or execution input.

### `tfq.from_tensor(tensor_to_convert)`

- Converts a TFQ tensor back into Python Cirq objects.
- Accepts a `tf.Tensor`, NumPy array, list, or tuple containing one serialized
  TFQ object type.
- Mixed decoded types or malformed payloads raise `TypeError`.
- Use it to round-trip a serialized circuit or Pauli batch back to Cirq.

## Raw execution getters

### `tfq.get_expectation_op(backend=None, *, quantum_concurrent=True)`

- `backend=None` returns the native C++ analytic expectation op.
- A `cirq.sim.simulator.SimulatesExpectationValues` backend or
  `cirq.DensityMatrixSimulator` selects Cirq-based analytic expectation.
- Passing a `cirq.SimulatesSamples` or `cirq.Sampler` backend raises
  `NotImplementedError`; use `tfq.get_sampled_expectation_op` instead.
- `quantum_concurrent` must be a Python `bool`.

### `tfq.get_sampled_expectation_op(backend=None, *, quantum_concurrent=True)`

- `backend=None` returns the native C++ sampled-expectation op.
- Any `cirq.Sampler` backend selects the Cirq-based sampled path.
- `num_samples` must match the shape of `pauli_sums` and contain positive
  integer counts.
- Use this for Monte Carlo expectation estimates or noisy circuits.

### `tfq.get_sampling_op(backend=None, *, quantum_concurrent=True)`

- `backend=None` returns the native C++ sampling op.
- Any `cirq.Sampler` backend selects the Cirq-based sampling path.
- Returned padded samples are converted to ragged tensors.
- `quantum_concurrent` must be a Python `bool`.

### `tfq.get_state_op(backend=None, *, quantum_concurrent=True)`

- `backend=None` returns the native C++ state-vector op.
- Any `cirq.SimulatesFinalState` backend selects the Cirq-based state path.
- Returned padded states are converted to ragged tensors.
- `quantum_concurrent` must be a Python `bool`.

### `tfq.get_unitary_op(quantum_concurrent=True)` / `tfq.core.ops.tfq_unitary_op.get_unitary_op(quantum_concurrent=True)`

- Source/test-verified low-level unitary op.
- Returns a callable that produces ragged 2D unitary matrices after padding
  conversion.
- Rejects noisy circuits and follows the same `quantum_concurrent` lock rule
  as the other raw execution ops.

## Utility ops and helpers

### `tfq.append_circuit(programs, programs_to_append)`

- Pairwise appends one batch of serialized circuits to another.
- Inputs must be rank-1 string tensors with matching batch size.
- Use it only after both circuit batches are serialized.

### `tfq.padded_to_ragged(masked_state)`

- Converts a padded state tensor with `-2` sentinels into a ragged tensor.
- This is the low-level helper used by sample/state wrappers.

### `tfq.padded_to_ragged2d(masked_state)`

- Converts a padded rank-3 matrix batch into ragged 2D matrices.
- This is the helper used by the unitary op wrapper.

### `tfq.resolve_parameters(programs, symbol_names, symbol_values)`

- Resolves symbols in serialized circuits and returns serialized circuits.
- Partial resolution is allowed: unresolved symbols remain in the output.
- `symbol_names` is the positional order for `symbol_values`.

## Quantum concurrent op mode

### `tfq.get_quantum_concurrent_op_mode()` / `tfq.set_quantum_concurrent_op_mode(mode)`

- Getter and setter for the global execution-context flag that controls whether
the raw execution ops block one another at graph level.
- Use these only when you need to inspect or override the concurrency mode for
low-level execution debugging.
- The setter expects a Python `bool`.

## Math namespace

### `tfq.math.inner_product(programs, symbol_names, symbol_values, other_programs)`

- Computes batched inner products between a parameterized circuit batch and a
symbol-free comparison batch.
- `other_programs` must be a rank-2 circuit tensor shaped like `[batch_size, n_others]`; use `tfq.convert_to_tensor([[reference_circuit]])` for one reference per input.
- Returns a complex tensor of shape `[batch_size, n_others]`.
- Use it when you need overlap values or when you want a differentiable bridge
for circuit similarity.

### `tfq.math.fidelity(programs, symbol_names, symbol_values, other_programs)`

- Computes squared overlap magnitudes for the same circuit-batch contract used
by `inner_product`.
- Returns a real tensor of shape `[batch_size, n_others]`.
- Use it when you want fidelity rather than complex amplitude overlap.

### `tfq.math.mps_1d_expectation(programs, symbol_names, symbol_values, pauli_sums, bond_dim=4)`

- Uses the C++ MPS simulator to compute 1D non-periodic expectation values.
- `bond_dim` defaults to `4` and must satisfy the simulator's minimum bond-dim
constraint.
- Use it only for 1D circuit topologies without noise channels.

### `tfq.math.mps_1d_sample(programs, symbol_names, symbol_values, num_samples, bond_dim=4)`

- Uses the C++ MPS simulator to return ragged samples for 1D non-periodic
circuits.
- `num_samples` is a one-element rank-1 integer tensor/list such as `[3]`, not a Python scalar.
- Use it when you need samples from a 1D circuit family rather than the native
sampler path.

### `tfq.math.mps_1d_sampled_expectation(programs, symbol_names, symbol_values, pauli_sums, num_samples, bond_dim=4)`

- Uses the C++ MPS simulator and then samples the resulting 1D state to estimate
expectations.
- `num_samples` must match the shape of `pauli_sums`.
- Use it for 1D non-periodic sampled-expectation workflows.

## Noise namespace

### `tfq.noise.expectation(...)`

- Monte Carlo noisy expectation using the native noisy op module.
- `num_samples` must have the same shape as `pauli_sums` and positive integer
  entries.

### `tfq.noise.sampled_expectation(...)`

- Monte Carlo sampled expectation using the noisy trajectory backend.
- Same shape and positivity rules as `tfq.noise.expectation`.

### `tfq.noise.samples(...)`

- Noisy sample generation wrapped to ragged output.
- Use it when the circuit contains channels or when you need noisy bitstrings.

## `tfq.util` helpers

### `tfq.util.get_supported_gates()`

- Returns a dictionary mapping supported Cirq gate instances to their qubit
  arity.
- The mapping is built from the serializer-supported gate types and excludes
  channel classes.

### `tfq.util.get_supported_channels()`

- Returns a dictionary mapping supported Cirq channel instances to arity 1.
- The supported channel set includes depolarizing, amplitude damping, reset,
  phase damping, phase flip, and bit flip variants.

### `tfq.util.get_circuit_symbols(circuit)`

- Returns the string names of the symbols found in a `cirq.Circuit`.
- Controlled operations are handled by scanning the underlying gate symbol
  expressions.

### `tfq.util.exponential(operators, coefficients=None)`

- Builds a Cirq circuit for exponentiating a list or tuple of
  `cirq.PauliSum`/`cirq.PauliString` objects.
- Coefficients may be strings, symbols, floats, or NumPy arrays of those
  values; the coefficient list must match the operator count.
- Terms must be commuting; non-commuting sums raise `ValueError`.
- Complex coefficients are rejected; identity terms use the special identity
  decomposition path.

## Quick ownership reminder

This sub-skill owns raw tensor conversion, execution-op selection, noisy vs
noiseless operator choice, and the small utility helpers that support those
flows.
