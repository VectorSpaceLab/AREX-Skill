# Pauli and experiment API reference

All signatures and boundaries here are for PyQuil 4.18.0.

## PauliTerm and PauliSum

Construct terms with `PauliTerm(op, index, coefficient=1.0)` or the helpers
`ID`, `ZERO`, `sI`, `sX`, `sY`, and `sZ`. `op` is one of `I`, `X`, `Y`, `Z`.
Non-identity terms require a non-negative integer qubit, a
`QubitPlaceholder`, or a formal argument. `PauliTerm.from_list([("X", 0),
("Y", 1)], coefficient=...)` is efficient, but the listed qubits must be
disjoint; repeated indices belong in multiplication so the Pauli product phase
is simplified.

A term stores only non-identity operations. `len(term)` is its Pauli weight,
`term.get_qubits()` returns its actual support, `term[q]` returns `I` when `q`
is absent, and `term.operations_as_set()` is the order-independent structural
identity. Prefer `operations_as_set()` over `id()` for comparison; `id()` may
sort qubits and warns for non-sortable placeholders. `term.pauli_string(qubits)`
uses the supplied qubit order and inserts `I` for absent positions. This order
is the right way to make a dense basis string.

Arithmetic returns new simplified objects in ordinary use:

- term × term/sum/number applies the single-qubit multiplication table and its
  complex phase (`X*Y=iZ`, `Y*X=-iZ`, etc.);
- term + term/sum/number returns a `PauliSum` and combines like supports;
- `PauliSum(terms)` requires a sequence of `PauliTerm` objects; an empty sum is
  represented by zero times identity;
- `simplify()` combines equal supports and removes near-zero terms, potentially
  reordering operations;
- `term ** power` and `sum ** power` require a non-negative integer; negative
  powers are rejected;
- `is_identity` means a nonzero scalar multiple of identity, while `is_zero`
  means a zero term/sum. A zero scalar is not an identity observable.

Coefficients may be symbolic Quil expressions for program construction. Numeric
matrix exponentiation and expectation post-processing require fixed numeric
coefficients. Keep coefficients real when the observable is measured.

Useful signatures:

```text
PauliTerm.from_list(terms_list, coefficient=1.0)
PauliTerm.from_compact_str(str_pauli_term)
PauliTerm.pauli_string(qubits=None)       # pass an explicit order in new code
PauliSum.from_compact_str(str_pauli_sum)
PauliSum.get_programs() -> (list[Program], numpy.ndarray)
check_commutation(pauli_list, pauli_two) -> bool
commuting_sets(pauli_sum) -> list[list[PauliTerm]]
```

`commuting_sets` is an algebraic grouping helper. Commuting operators are not
necessarily measurable in the same tensor-product basis using only local basis
rotations. Use `group_settings` for experiment grouping.

## Exponentiation boundaries

`exponentiate(term)` returns a Quil `Program` for `exp(-i * term)`.
`exponential_map(term)` returns a callable `f(alpha)` for
`exp(-i * alpha * term)`. The generated circuit changes X/Y factors into the Z
basis, chains CNOTs over the term support, applies `RZ(2*coefficient*alpha)`,
and reverses the basis change. It is a program builder, not an execution call.

`exponentiate_commuting_pauli_sum(pauli_sum)` returns a callable that concatenates
term exponentials. Use it only when the terms commute; the function does not
prove the premise. For a noncommuting pair, `trotterize(first, second,
trotter_order=1..4, trotter_steps=1...)` returns an approximation. Higher order
and more steps generally reduce approximation error but increase program size.

`exponentiate_pauli_sum(pauli_sum_or_term)` instead returns a dense NumPy
unitary. It requires fixed numeric coefficients and integer qubits (not
placeholders). Its convention is cycles:

```text
U = exp(-i * pi * sum(theta_i P_i)).
```

Do not compare its coefficient convention directly with `exponential_map`
without accounting for the factor of `pi`. Dense matrices scale exponentially
with support size; use the program-producing APIs for larger circuits.

## TensorProductState and ExperimentSetting

`TensorProductState(states=None)` stores one-qubit state descriptors. Helpers
construct descriptors without executing anything:

```python
from pyquil.experiment import (
    SIC0, SIC1, SIC2, SIC3,
    plusX, minusX, plusY, minusY, plusZ, minusZ, zeros_state,
)

initial = plusX(0) * plusZ(1)
setting = ExperimentSetting(initial, sX(0) * sZ(1))
```

The state labels are `SIC` indices 0–3 or Pauli eigenstate labels `X`, `Y`,
`Z` with index 0 for +1 and 1 for -1. `TensorProductState.from_str` and
`ExperimentSetting.from_str` parse their serializable string forms. `SIC` states
cannot be converted to a Pauli input operator by the legacy compatibility
shim; leave them as explicit `TensorProductState` values.

`ExperimentSetting(in_state, out_operator, additional_expectations=None)`
contains one preparation/observable pair. `additional_expectations` is a list
of qubit-index lists computed from the same bitstrings. Its indices refer to the
experiment's measured-register order when passed through the execution path;
validate this mapping before using it.

## Experiment construction

`Experiment(settings, program, *, symmetrization=EXHAUSTIVE,
calibration=PLUS_EIGENSTATE)` accepts a flat list of settings or a list of
setting groups. A flat list is normalized to singleton groups. The object does
not group settings automatically; call `group_settings` explicitly.

The experiment takes `shots` from `program.num_shots`, so put
`program.wrap_in_numshots_loop(shots)` on the main program first. If the input
program contains `RESET`, the constructor records `reset=True` and removes the
reset from the stored body so its generated program can prepend one safely. Do
not declare conflicting generated regions (`ro`, `preparation_*`,
`measurement_*`, or `symmetrization`) in the user program.

