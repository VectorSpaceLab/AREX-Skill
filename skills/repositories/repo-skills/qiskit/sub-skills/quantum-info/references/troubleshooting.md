# Quantum-info troubleshooting

## Operator construction fails on a circuit

**Symptom**: `Operator` or `Operator.from_circuit()` rejects a circuit.

**Cause**: the circuit may contain measurement, reset, non-unitary behavior, or instructions that cannot be converted to a matrix.

**Fix**: remove final measurements for unitary analysis, or use a state/result workflow instead of an operator workflow.

## Dimensions do not match

**Symptom**: state, operator, or Pauli construction fails with a shape or dimension error.

**Cause**: the array dimension is not compatible with the declared subsystem dimensions or Pauli string length.

**Fix**: state qubit count and matrix shape explicitly before constructing the object.

## Numerical equality is surprising

**Symptom**: two matrices or states look equivalent but equality fails.

**Cause**: global phase, floating-point tolerance, or qubit-order convention differences.

**Fix**: use an equivalence helper or predicate with explicit tolerance and phase policy instead of raw equality.

## `diamond_norm` or an advanced measure is unavailable

**Symptom**: an optional import is missing while computing a measure.

**Cause**: some advanced quantum-information routines rely on optional external solvers such as `cvxpy`.

**Fix**: install the named package only when that measure is required; do not add unrelated extras.

## Matrices are too large

**Symptom**: memory use explodes or a small-looking task becomes slow.

**Cause**: full state and operator representations scale exponentially with qubit count.

**Fix**: reduce the circuit size, use sparse Pauli representations, or avoid full matrix construction.
