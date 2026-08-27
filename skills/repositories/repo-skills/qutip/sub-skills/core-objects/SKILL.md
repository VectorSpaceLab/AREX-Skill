---
name: "core-objects"
description: "QuTiP quantum-object construction, algebra, measurement, and
  metric workflows."
metadata:
  disco-role: operating
disable-model-invocation: true
license: BSD 3-Clause
---

# Core objects

Use this subskill when the task is about QuTiP's fundamental quantum-object layer: `Qobj`, state and operator construction, tensor products, superoperators, random states, measurements, metrics, entropy, partial transpose, and gate helpers.

## Read this subskill when the prompt mentions

- `Qobj`, `basis`, `ket2dm`, `qeye`, `destroy`, `create`, `sigmax`, `sigmaz`, `tensor`
- density matrices, kets, bras, operator dimensions, or tensor structure
- `measure_observable`, `measurement_statistics_observable`, or POVM-style measurements
- `fidelity`, `tracedist`, `bures_dist`, `average_gate_fidelity`, or similar metrics
- random states/operators, superoperators, partial trace, partial transpose, or entropy

## What to do first

1. Decide the Hilbert-space dimensions before building objects.
2. Create the simplest valid `Qobj` or constructor result that matches the physics.
3. Check `dims`, `shape`, `isherm`, `isket`, `isbra`, `isoper`, or `superrep` before doing anything more complicated.
4. If the task includes evolution, coefficients, or plotting, route to a different subskill instead of expanding this one.

## Core workflow

- Use the state and operator constructors from `qutip.core.states` and `qutip.core.operators`.
- Compose systems with `tensor` and `super_tensor` when tensor structure matters.
- Convert between kets and density matrices with `ket2dm`.
- Use measurement helpers only when the operator/state dimensions are already compatible.
- Use metrics and entropy helpers after the state or channel is built and sanity-checked.

## Typical success signals

- The object prints the expected tensor dimensions.
- The object type matches the intended physics role.
- Measurement probabilities sum to one.
- Metrics like fidelity and trace distance return finite values in the expected range.

## Boundaries

Use this subskill for object validity and algebra. Do not use it as the primary route for:

- Time evolution, collapse operators, solver options, or time-dependent Hamiltonians; use `dynamics-and-solvers`.
- Bath models, PIQS, HEOM, or transfer tensors; use `specialized-open-systems`.
- Figure creation, tomography plots, or object serialization; use `analysis-and-io`.

## Answer shape

When responding from this subskill, give:

1. The concrete constructor or helper API to use.
2. A minimal object-building code snippet.
3. The dimension/type checks that prove the object is valid.
4. The next route if the user wants to evolve, plot, or save the object.

## Validation hints

- For tensor workflows, print `dims` before and after `tensor` or `ptrace`.
- For measurements, check that all projectors/observables share the state dimensions.
- For metrics, check normalization and object type before trusting the number.

## Reference files

- `references/api-reference.md` for constructors, object properties, and the most-used helper families.
- `references/workflows.md` for small composition, measurement, and comparison recipes.
- `references/troubleshooting.md` for dims mismatch, type mismatch, and measurement errors.

## Helper script

- `scripts/core_smoke.py` runs a tiny object-construction, tensor, measurement, and metric smoke check.
