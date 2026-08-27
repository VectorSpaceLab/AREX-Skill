# Results, memory maps, and batching

Read this when a program has runtime parameters, when batching a compiled
executable, or when a result's shape is surprising. The API details come from
`api/_qam.py`, `_qpu.py`, `pyqvm.py`, v4 parameter/raw-data docs, and QPU/QVM
unit tests. Installed signatures were checked against pyQuil 4.18.0.

## Runtime memory maps

The `MemoryMap` type is a mapping from region name to a sequence of integers or
floats:

```python
MemoryMap = Mapping[str, Sequence[int] | Sequence[float]]
```

Every value is a sequence, including a one-cell region. The region must have
been declared by the program and its name/type/width must match the executable.
A scalar such as `{"theta": 0.5}` is invalid; use `{"theta": [0.5]}`. Keep
parameter units and register widths explicit:

```python
program = Program()
theta = program.declare("theta", "REAL", 1)
ro = program.declare("ro", "BIT", 1)
program += RX(theta[0], 0)
program += MEASURE(0, ro[0])
program.wrap_in_numshots_loop(32)

executable = qc.compile(program)
result = qc.run(executable, memory_map={"theta": [0.25]})
```

Compile once when only declared runtime values change. Do not mutate the
program's declarations or the compiled executable to update parameters.
Validate before submit:

- every map key is a declared runtime region;
- each value is a sequence, not a scalar;
- the sequence length fits the declared region and uses the declared numeric
  type (`BIT`/integer-like versus `REAL`/floating-point);
- map values have the same semantic shape across a batch;
- readout declarations and `num_shots` are known before checking results.

The QVM/QPU service performs the final validation, so a local pre-check is a
helpful error message, not a substitute for backend validation.

## Single and split-phase calls

The exact high-level methods are:

```python
qc.run(executable, memory_map=None, **kwargs) -> QAMExecutionResult
qc.run_with_memory_map_batch(executable, memory_maps, **kwargs) -> list[QAMExecutionResult]
```

The lower-level equivalents are `qc.qam.execute`,
`qc.qam.execute_with_memory_map_batch`, and `qc.qam.get_result`. `QAM.run`
implements `get_result(execute(...))`.

For a service-backed QVM, the batch implementation is a convenience loop and
is not more efficient than separate requests. For a QPU, submission is a
parameter batch through QCS and the returned handles/results preserve the
length and order of the `memory_maps` input. For `PyQVM`, the installed
implementation raises `NotImplementedError` for batch execution because its
state resets at the start of each execution. Use independent single runs for
PyQVM or route simulation-specific work to [simulation](../../simulation/SKILL.md).

A strict service-QVM/QPU batch consumer should look conceptually like:

```python
memory_maps = [{"theta": [value]} for value in values]
results = qc.run_with_memory_map_batch(executable, memory_maps)
assert len(results) == len(memory_maps)
for index, result in enumerate(results):
    registers = result.get_register_map()
    ro = registers.get("ro")
    assert ro is not None and ro.shape == (shots, readout_width)
    # Associate this result with memory_maps[index], never by sorting output.
```

When concurrency rather than backend batching is required, use
`execute`/`get_result` or a bounded thread pool as described in
[configuration.md](configuration.md). Copy non-thread-safe programs and
encrypted executables before concurrent use.

## `QAMExecutionResult`

Installed constructor:

```python
QAMExecutionResult(executable: QuantumExecutable, data: ExecutionData)
```

Use these accessors:

- `get_register_map() -> dict[str, np.ndarray | None]`: maps region names such
  as `"ro"` to rectangular NumPy matrices. For ordinary shot-based QVM data,
  `ro.shape` is `(num_shots, declared_width)`. A region can be `None` when no
  corresponding result is available.
- `get_raw_readout_data()`: returns QCS SDK raw QVM or QPU readout data. Use it
  when measurements can be repeated, skipped, or emitted by dynamic control
  flow, or when a QPU result is jagged.
- `get_memory_values()`: returns final QPU memory values for regions both read
  and written during execution. It is `{}` for QVM data and is **not** shot
  readout data.
- `execution_duration_microseconds`: a float or `None`; it reports the QPU
  exclusive hardware duration when provided. QVM/PyQVM results normally have
  `None`.
- `readout_data`: deprecated compatibility property equivalent to
  `get_register_map()`. Prefer the explicit method.

A rectangular conversion can succeed even when the program reused a memory
reference more than once per shot in a way that happens to form a matrix.
Therefore choose raw data based on program semantics, not only on whether a
conversion exception occurred.

## Raw versus register interpretation

For ordinary measurement code:

```python
registers = result.get_register_map()
ro = registers.get("ro")
if ro is None or ro.ndim != 2:
    raise ValueError("expected a rectangular ro register")
shots, width = ro.shape
assert width == expected_width
```

For QPU dynamic control flow or repeated measurements, catch
`qcs_sdk.RegisterMatrixConversionError` and inspect:

```python
raw = result.get_raw_readout_data()
# Use raw.mappings/readout_values according to the QVM/QPU raw type.
```

Build a domain-specific ragged representation from raw data; do not pad or
reshape it without a rule tied to the program's control flow. `get_memory_values`
is useful for final classical memory inspection only.

## Encrypted QPU executable boundary

A QPU result's `result.executable` is an `EncryptedProgram`. Its `.program` is
opaque translated representation, not source Quil or printable native output.
Do not try to deserialize it as a QVM `Program`, inspect it for gates, or submit
it to `QVM`. Recompile for a QVM target when a readable native executable or
local validation is needed. QPU compilation and result retrieval remain QCS
operations even when the Python object was constructed successfully.
