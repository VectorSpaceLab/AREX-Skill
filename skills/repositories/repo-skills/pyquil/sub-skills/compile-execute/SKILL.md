---
name: compile-execute
description: "Select a pyQuil quantum computer, compile and execute programs,
  batch parameter maps, inspect QAM results, configure QVM/QPU endpoints, and
  recover from service or compiler failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Compile and execute

Use this route when the task mentions `get_qc`, `QuantumComputer.compile`,
`qc.run`, `execute`/`get_result`, QVM, QPU, quilc, QCS settings, endpoints,
reservations, memory maps, batch execution, timeouts, or connection errors.
This skill owns the **compiled executable → QAM → result** lifecycle; it does
not own Quil construction or numerical state analysis.

## Route first

1. Read [qc-selection.md](references/qc-selection.md) when choosing a target,
   interpreting `get_qc` names/flags, or deciding between PyQVM, service QVM,
   and QPU.
2. Read [compile-and-run.md](references/compile-and-run.md) for compilation
   stages, compiler classes, protoquil, metadata, PRAGMAs, and the exact run
   lifecycle.
3. Read [configuration.md](references/configuration.md) before changing URLs,
   QCS profiles, timeouts, clients, endpoint IDs, or concurrency.
4. Read [results-and-batching.md](references/results-and-batching.md) when
   consuming register/raw/memory/duration data or reusing an executable with
   parameter maps.
5. Read [troubleshooting.md](references/troubleshooting.md) after any compiler,
   service, configuration, credential, shape, or backend-specific error.
6. Run `scripts/check_services.py --help` for safe diagnostics. It never starts
   services and does not make network requests unless explicitly requested.
   Run `scripts/qvm_bell_smoke.py --help`; execute it only with the explicit
   `--execute` opt-in after a local QVM and quilc are known to be available.

For program syntax, declarations, measurements, placeholders, and Quil-T,
route to [program-authoring](../program-authoring/SKILL.md). For statevectors,
PyQVM numerical behavior, and service-free simulation, route to
[simulation](../simulation/SKILL.md). For noise/Experiment workflows, route to
[noise-experiments](../noise-experiments/SKILL.md). For topology or ISA
construction, route to [processor-isa](../processor-isa/SKILL.md).

## Non-negotiable lifecycle

1. Build and validate a `Program` using the authoring route.
2. Select a target with `get_qc(...)`; record whether `.qam` is `QVM`, `QPU`,
   or `PyQVM`, and whether `.compiler` is `QVMCompiler` or `QPUCompiler`.
3. For service-backed QVM or QPU, call `executable = qc.compile(program)`.
   `qc.compile` performs native Quil compilation and executable translation.
4. Supply only the compiled `QuantumExecutable` to `qc.run(executable, ...)`,
   or use `qc.qam.execute(...)` followed by `qc.qam.get_result(handle)` when
   asynchronous control is needed. Do not pass an uncompiled high-level
   program to a QPU; a standard `QVM` also requires a `Program` executable,
   but the high-level `qc.compile` path is the portable choice.
5. Validate the returned register names and shapes before interpreting data.
   Use raw readout data rather than forcing a rectangular matrix for dynamic
   control flow or QPU qubit reuse.

`get_qc` and the execution methods have exact installed signatures; see the
linked references rather than guessing keyword names. Compilation and execution
are network/service operations unless the chosen QAM is explicitly in-process.
No helper in this sub-skill proves that a QVM, quilc, QPU, reservation, or QCS
credential is available.

## Minimal pattern

```python
from pyquil import Program, get_qc
from pyquil.gates import H, CNOT, MEASURE

program = Program()
ro = program.declare("ro", "BIT", 2)
program += [H(0), CNOT(0, 1), MEASURE(0, ro[0]), MEASURE(1, ro[1])]
program.wrap_in_numshots_loop(100)

qc = get_qc("9q-square-qvm")
executable = qc.compile(program)       # requires quilc for this target
result = qc.run(executable)            # requires QVM service
bits = result.get_register_map()["ro"]
assert bits.shape == (100, 2)
assert (bits[:, 0] == bits[:, 1]).all()
```

For a local QVM smoke test with bounded failure behavior, use the bundled
`qvm_bell_smoke.py`; it deliberately does not use QCS credentials or start
`qvm`/`quilc`. For service/config presence checks, use `check_services.py`.
