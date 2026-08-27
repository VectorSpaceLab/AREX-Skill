# Compilation and execution

Read this for the compile-before-run contract, compiler controls, native Quil,
metadata, and QVM/QPU implementation differences. Source intent comes from
`api/_abstract_compiler.py`, `api/_compiler.py`, `api/_qvm.py`, `api/_qpu.py`,
the compiler/getting-started docs, and compiler tests. Installed signatures were
checked directly.

## The two compilation stages

`QuantumComputer.compile` has this installed signature:

```python
qc.compile(
    program: Program,
    to_native_gates: bool = True,
    optimize: bool = True,
    *,
    protoquil: bool | None = None,
) -> QuantumExecutable
```

`QuantumExecutable` is the union of a native `Program` and an
`EncryptedProgram`. With the default flags, pyQuil does:

1. `qc.compiler.quil_to_native_quil(program, protoquil=protoquil)` through
   the configured quilc client. This converts general Quil to the target ISA,
   may optimize and rewire, and may attach `native_quil_metadata`.
2. `qc.compiler.native_quil_to_executable(native_program)`. A `QVMCompiler`
   returns the native `Program`; a `QPUCompiler` translates it to an opaque
   `EncryptedProgram`.

Compile first, then run the returned object:

```python
executable = qc.compile(program, protoquil=None)
result = qc.run(executable, memory_map={"theta": [0.25]})
```

`protoquil=None` defers to the compiler server. `True` asks for a protoquil
input/output restriction suitable for QPU execution; `False` disables that
restriction. The compiler server's own `-P` mode can affect the deferred case.
Do not claim a program is QPU-compatible just because local compilation
returned; verify its target ISA and protoquil constraints.

`to_native_gates` and `optimize` must be both true or both false. Mixed values
raise `ValueError("Must turn to_native_gates and optimize on or off together")`.
Turning both off skips quilc in `QuantumComputer.compile` and hands the input
program to `native_quil_to_executable`; this is an expert path for already
native Quil, not a way to bypass target compatibility.

For stage-level inspection:

```python
native = qc.compiler.quil_to_native_quil(program, protoquil=True)
metadata = native.native_quil_metadata  # may be None
executable = qc.compiler.native_quil_to_executable(native)
```

The abstract compiler signature is
`quil_to_native_quil(program, *, protoquil=None)`. QVM compiler construction
uses `QVMCompiler(quantum_processor=..., timeout=10.0,
client_configuration=None, quilc_client=None)`; QPU compiler construction uses
`QPUCompiler(quantum_processor_id=..., quantum_processor=..., timeout=10.0,
client_configuration=None, api_options=None, quilc_client=None)`.

## Native output and metadata

A QVM executable is printable native Quil. A QPU executable is an
`EncryptedProgram` with these data fields:

- `program`: opaque translated program text; do not parse or print it as useful
  native Quil, and do not persist or share it as if it were source.
- `memory_descriptors`: declared region names and `ParameterSpec` type/length.
- `ro_sources`: mapping from `MemoryReference` to translated readout source.
- `copy()`: returns a separate dataclass wrapper for safe independent use;
  treat its contained descriptors and opaque program as immutable values.

For native compiler metadata, the installed `NativeQuilMetadata` fields are
`final_rewiring`, `gate_depth`, `gate_volume`, `multiqubit_gate_depth`,
`program_duration`, `program_fidelity`, `qpu_runtime_estimation`, and
`topological_swaps`. Values may be `None`; metadata is an estimate/description
of compilation, not measured hardware performance. `final_rewiring` describes
logical-to-physical relabeling; topology/ISA ownership belongs to
[processor-isa](../../processor-isa/SKILL.md).

`QPUCompiler.native_quil_to_executable(native_program, *, api_options=None,
**kwargs)` accepts `QPUCompilerAPIOptions`, an alias of the QCS SDK translation
options. A per-call `api_options` overrides `qc.compiler.api_options`. The
translation backend is selected by processor ID: Aspen targets use V1 and
later targets use V2; an incompatible explicit choice is changed with
`IncompatibleBackendForQuantumProcessorIDWarning`.

## PRAGMAs and compilation boundaries

PRAGMAs are part of the input `Program`; program syntax belongs to the
[program-authoring](../../program-authoring/SKILL.md) route. At execution
planning time, remember:

- `PRAGMA PRESERVE_BLOCK`/`END_PRESERVE_BLOCK` asks the compiler not to modify
  the enclosed instructions. The block must still be legal for the target.
- `PRAGMA COMMUTING_BLOCKS` with `BLOCK`/`END_BLOCK` supplies scheduling hints;
  an incorrect commutation claim can change results.
- `PRAGMA INITIAL_REWIRING "NAIVE|RANDOM|PARTIAL|GREEDY"` changes initial
  logical-to-physical allocation. `PARTIAL` generally favors fidelity,
  `NAIVE` preserves labels where possible, and `GREEDY` favors faster mapping.

Inspect the native program and metadata when a topology mismatch, unexpected
SWAP, or execution fidelity concern matters. Do not assume a `CZ` in the
source remains a `CZ` in native output.

## QVM, PyQVM, and QPU execution

`QAM` defines these methods:

```python
execute(executable, memory_map=None, **kwargs) -> handle
execute_with_memory_map_batch(executable, memory_maps, **kwargs) -> list[handle]
get_result(handle) -> QAMExecutionResult
run(executable, memory_map=None, **kwargs) -> QAMExecutionResult
```

`run` is exactly the synchronous `get_result(execute(...))` convenience. Use
`execute`/`get_result` when submission and retrieval need to be separated or
when QPU cancellation/concurrency matters.

- `QVM` accepts a `Program`, sends it to the configured QVM HTTP endpoint, and
  checks the server version during construction. Its batch method is a
  convenience loop over individual requests and is not more efficient than
  separate requests. Its `timeout` applies to QVM requests.
- `PyQVM` executes `Program` objects in-process and resets state on every
  `execute`; the installed implementation raises `NotImplementedError` for
  `execute_with_memory_map_batch` because batch execution conflicts with that
  reset model. Use a loop of independent copies or route numerical/state tasks
  to [simulation](../../simulation/SKILL.md).
- `QPU` requires an `EncryptedProgram`. It submits through QCS, returns a
  `QPUExecuteResponse` job descriptor, and retrieves results later. Its batch
  API returns handles in the same length/order as the input memory maps. A QPU
  handle can be passed to `cancel`, best effort, only while cancellation is
  possible.

A service-backed QVM smoke run needs both `quilc` and `qvm`; pyQuil does not
ship those executables in this checkout. A successful Python import or object
construction is not proof of either service. The bundled
`scripts/qvm_bell_smoke.py` reports this boundary explicitly.

## Local services

The documented local defaults are QVM `http://127.0.0.1:5000` and quilc
`tcp://127.0.0.1:5555`. `local_forest_runtime(host=..., qvm_port=5000,
quilc_port=5555, use_protoquil=False)` can launch `qvm -S` and `quilc` itself,
but only after the Forest SDK binaries are installed. If a port is occupied,
the context manager warns and does not start that process; it terminates only
processes it started. Prefer an explicit terminal/service supervisor when
reproducibility or process ownership matters.
