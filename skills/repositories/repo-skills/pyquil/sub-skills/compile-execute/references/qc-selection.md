# Quantum-computer selection

Read this when the target is not already fixed, when `get_qc` parses an
unexpected name, or when deciding whether a run needs local services or QCS.
The API facts below were checked against pyQuil 4.18.0 and the repository's
`_quantum_computer.py`, unit name-parsing tests, and getting-started/QC docs.

## `get_qc` contract

Installed signature:

```python
get_qc(
    name: str, *, as_qvm: bool | None = None, noisy: bool | None = None,
    compiler_timeout: float = 30.0, execution_timeout: float = 30.0,
    client_configuration: QCSClient | None = None,
    endpoint_id: str | None = None,
    quilc_client: QuilcClient | None = None,
    qvm_client: QVMClient | None = None,
) -> QuantumComputer
```

`client_configuration` is a `qcs_sdk.QCSClient`; the two client overrides are
`qcs_sdk.compiler.quilc.QuilcClient` and `qcs_sdk.qvm.QVMClient`. Both timeout
values are seconds. `endpoint_id` is meaningful for QPU execution and is
passed into QPU execution options; it is not a replacement for a QVM URL.

The parser removes only terminal suffixes and preserves the processor prefix.
These forms are useful:

| Name | Result | Service/credential boundary |
|---|---|---|
| `9q-square-qvm` | generic 3×3-topology `QVM` | local `quilc` + QVM service |
| `9q-square-noisy-qvm` | generic noisy `QVM` | local `quilc` + QVM service |
| `2q-qvm`, `5q-qvm` | fully connected `QVM` with that many qubits | local `quilc` + QVM service |
| `2q-pyqvm`, `5q-pyqvm` | in-process `PyQVM` on a fully connected topology | no QVM service; `qc.compile` still uses the compiler client |
| `<processor>-qvm` | QVM using a QCS-fetched processor ISA | QCS access for ISA plus local/selected compiler/QVM |
| `<processor>-pyqvm` | in-process PyQVM using a QCS-fetched processor ISA | QCS access for ISA; no QVM service |
| `<processor>` | QPU with that processor ID | QCS settings/credentials and authorized endpoint |

The special `9q-square` topology is only valid as a QVM. A bare numeric
prefix such as `5q` must be forced to a simulator with `as_qvm=True`; a name
with `-qvm` or `-pyqvm` already forces that choice. A normal processor name
without a simulator suffix is treated as a QPU and causes an ISA lookup.

`as_qvm=True` forces QVM construction for a processor name and `noisy=True`
requests a noise model for supported QVM forms. `noisy=False` conflicts with a
`-noisy-qvm`/`-noisy-pyqvm` name; `as_qvm=False` conflicts with a simulator
suffix. Redundant matching flags are accepted. A noisy QCS-hardware-backed
processor is rejected by this version; use a named generic noisy QVM instead.

Useful canonical examples:

```python
from pyquil import get_qc

local = get_qc("9q-square-qvm")
in_process = get_qc("5q-pyqvm")
qvm_like_hardware = get_qc("Aspen-M-3", as_qvm=True)
# A real QPU: only after QCS access, authorization, and endpoint readiness.
# qpu = get_qc("Aspen-M-3", endpoint_id="approved-endpoint")
```

Do not infer that a processor name exists merely because it parses. Use
`list_quantum_computers()` to list QCS-visible processors (that can make a
remote request for QPUs); the built-in local QVM names are always the two
`9q-square` names when `qpus=False`.

## What a `QuantumComputer` contains

`QuantumComputer(name=..., qam=..., compiler=..., symmetrize_readout=False)`
wraps three compatible components:

- `.qam`: the execution implementation, normally `QVM`, `QPU`, or `PyQVM`.
- `.compiler`: `QVMCompiler` for QVM/PyQVM construction or `QPUCompiler` for
  a QPU. It owns the compiler client and target processor.
- `.quantum_processor`: a property forwarding to
  `qc.compiler.quantum_processor`; it supplies qubits, topology, and compiler
  ISA. `qc.qubits()`, `qc.qubit_topology()`, and `qc.to_compiler_isa()` expose
  the corresponding views.

Check types before using backend-only behavior:

```python
from pyquil.api import QPU, QPUCompiler

if isinstance(qc.qam, QPU):
    handle = qc.qam.execute(executable)
    # A QPU handle can be cancelled while pending.
    qc.qam.cancel(handle)
if isinstance(qc.compiler, QPUCompiler):
    calibration_program = qc.compiler.get_calibration_program()
```

`QPU.cancel` is not a QVM method. `QPUCompiler.get_calibration_program()`
fetches and caches QPU Quil-T calibrations; `force_refresh=True` performs a
new fetch, and the returned cached `Program` should be copied before mutation.
These are QPU/QCS operations, not local proof of a compiler or hardware.

## Backend decision table

| Need | Select | Stop/verify boundary |
|---|---|---|
| deterministic local numerical reasoning | route to `simulation` and use PyQVM/reference APIs | do not call this route's service QVM smoke test |
| same compiled workflow as a service QVM | `*-qvm` | both compiler and QVM endpoints must be reachable |
| no QVM daemon, lightweight in-process execution | `*-pyqvm` | PyQVM has different feature/batch limits; compile may still require quilc |
| hardware-shaped QVM | `<processor>-qvm` or `as_qvm=True` | QCS ISA lookup and local/selected services are still required |
| real hardware | bare processor name | require QCS settings/secrets, authorization/reservation or endpoint, and execution policy |

`local_forest_runtime()` is a separate opt-in context manager that can start
`qvm` and `quilc` subprocesses. It checks ports, starts only missing local
processes, and terminates only processes it started. It raises
`FileNotFoundError` when either binary is absent. Do not use it in diagnostics
or unattended helpers unless process startup is explicitly authorized; the
bundled checks intentionally never start services.
