---
name: noise-experiments
description: "Construct and validate PyQuil noise channels, readout corrections,
  Pauli observables, and experiment settings while keeping model construction
  separate from backend execution."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Noise experiments

Use this sub-skill when the task involves any of the following:

- Kraus gate noise, assignment/readout matrices, decoherence, or noise pragmas.
- `PauliTerm`/`PauliSum` algebra, grouping, exponentiation, or observable bases.
- `ExperimentSetting`, `Experiment`, calibration, readout symmetrization, or
  `ExperimentResult` interpretation.
- Preparing an experiment for a `QuantumComputer` without claiming that a QVM,
  QPU, QCS, or other service was reached.

## Route before acting

- Constructing or inspecting a `Program`, gates, declarations, measurements, or
  Quil text belongs in [program-authoring](../program-authoring/SKILL.md).
- Compiling, submitting jobs, configuring QVM/QPU/QCS clients, or consuming raw
  QAM results belongs in [compile-execute](../compile-execute/SKILL.md).
- Statevector/density-matrix simulation and numerical simulator internals belong
  in [simulation](../simulation/SKILL.md).
- Processor topology and ISA construction belongs in
  [processor-isa](../processor-isa/SKILL.md).

Read [noise-models.md](references/noise-models.md) for API selection, shapes,
channel formulas, and the legacy/new boundary. Read
[pauli-and-experiment-api.md](references/pauli-and-experiment-api.md) for exact
object contracts. Read [workflows.md](references/workflows.md) before composing
a model or experiment. Use [troubleshooting.md](references/troubleshooting.md)
when a validation or execution boundary fails.

## Core operating rules

1. Treat `pyquil.noise.KrausModel` and `pyquil.noise.NoiseModel` as the
   supported public, legacy Kraus/QVM surface in 4.18.0. A model contains
   definitions; it is not evidence that any backend executed them.
2. Build a map with square complex operators. For `n` qubits each operator is
   `(2**n, 2**n)` and a trace-preserving map satisfies
   `sum(K.conj().T @ K) = eye(2**n)`. Check this before attaching pragmas.
3. `tensor_kraus_maps(k1, k2)` combines independent maps on different qubits;
   `combine_kraus_maps(k1, k2)` composes maps on the same qubits with `k2`
   first and `k1` second. `append_kraus_to_gate` post-multiplies a gate by each
   Kraus operator (`K @ U`).
4. `apply_noise_model(program, model)` returns a new transformed `Program` with
   definitions and `PRAGMA ADD-KRAUS`/`READOUT-POVM` headers. Inspect its Quil;
   do not call this transformation a run or a physical calibration.
5. Keep the two legacy readout representations distinct. A
   `READOUT-POVM`/`estimate_assignment_probs` conditional matrix is laid out as
   `[[p00, 1-p11], [1-p00, p11]]` (observed rows, prepared columns), while the
   legacy `NoiseModel.assignment_probs` produced by decoherence helpers stores
   `[[p00, 1-p00], [1-p11, p11]]` and the header reconstructs the POVM from its
   diagonals. The probability tensor has one length-2 axis per measured bit in
   the same order as the shot columns.
6. Pauli coefficients used for measured expectations must be real. Bits map to
   eigenvalues as `0 -> +1` and `1 -> -1`; an `n`-bit joint expectation is the
   product over selected columns.
7. `Experiment` defaults to exhaustive symmetrization and plus-eigenstate
   calibration. These increase backend work. Explicitly choose `shots`, the
   symmetrization level, and calibration policy for reproducibility.
8. In 4.18.0 `QuantumComputer.run_experiment` compiles and executes through its
   configured backend and rejects grouped settings (`len(settings) > 1`).
   `pyquil.operator_estimation.measure_observables` remains importable and can
   process grouped settings, but still needs a usable `QuantumComputer` and
   backend. Stop at the service boundary if those are unavailable.

## Minimal local validation

For a service-free smoke check, run the bundled helper when you need to validate
Kraus completeness, readout tensor correction, and transformed Quil:

```bash
python scripts/noise_model_smoke.py --help
python scripts/noise_model_smoke.py
```

The helper uses tiny deterministic arrays and a two-qubit `Program`; it never
starts a service, reads credentials, compiles, submits, or downloads anything.
Its successful output proves construction/transformation only. For a detailed
manual workflow, use [workflows.md](references/workflows.md).

## Handoff checklist

Before handing an operating plan to another agent, record:

- model family (legacy public Kraus versus private/new quax channel), channel
  dimensions, completeness/CP-TP checks, and qubit/operand ordering;
- supported gate/parameter matches and whether noise was applied once or twice;
- which legacy readout representation is in use (internal
  `NoiseModel.assignment_probs` versus POVM/calibration matrix), axis/qubit
  ordering, correction conditioning, shot count, and any negative or
  out-of-range corrected probabilities;
- Pauli settings, grouping method, compatible preparation/measurement bases,
  symmetrization level and trial expansion, calibration denominator, and result
  uncertainty;
- exact next execution owner and missing QVM/QPU/QCS/compiler credentials or
  services. Never report a constructed model or generated `Program` as an
  executed experiment.
