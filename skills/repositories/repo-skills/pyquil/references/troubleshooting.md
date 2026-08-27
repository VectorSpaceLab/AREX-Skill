# PyQuil Troubleshooting

Read this reference after an import, API, configuration, compiler, simulator,
noise, or backend failure. First identify whether the symptom is local Python
behavior, a service boundary, or a credential/hardware boundary.

| Symptom | Likely cause | Recovery |
|---|---|---|
| `ModuleNotFoundError` or compiled dependency import failure | Unsupported Python/platform, incomplete install, or a Rust-backed wheel unavailable | Use an isolated supported Python 3.11/3.12 environment, reinstall `pyquil`, inspect the first missing distribution, and use the package's documented platform/toolchain path. Do not install every extra by default. |
| Package imports but version is unexpected | Another environment or checkout is shadowing the intended distribution | Run `python -c "from importlib.metadata import version; import pyquil; print(version('pyquil'), pyquil.__file__)"` from a neutral directory and repair the active environment. |
| `Program.out()` fails or output is unstable | Unresolved `QubitPlaceholder`/`LabelPlaceholder`, malformed instruction, or unsupported Quil-T object | Read `program-authoring` troubleshooting; resolve placeholders, parse/round-trip a small string, and inspect `out(calibrations=...)`. |
| `qc.run()` rejects a program | The high-level Program was not compiled for the selected target | Build/validate the Program, call `qc.compile(program)`, then pass the resulting executable to `qc.run()`. Check target/compiler compatibility. |
| `Could not communicate with QVM` or connection refused | QVM is not running, URL is wrong, or a service-backed API was mistaken for an in-process simulator | Use `simulation` with `PyQVM`/reference simulators for service-free work, or start/authorize the documented QVM separately and verify its URL. Never claim a service pass from an import. |
| Compiler hangs, times out, or reports a version mismatch | `quilc` is unavailable, unreachable, incompatible, or the program is too complex for the timeout | Run the bundled service probe; verify `quilc` and QVM independently, use finite `compiler_timeout`, inspect compiler diagnostics, and reduce the program before increasing limits. |
| QCS settings/secrets/credentials error | Missing profile, wrong `QCS_SETTINGS_*` path, expired access, reservation, or endpoint | Do not print or copy secrets. Verify paths and access through the user's authorized QCS procedure, then pass an explicit `client_configuration` or endpoint. Stop at the credential boundary if access is not available. |
| QPU executable is opaque/encrypted | QPU translation intentionally hides native program details | Use compiler metadata/documented diagnostics rather than expecting readable native Quil. Test algorithmic behavior on a topology-matched QVM first. |
| Register map has a missing key, wrong shape, or jagged data | Memory declaration/name/size mismatch, dynamic control flow, or QPU-specific readout | Inspect declarations and `get_register_map()`, validate shapes before interpretation, and use raw readout data when rectangular assumptions do not hold. |
| Batch memory maps fail | Map names/types/shapes do not match declared parameters or the backend does not support the requested batch path | Inspect `Program.declare`, use one validated map first, then call `run_with_memory_map_batch` with an iterable of complete maps. |
| `WavefunctionSimulator` works to import but fails on call | It is a QVM HTTP client, not a local state simulator | Use `PyQVM` or `ReferenceWavefunctionSimulator` for local state calculations; route actual wavefunction-service work to `compile-execute`. |
| Reference simulator stochastic operation complains about random state | Direct simulator was initialized with `rs=None` | Pass a `numpy.random.RandomState` or use seeded `PyQVM`. Record the seed for reproducibility. |
| Density state is rejected | Matrix is not square, wrong dimension, non-Hermitian, non-unit trace, or has negative eigenvalues | Validate shape `(2**n, 2**n)`, Hermiticity, trace, and positivity before `set_initial_state`. Stop before allocating a larger exponential state. |
| Noise transform has dimension/parameter/assignment errors | Kraus shapes, CPTP completeness, T1/T2/gate times, gate operands, or readout orientation are invalid | Check model dimensions and `sum(K†K)`, preserve qubit order, distinguish legacy assignment layout from POVM layout, and apply a model only once. |
| Pauli/Experiment result is surprising | Bit-to-eigenvalue sign, incompatible grouped settings, calibration/symmetrization expansion, or finite-shot uncertainty was ignored | Record Pauli convention, settings, shots, calibration and symmetrization levels; group only compatible settings; report uncertainty and backend prerequisites. |
| ISA has missing/dead resources or compiler rejects a gate | Graph omitted isolated nodes, labels created dead gaps, gate is not in the selected 1Q/2Q set, or compiler/QAM/processor targets differ | Inspect graph nodes and ISA dictionaries, validate supported gates and `dead` flags, and keep processor metadata matched to the chosen compiler/QAM. |
| QCS ISA conversion raises `QCSISAParseError`, `GraphGateError`, or an unexpected index error | Malformed operation arity/fields or a version-specific transformer edge case | Validate raw fields and arity before conversion, retain the source ISA, and treat unexpected transformer errors as input/compatibility defects rather than silently dropping gates. |
| LaTeX text works but display fails | `to_latex` only generates source; `display` additionally needs IPython and external TeX/ImageMagick tools | Install the `latex` extra only for interactive display and verify external binaries separately. Neither operation executes a quantum program. |

## Safe escalation

Use the generated route's bundled helper first. Avoid starting services,
contacting QCS, reading credentials, downloading data, or changing a user-owned
environment as a diagnostic shortcut. If an external prerequisite is required,
report the exact missing binary, URL/config class, credential, reservation, or
hardware condition and stop with an explicit unverified boundary.
