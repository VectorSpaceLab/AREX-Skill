# Core object API reference

This subskill centers on the objects QuTiP users manipulate most often.

## Build and inspect `Qobj`

A `Qobj` wraps an array-like payload together with Hilbert-space dimensions and type metadata.
The most useful attributes and methods are:

- `dims` — tensor-space structure.
- `shape` — matrix shape.
- `isherm`, `isket`, `isbra`, `isoper`, `issuper` — object-type flags.
- `dag()` — Hermitian adjoint.
- `unit()` — normalization helper for states.
- `ptrace(...)` — partial trace.

A quick live signature check in the inspected QuTiP build shows the constructor as:

```python
Qobj(arg=None, dims=None, copy=True, superrep=None, isherm=None, isunitary=None, dtype=None)
```

## Common constructors

Use the smallest constructor that matches the physics:

- `basis(...)` for kets.
- `ket2dm(...)` for density matrices.
- `sigmax()`, `sigmay()`, `sigmaz()`, `qeye()`, `destroy()`, `create()` for common operators.
- `tensor(...)` for composite systems.
- `rand_ket`, `rand_dm`, `rand_unitary`, `rand_super` for randomized smoke checks and examples.

## Measurement and comparison helpers

- `measure_observable(state, op, tol=None)` for projective measurements.
- `measurement_statistics_observable(state, op, tol=None)` for probabilities and projectors.
- `fidelity`, `tracedist`, `bures_dist`, `bures_angle`, `hellinger_dist`, `hilbert_dist` for state distances.
- `average_gate_fidelity`, `process_fidelity`, `unitarity`, `dnorm` for channels and processes.
- `entropy_vn`, `entropy_linear`, `entropy_mutual`, `entropy_relative`, `concurrence` for entanglement and mixedness.

## Structural helpers

- `partial_transpose` for bipartite analysis.
- `super_tensor`, `to_super`, `to_choi`, `to_kraus`, `to_chi`, `to_stinespring` for channel representations.
- `direct_sum` and `simdiag` for less-common linear-algebra workflows.
- `gates` and `spin_*` helpers for prebuilt operators.

## How to read this reference

If the task is about building the state or operator correctly, read this first.
If the task has already moved on to time evolution or plotting, switch to the matching subskill instead of piling more object logic into the answer.
