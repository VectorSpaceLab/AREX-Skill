# Configuration, endpoints, and concurrency

Read this before altering QCS settings, URL overrides, client objects,
timeouts, alternative endpoints, or parallel execution. The facts below are
from `advanced_usage.rst`, `_compiler_client.py`, `_qpu.py`, `_qvm.py`,
`_quantum_computer.py`, and installed `qcs_sdk` signatures/stubs.

## QCS client loading

APIs such as `get_qc` load `QCSClient.load()` when no
`client_configuration` is supplied. The documented configuration locations
are:

- settings: `$HOME/.qcs/settings.toml`
- secrets: `$HOME/.qcs/secrets.toml`

Override paths with `QCS_SETTINGS_FILE_PATH` and
`QCS_SECRETS_FILE_PATH`. A profile can supply
`profiles.<profile>.applications.pyquil.qvm_url` and
`profiles.<profile>.applications.pyquil.quilc_url`. The active profile can be
selected using the QCS SDK's `QCSClient.load(profile_name=...)` API.

URL-only overrides are:

```text
QCS_SETTINGS_APPLICATIONS_QVM_URL=http://127.0.0.1:5000
QCS_SETTINGS_APPLICATIONS_QUILC_URL=tcp://127.0.0.1:5555
```

If neither settings nor overrides provide them, those are the documented local
defaults. The compiler client validates that `quilc_url` starts with `tcp://`;
a URL such as `http://...` produces a `ValueError`. QVM URLs are HTTP URLs for
`QVMClient.new_http`. Do not put secrets in URL environment variables or
commit settings/secrets files.

The bundled `scripts/check_services.py` reports only whether config paths and
non-secret environment variable names are present, plus redacted URL
scheme/host/port information. It never prints settings or secrets contents.

For tests, diagnostics, and deliberately credential-free local behavior, build
an explicit client configuration instead of implicitly loading the user's QCS
profile:

```python
from qcs_sdk import QCSClient

client = QCSClient(
    qvm_url="http://127.0.0.1:5000",
    quilc_url="tcp://127.0.0.1:5555",
)
```

Pass this as `client_configuration=client`, and pass explicit
`QVMClient.new_http(client.qvm_url)`/`QuilcClient.new_rpcq(client.quilc_url)`
when needed. This avoids silently selecting a different profile; it does not
make unavailable services available.

## Timeout ownership

`get_qc` defaults `compiler_timeout=30.0` and `execution_timeout=30.0`.
These values are passed to the compiler and QAM construction. Direct `QVM`
construction has a `timeout=10.0` default. Direct `QPU` construction has
`timeout=30.0 | None`, `priority=1`, optional `endpoint_id`, and optional
`execution_options`.

Increase a timeout only after checking endpoint reachability and program size:

```python
qc = get_qc(
    "9q-square-qvm",
    compiler_timeout=60.0,
    execution_timeout=60.0,
    client_configuration=client,
)
```

A timeout is not evidence of a long-running valid job. Capture the target,
URLs (redacted), pyQuil/QVM/quilc versions, and diagnostics, then distinguish
compile timeout from execution timeout. See
[troubleshooting.md](troubleshooting.md).

## QPU endpoint semantics

`get_qc("processor-id", endpoint_id="endpoint-id")` places the endpoint ID in
the QPU's execution configuration. The equivalent lower-level construction is
`QPU(quantum_processor_id="processor-id", endpoint_id="endpoint-id")`.
For an explicitly constructed QPU, an `execution_options` object takes
precedence over the constructor's `timeout` and `endpoint_id`.

An alternate endpoint routes execution to another QCS service associated with
the processor architecture. It does **not** turn a QVM into a QPU, bypass QPU
authorization, or guarantee scientifically meaningful results. The endpoint
must be valid for the account and execution environment. Follow the endpoint's
service policy and do not guess an ID.

For per-request QPU control:

```python
from pyquil.api import ConnectionStrategy, ExecutionOptionsBuilder

builder = ExecutionOptionsBuilder()
builder.timeout_seconds = 60.0
builder.connection_strategy = ConnectionStrategy.endpoint_id("approved-endpoint")
options = builder.build()
result = qc.run(executable, execution_options=options)
```

`ConnectionStrategy.direct_access()` is a QCS policy choice for direct access;
it does not create a reservation or credentials. Keep QPU credentials out of
scripts and logs. A missing reservation, engagement, gateway access, or
credential is a stop condition, not a reason to retry indefinitely.

## Client injection and libquil boundary

`quilc_client` and `qvm_client` let callers inject SDK clients. Installed
inspection confirms `QuilcClient.new_rpcq(endpoint)` and
`QVMClient.new_http(endpoint)`. The QVM SDK may expose `new_libquil()` when the
optional libquil build is available; the inspected `QuilcClient` did not expose
a corresponding `new_libquil()` factory in this version. Treat libquil as an
optional, platform-dependent alternative and verify its actual SDK API before
using it. Do not claim that an optional library is installed from pyQuil's
import alone.

## Concurrency and object ownership

The documented concurrency contract is:

- `QuantumComputer` objects are safe to share between threads for concurrent
  execute/retrieve operations.
- `Program` and `EncryptedProgram` are **not** thread-safe. Copy them before
  concurrent use (`program.copy()` or `encrypted_program.copy()`). Do not
  mutate declarations, instructions, compiler options, or a shared executable
  while another thread uses it.
- pyQuil has no asyncio API in the documented workflow; a thread pool is the
  supported pattern. QVM requests are processed in parallel. QPU parallelism
  depends on qubits/service scheduling, and large concurrent sets may need a
  larger `execution_timeout`.
- Keep at least two units of desired parallelism only when the service/account
  permits it; do not turn this recommendation into unbounded submissions.

Safe shape:

```python
from multiprocessing.pool import ThreadPool

base = program.copy()
def one_run(memory_map):
    local_program = base.copy()
    executable = qc.compile(local_program)
    return qc.run(executable, memory_map=memory_map)

with ThreadPool(2) as pool:
    results = pool.map(one_run, [{"theta": [0.0]}, {"theta": [1.0]}])
```

If compilation is expensive and the executable is immutable for the target,
compile once, then give each thread its own copied `Program`/`EncryptedProgram`
where the backend requires it. Keep the mapping between input parameters and
result order explicit.
