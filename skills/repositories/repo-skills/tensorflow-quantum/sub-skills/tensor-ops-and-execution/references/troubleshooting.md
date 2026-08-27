# Troubleshooting

This page covers low-level tensor, backend, and execution failures.

## Backend selection errors

### Symptom
`TypeError: Backend ... is invalid`

### Likely cause
The backend does not satisfy the getter family you called.

### Recovery
- Expectation: use `backend=None`, a `cirq.sim.simulator.SimulatesExpectationValues`
  backend, or `cirq.DensityMatrixSimulator`.
- Sampled expectation: use `backend=None` or a `cirq.Sampler`.
- Sampling: use `backend=None` or a `cirq.Sampler`.
- State: use `backend=None` or a `cirq.SimulatesFinalState`.
- `quantum_concurrent` must be a Python `bool`, not a string, tensor, or other
  wrapper.

### Symptom
`NotImplementedError: Sample-based expectation is not supported`

### Likely cause
A sampler-only backend was passed to `tfq.get_expectation_op`.

### Recovery
Switch to `tfq.get_sampled_expectation_op` for sample-based estimation, or keep
`backend=None` for the native analytic expectation op.

## Tensor rank and batch-shape mismatches

### Symptom
`programs must be rank 1`, `symbol_names must be rank 1`, or
`symbol_values must be rank 2`

### Likely cause
The raw execution op received a tensor with the wrong batch shape.

### Recovery
Build explicit batches with shape:
- `programs`: `[batch_size]`
- `symbol_names`: `[n_params]`
- `symbol_values`: `[batch_size, n_params]`
- `pauli_sums`: `[batch_size, n_ops]`
- `num_samples`: same shape as `pauli_sums`

### Symptom
`num_samples contains sample value <= 0`

### Likely cause
A non-positive sample count was passed to a noisy or sampled-expectation op.

### Recovery
Use positive integer sample counts only.

## Serialization and tensor-conversion failures

### Symptom
`Incompatible item passed into convert_to_tensor` or a non-rectangular error

### Likely cause
A tensor batch mixed Cirq circuits with Pauli objects, or the nesting was not
rectangular.

### Recovery
- Keep one tensor batch type at a time.
- Serialize circuits separately from Pauli sums.
- Use `cirq.GridQubit`s in the source Cirq objects.

### Symptom
`Error decoding item` or `from_tensor expected to find a tensor containing elements of a single type`

### Likely cause
The serialized tensor was malformed, corrupted, or mixed decoded object types.

### Recovery
Rebuild the tensor with `tfq.convert_to_tensor` and keep the decoded batch
homogeneous.

## Parameter-resolution failures

### Symptom
`Unparseable proto`, `Could not find symbol in parameter map`, or
`Cast string to float is not supported`

### Likely cause
The circuit tensor was not TFQ-serialized, the symbol list does not match the
circuit, or the parameter values are not numeric.

### Recovery
- Re-serialize the circuits.
- Ensure the symbol list matches the symbols in the circuit.
- Pass numeric values, not strings.
- Partial resolution is allowed, but only for symbols that actually appear in
the circuit.

## Append and unitary failures

### Symptom
`programs and programs_to_append must have matching sizes`

### Likely cause
The two serialized circuit batches have different batch lengths.

### Recovery
Make both batches the same size before calling `append_circuit`.

### Symptom
A unitary call complains about channels or unsupported noisy circuits

### Likely cause
The circuit contains noise channels, but unitary output is only defined for the
supported noiseless gate set.

### Recovery
Use noisy execution helpers instead of the unitary op when the circuit contains
channels.

## Exponential helper failures

### Symptom
`non-commutable` or `only supports real coefficients`

### Likely cause
The operator sum is not commuting, or one of the coefficients is complex.

### Recovery
Split the operator into commuting pieces, or build the desired circuit by some
other route.

## Noisy-vs-noiseless confusion

### Symptom
The circuit has channels but the chosen getter behaves like a noiseless
simulation path.

### Likely cause
The wrong execution family was chosen.

### Recovery
- Use `tfq.noise.expectation`, `tfq.noise.sampled_expectation`, or
  `tfq.noise.samples` when the circuit includes channels.
- Use `tfq.get_expectation_op`, `tfq.get_sampled_expectation_op`,
  `tfq.get_sampling_op`, or `tfq.get_state_op` for the noiseless families.
- Use `tfq.get_unitary_op` / `tfq.core.ops.tfq_unitary_op.get_unitary_op`
  only for noiseless unitary matrices.

## Inner product and fidelity failures

### Symptom
`Found symbols in other_programs`, `other_programs must be rank 2`, qubit-mismatch errors, or a rank/batch-shape
error while calling `tfq.math.inner_product` or `tfq.math.fidelity`.

### Likely cause
The reference circuits still contain unresolved symbols, or the paired circuit
batches do not have compatible shapes or qubit layouts.

### Recovery
- Resolve the comparison circuits first.
- Keep `symbol_names` aligned with `symbol_values`.
- Make sure the reference batch is symbol-free and rank 2; for one reference circuit use `tfq.convert_to_tensor([[reference_circuit]])`.
- Use `inner_product` when you need the complex overlap, and `fidelity` when you
  need the squared magnitude.

## MPS helper failures

### Symptom
`not in 1D topology`, `cirq.Channel`, `num_samples must be rank ...`, `All input circuits require minimum ... qubits`, or a bond-dimension constraint error
while calling `tfq.math.mps_1d_expectation`, `tfq.math.mps_1d_sample`, or
`tfq.math.mps_1d_sampled_expectation`.

### Likely cause
The helper was used on a non-1D circuit, on a noisy circuit, with the wrong `num_samples` rank, with too few participating qubits for the MPS op, or with a bond
dimension below the simulator minimum.

### Recovery
- Restrict the circuit to a 1D non-periodic topology.
- Remove channels and other noisy operations.
- Keep `bond_dim` at or above the documented minimum (default `4`).
- For `mps_1d_sample`, pass `num_samples` as a rank-1 value such as `[3]`; for sampled expectation, pass a rank-2 value matching the observable tensor such as `[[10]]`.
- If a toy circuit still fails a minimum-qubit check, switch to a 5-qubit line for the MPS smoke.
- For general circuits, switch back to the raw execution getters instead of
  forcing MPS.

## TensorFlow / legacy Keras note

If a smoke snippet imports TensorFlow before TFQ in a legacy-Keras setup, set
`TF_USE_LEGACY_KERAS=1` before the import.