Important methods:

```text
experiment.get_meas_qubits() -> sorted list[int]
experiment.get_meas_registers(qubits=None) -> sorted register indices
experiment.generate_experiment_program() -> parameterized Program
experiment.build_setting_memory_map(setting) -> dict[str, list[float]]
experiment.build_symmetrization_memory_maps(qubits, label="symmetrization")
experiment.generate_calibration_experiment() -> Experiment
```

`generate_experiment_program` adds parameterized ZXZXZ preparation/measurement,
optional symmetrization RX gates, readout, and the shot loop. In 4.18.0 it
rejects grouped settings. `build_symmetrization_memory_maps` supports `NONE`
(`[{ }]`) and `EXHAUSTIVE` in the experiment memory-map path; the implementation
raises for OA levels even though `QuantumComputer.run_symmetrized_readout`
supports OA levels. Check the actual chosen path rather than assuming all enum
values are accepted everywhere.

## Symmetrization and calibration levels

`SymmetrizationLevel` is an `IntEnum`:

| Value | Meaning | Construction/execution implication |
| ---: | --- | --- |
| `-1` | `EXHAUSTIVE` | Every bit-flip combination; `2**n` patterns for `n` symmetrized qubits. Required by the built-in plus-eigenstate calibration path. |
| `0` | `NONE` | One ordinary measurement pattern; asymmetric readout remains. |
| `1` | `OA_STRENGTH_1` | Orthogonal-array strength 1 in `run_symmetrized_readout`. Not supported by `Experiment.build_symmetrization_memory_maps` in this release. |
| `2` | `OA_STRENGTH_2` | Orthogonal-array strength 2 in `run_symmetrized_readout`; service execution expands trials. |
| `3` | `OA_STRENGTH_3` | Orthogonal-array strength 3 in `run_symmetrized_readout`; default there, but not the `Experiment` default. |

`CalibrationMethod` is `PLUS_EIGENSTATE=1`, `NONE=0`, and
`MINUS_EIGENSTATE=-1`. The implemented `Experiment.generate_calibration_experiment`
currently supports only plus-eigenstate and exhaustive symmetrization. When a
non-exhaustive experiment is constructed with a nonzero calibration value, the
constructor warns and stores `CalibrationMethod.NONE`.

Calibration estimates a scale factor by preparing the +1 eigenstate of each
observable, measuring the same observable, and dividing the raw expectation by
that calibration expectation. It assumes a nonzero, stable denominator and a
symmetric effective readout model after symmetrization. A small denominator makes
correction and its variance unstable; report this rather than clipping it.

The service-backed `QuantumComputer.run_symmetrized_readout(program, trials,
symm_type=3, meas_qubits=None)` raises for a symmetrization type outside
`[-1,0,1,2,3]` and increases too-small trial counts with a warning. Minimum
trial counts are:

- `-1`: `2**n`;
- `2`: the smallest `4*lambda`-style OA count sufficient for `n`, plus one;
- `3`: the next power of two at least `2*n`;
- `0` and `1`: 2.

These are mathematical minimums, not enough for low statistical error. Use
hundreds or thousands of trials for an actual noisy experiment when practical.

## Grouping and operator estimation

`group_settings(experiment, method="greedy")` returns a new experiment with
settings placed into groups that share compatible tensor-product bases. The
other method is `"clique-removal"`; invalid method names raise `ValueError`.
Grouping requires both:

- compatible input states: no qubit is requested in two different one-qubit
  states;
- compatible output bases: no qubit is requested with two different nonidentity
  Pauli axes.

Commutation alone is insufficient. For example, operators with swapped X/Z
axes on two qubits can commute yet fail local TPB grouping. A grouped setting's
inner list is measured from one bitstring collection and each observable selects
its own subset.

`pyquil.operator_estimation` remains importable in 4.18.0 and exposes
`group_experiments`, `group_experiments_greedy`,
`group_experiments_clique_removal`, and `measure_observables`. These are aliases
or wrappers around the experiment implementation, not a separate execution
backend. `measure_observables(qc, experiment, progress_callback=None,
calibrate_readout="plus-eig")` supports grouped settings and checks that
calibration is used only with exhaustive symmetrization. It rejects complex
observable coefficients for sampled expectation values. In 4.18.0 there is no
module-level deprecation marker for this import surface; old `measure_observables`
arguments such as `n_shots`, `active_reset`, and legacy symmetrization keyword
forms were removed—set shots/reset/symmetrization on `Program`/`Experiment`
instead.

By contrast, `QuantumComputer.run_experiment(experiment, memory_map=None)`
handles parameterized program construction and execution but currently raises
`ValueError` for groups with more than one setting. Choose the path deliberately:
use singleton settings for `run_experiment`, or use `measure_observables` for
local-TPB grouped estimation with an available backend.

## Result and uncertainty interpretation

`ExperimentResult` stores:

```text
setting, expectation, total_counts, std_err,
raw_expectation, raw_std_err,
calibration_expectation, calibration_std_err, calibration_counts,
additional_results
```

`std_err` is the estimated standard error of the mean, not the single-shot
standard deviation. `bitstrings_to_expectations(bitstrings,
joint_expectations=None)` maps each bit to `1-2*bit`; with a list of subsets it
multiplies the selected eigenvalue columns and returns one expectation column
per subset.

`correct_experiment_result(result, calibration)` computes
`corrected = result.expectation / calibration.expectation` and propagates the
independent-sample ratio variance approximately as

```text
Var(A/B) ≈ Var(A)/b**2 + a**2*Var(B)/b**4.
```

Both results need standard errors. Additional results are corrected recursively
and their list lengths must match. The correction is a model-based estimate;
finite samples can leave corrected values outside `[-1,1]` and do not establish
that a physical device was corrected perfectly.
