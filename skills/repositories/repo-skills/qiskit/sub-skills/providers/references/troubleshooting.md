# Provider and backend troubleshooting

## Backend not found

**Symptom**: `QiskitBackendNotFoundError` from `get_backend()`.

**Cause**: the requested backend name does not match the provider's available backends, or filters are too restrictive.

**Fix**: inspect `provider.backends()` and then retry with an exact backend name or relaxed filters.

## `GenericBackendV2` rejects basis gates

**Symptom**: construction raises `QiskitError` about unsupported or too-wide basis gates.

**Cause**: the requested gate is not in Qiskit's supported standard-gate set or needs more qubits than the backend exposes.

**Fix**: reduce the basis gate list, increase `num_qubits`, or use a custom `Target` in the transpiler path.

## Coupling map size mismatch

**Symptom**: the fake backend refuses the coupling map.

**Cause**: the coupling map qubit count does not match `num_qubits`.

**Fix**: rebuild the coupling map with the same qubit count as the fake backend.

## Invalid `run()` input

**Symptom**: backend `run()` raises `QiskitError` before simulation.

**Cause**: the input is not a `QuantumCircuit` or a list of `QuantumCircuit` objects.

**Fix**: validate inputs and transpile/measure circuits before passing them to the backend.

## Aer fallback surprises

**Symptom**: `GenericBackendV2.run()` warns that Aer is not found, or noise behavior differs from expectations.

**Cause**: Aer is optional. Without it, `GenericBackendV2` falls back to `BasicSimulator` without noise.

**Fix**: install `qiskit-aer` only when the workflow requires Aer-backed noise modeling; otherwise treat the fallback as expected.

## Option validator errors

**Symptom**: setting or passing an option raises a `ValueError` or `TypeError`.

**Cause**: the option validator rejects a value such as an out-of-range shot count or unsupported method.

**Fix**: inspect the backend options and validator constraints before forwarding user kwargs.
