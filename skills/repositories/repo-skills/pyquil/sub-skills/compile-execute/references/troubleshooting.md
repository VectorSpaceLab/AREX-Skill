# Compile/execute troubleshooting

Use the symptom and recovery table before retrying. Keep failures classified as
local Python/API, compiler service, QVM service, QCS configuration, or QPU
authorization. A successful import, `get_qc` object, or compile request does
not prove a live service or QPU run.

| Symptom | Likely cause | Recovery and stop condition |
|---|---|---|
| `ValueError` says a QVM name conflicts with `as_qvm=False` or `noisy=False` | Name suffix and explicit flag disagree | Remove the conflicting flag or choose a canonical `*-qvm`/`*-pyqvm` name; do not retry a different backend accidentally. |
| `ValueError` says `9q-square` is only available as a QVM | Special generic topology was requested as QPU | Add `-qvm`/`-pyqvm` or choose an actual processor ID. |
| Unknown processor / ISA lookup failure | Bare name is interpreted as QPU, or QCS cannot find the processor | Verify the processor ID with a QCS-visible listing and active profile. Stop at missing QCS access; do not infer availability from the name grammar. |
| `qc.run(program)` fails after a normal QVM/QPU workflow | The high-level `Program` was not compiled for the target | Use `executable = qc.compile(program)` followed by `qc.run(executable)`. An in-process PyQVM has separate direct-Program semantics. |
| `QVMNotRunning`, connection refused, or no QVM response | `qvm` is absent, not in server mode, wrong QVM URL, or blocked port | Run `check_services.py` first. Start/repair the service through an authorized supervisor, or explicitly use a known QVM URL/client. The helper never starts services. |
| compiler request hangs/times out | `quilc` is absent/unreachable, compiler URL is wrong, or program is large | Check `tcp://` URL and port, confirm service separately, try a small program, then raise `compiler_timeout`. Do not treat a larger timeout as service proof. |
| `QuilcNotRunning` or compiler timeout | Compiler endpoint timed out or returned too slowly | Confirm `QCS_SETTINGS_APPLICATIONS_QUILC_URL`/profile, probe only with explicit network opt-in, then fix service or increase timeout. |
| `QuilcVersionMismatch` / compiler says version too old | `quilc` major/minor is incompatible with pyQuil | Obtain a compatible Forest/quilc version and rerun the version check. Do not suppress the mismatch or claim native output is valid. |
| `QVMVersionMismatch` | QVM is older than the supported compatibility floor | Upgrade/restart QVM and record both versions. A Python package version does not upgrade a separately installed daemon. |
| QVM URL validation/HTTP error | URL is malformed, wrong scheme/port, or endpoint is not a QVM | Use an HTTP QVM URL such as `http://127.0.0.1:5000`; use `tcp://...` only for quilc. Confirm no proxy or service mismatch. |
| `FileNotFoundError` in `local_forest_runtime` | `qvm` or `quilc` executable is not installed | Install the Forest SDK or run externally managed services. Do not add a service-start call to a safe diagnostic. |
| `local_forest_runtime` warns that a port is in use | Another process owns the port | Verify that process and endpoint; only the context manager's own children are terminated. Do not kill an unrelated service. |
| QPU authentication/credentials/settings error | Missing settings/secrets, wrong active profile, expired credential, or unauthorized account | Check only config presence and active profile, refresh credentials through the supported QCS procedure, and stop if no authorization/reservation exists. Never print or copy secrets into logs. |
| QPU times out or reservation/engagement is missing | Unsupported environment, no reservation, unavailable gateway/direct-access policy, or service outage | Verify account, reservation/engagement, endpoint policy, and execution environment. Increase `execution_timeout` only after these checks; do not loop indefinitely. |
| `endpoint_id` job is rejected or results are not meaningful | Endpoint is unknown, not enabled for the account, or is a mock/test service | Confirm the exact endpoint with QCS. Endpoint selection changes execution service; it does not grant access or establish scientific validity. |
| `QPU#execute requires an rpcq.EncryptedProgram` | A QVM `Program` or wrong executable was sent to QPU | Compile with a `QPU`/`QPUCompiler` target and submit that executable. Do not convert opaque encrypted text manually. |
| QPU executable prints as encrypted/opaque text | Expected QPU translation representation | Inspect native Quil before QPU translation, or compile for a QVM for readable local output. Do not parse encrypted `.program`. |
| `QPU`-only method missing on QVM | Called `cancel`, QPU calibration, or QPU options on a QVM | Check `isinstance(qc.qam, QPU)` / `isinstance(qc.compiler, QPUCompiler)` and route appropriately. |
| `ValueError` on mixed `to_native_gates`/`optimize` | Only one compile flag was disabled | Set both true (normal compile) or both false (already-native expert path). |
| compiler rejects `DEFGATE`, PRAGMA, or protoquil input | Program is outside target ISA/legality or a compiler hint is wrong | Route syntax to program-authoring, inspect native output and metadata, remove/fix unsafe preserve/commuting claims, or compile with an appropriate protoquil setting. |
| memory-map key rejected / undeclared region | Map name differs from a `DECLARE` region | Compare exact declaration names and executable descriptors; use a mapping such as `{"theta": [0.25]}`. |
| memory-map type/shape error | Scalar supplied, wrong numeric type, or sequence width mismatched | Values must be sequences of ints/floats and match region type/width. Validate every map before batch submission. |
| batch result count/order is wrong | Caller discarded input ordering or backend failure was hidden | Assert `len(results) == len(memory_maps)` and associate by index. Inspect per-result errors; do not sort by a backend handle. |
| `NotImplementedError` says PyQVM does not support batch execution | PyQVM resets state per execution | Run independent single executions on copied programs or use a service-backed QVM/QPU for backend batch semantics. |
| `RegisterMatrixConversionError` / jagged register | Dynamic control flow or QPU repeated/conditional measurements | Use `get_raw_readout_data()` and construct a ragged/domain-specific representation. Do not blindly reshape/pad. |
| rectangular `ro` has unexpected dimensions | Wrong shots, declaration width, or a program that writes a region differently | Check `wrap_in_numshots_loop`, declaration width, measurement addresses, and `ro.shape == (shots, width)` before analysis. |
| `get_memory_values()` is empty on QVM | Final-memory accessor is QPU-oriented | Use `get_register_map()`/raw data for readout; QVM duration and memory-values may be unavailable by design. |
| concurrent runs corrupt results or parameters | Shared `Program`/`EncryptedProgram` was mutated or reused unsafely | Share `QuantumComputer` if desired, but copy programs/executables per worker and never mutate compiler/QAM configuration concurrently. |
| diagnostics output contains too much environment detail | `pyquil.diagnostics.get_report()` is a diagnostic artifact, not a secret scrubber | Review and redact before sharing; never include secrets, tokens, full paths, or private config content. |

## A bounded diagnostic order

1. Run `python scripts/check_services.py` with no network flag. Confirm package
   import, binary presence, config path presence, and URL environment names.
2. If authorized, run `python scripts/check_services.py --probe-network` with
   explicit `--qvm-url`/`--quilc-url` or known safe defaults. This performs only
   bounded socket/HTTP reachability probes; it does not execute Quil or start
   processes.
3. Run the smallest possible program through the selected path. For service
   QVM, compile and run a one-qubit measurement. For PyQVM, use the simulation
   route if the purpose is numerical state validation.
4. For QPU, stop after a precise configuration/authorization boundary unless
   the user has explicitly authorized a real submission. Use an alternate
   endpoint only when its ID and semantics are known.
5. Collect `pyquil.diagnostics.get_report()` and versions only after removing
   credentials, secrets, private paths, and unrelated machine details.

## Version and source boundaries

`pyquil.diagnostics.get_report()` delegates to QCS SDK diagnostics and its
format is not stable. `QVM` checks its server version on construction; the
compiler checks quilc version before compilation. Neither check proves a QPU
reservation. If a version mismatch persists after upgrade, compare the actual
service binary version with the installed pyQuil/QCS SDK version rather than
reinstalling only the Python package.
