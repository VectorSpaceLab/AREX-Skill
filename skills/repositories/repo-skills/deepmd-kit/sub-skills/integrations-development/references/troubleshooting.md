# Integration Troubleshooting

Use this matrix when DeePMD-kit integrations fail at the boundary between model files, host engines, native libraries, and repository builds.

## LAMMPS

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| `Unrecognized pair style 'deepmd'` or `deepspin` | DeePMD LAMMPS package/plugin is not loaded | Check `lmp -h` for USER-DEEPMD styles; check whether plugin mode is required | Add `plugin load libdeepmd_lmp.so`, configure the plugin search path, or use a LAMMPS binary built with USER-DEEPMD. |
| `Cannot open shared object file libdeepmd_lmp.so` | Plugin library path missing | Inspect current run directory and plugin search path | Provide an absolute/relative plugin library path or set the LAMMPS plugin path in the launch environment. |
| Input uses `units lj` | DeePMD-kit LAMMPS integration does not support LJ units | Review the `units` command | Switch to `metal` or another supported physical unit style. |
| Run stops with missing mass errors | Data file lacks masses and script does not define them | Check `Masses` in the data file and `mass` commands | Add `mass TYPE VALUE` for every LAMMPS atom type before velocity or thermostat commands. |
| Energies/forces look wrong after startup | LAMMPS type order does not match model type map | Compare `pair_coeff * *` element order with data-file type IDs and the model type map | Use explicit element names in `pair_coeff` or reorder mapping to match trained types. |
| `pair_coeff` rejects element names | Model has no compatible stored type map or names conflict | Try a minimal `pair_coeff * *` only when the model type map should be used | Re-export/freeze with a type map or use type-index mapping consistently. |
| Model deviation file absent | Only one model was provided or run length/cadence never reached `out_freq` | Check `pair_style` model count and `out_freq` | Provide multiple models and a run long enough to emit deviation output. |
| Atomic deviation columns missing | `atomic` keyword omitted | Review `pair_style` keywords | Add `atomic` when per-atom deviations are needed. |
| Frame/atom parameter error | Model expects `fparam` or `aparam`, but script omits or mis-sizes it | Check model training/export contract and `pair_style` keywords | Add matching `fparam`, `fparam_from_compute`, `fparam_from_fix`, `aparam`, or `aparam_from_compute`. |
| Charge/spin runtime error | Charge/spin vector missing or wrong length | Check model metadata expectations | Add `charge_spin` values or use a model exported with a valid default charge/spin vector. |
| Spin model virial expectations fail | Spin models do not support virial/atomic virial like standard models | Check requested output and `pair_style deepspin` use | Remove virial-dependent checks or use a standard model when virials are required. |
| MPI/GPU run is slow or unstable | Rank-to-GPU mapping is invalid | Check MPI rank count, visible devices, and backend logs | Use at most one GPU per MPI rank and make device mapping explicit. |

## i-PI

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| `dp_ipi` command missing | DeePMD-kit was not built with i-PI support | Check command availability and build options | Rebuild/install with i-PI support enabled. |
| Client cannot connect | Socket type, host, or port mismatch | Compare i-PI XML and DeePMD client JSON | Align `use_unix`, `host`, and `port`; ensure server starts before clients. |
| Atom type error | XYZ atom labels are not mapped to DeePMD type indexes | Inspect `coord_file` labels and `atom_type` JSON | Add every atom label to `atom_type` with the correct zero-based type index. |
| Forces do not correspond to intended model | Wrong `graph_file` or stale client JSON | Inspect client JSON in the run directory | Point `graph_file` to the intended frozen model and restart the client. |

## Native C/C++/HPP APIs

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| Header include fails | Include directory missing | Check compiler `-I` flags | Add the DeePMD-kit include directory that contains `deepmd/DeepPot.h`, `deepmd/c_api.h`, or `deepmd/deepmd.hpp`. |
| Linker cannot find `deepmd_c` or `deepmd_cc` | Library directory missing | Check linker `-L` flags and installed libs | Add the DeePMD-kit library directory and the correct library name. |
| TensorFlow/PyTorch symbol errors | Backend library missing or incompatible | Check backend root and model backend | Link and load the backend library required by the model, or rebuild DeePMD-kit with that backend. |
| Runtime cannot load shared libraries | Runtime search path missing | Check rpath, loader path, and environment | Add `-Wl,-rpath=...` at link time or configure the runtime library path externally. |
| `TensorFlow backend is not built` or similar | Native library lacks the requested backend | Check build options and model suffix/backend | Rebuild with the backend required by the model or use a model for an available backend. |
| Wrong output size or crashes | Flat arrays have wrong lengths | Count `coord`, `cell`, `atype`, force, virial, and atom-output buffers | Use `natoms * 3`, `9`, `natoms`, `natoms * 3`, `9`, `natoms`, and `natoms * 9` conventions as appropriate. |
| Type mapping mismatch | DeePMD type indexes differ from host-engine IDs | Compare host IDs with zero-based model type indexes | Translate host types before calling native APIs. |
| Charge/spin error | Missing default or wrong explicit length | Check model metadata and overload used | Pass explicit charge/spin with the expected dimension or re-export with defaults. |

## Node.js

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| `Cannot find module 'deepmd-kit'` | Node package not installed or linked | Run `node -e "require('deepmd-kit')"` | Install/link the Node package in the active Node environment. |
| Native addon load failure | Shared libraries or backend libs unavailable | Inspect error text for `.node`, DeePMD, TensorFlow, or PyTorch library names | Configure runtime library search paths and ensure native build compatibility. |
| Build from source fails | Node.js headers, SWIG, or node-gyp unavailable | Check tool versions and CMake Node options | Install required Node build tools and configure Node include directories. |
| `vectord`/`vectori` usage error | Plain JS arrays passed directly to native compute | Inspect call site | Convert arrays to DeePMD vector wrapper classes before calling `compute`. |

## ASE and dpdata

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| `deepmd.calculator` import fails | ASE extra or DeePMD Python install missing | Import `deepmd` and `ase` separately | Install the Python dependencies through the installation-backends workflow. |
| ASE calculator returns unexpected units | Caller mixes unit systems | Check ASE structure units and model training units | Keep ASE positions in angstrom and interpret energy/force according to DeePMD model conventions. |
| dpdata `driver="dp"` fails | dpdata plugin registration unavailable | Check `dpdata` and `deepmd` imports in the same environment | Install compatible dpdata and DeePMD-kit packages in the same environment. |
| Predicted labels look mismapped | Type names/order differ between dpdata system and model | Inspect dpdata type map and model type map | Reconcile type ordering before prediction. |

## Repository Build and Test

| Symptom | Likely cause | Checks | Fix |
| --- | --- | --- | --- |
| C++ build fails before compiling DeePMD code | Backend roots missing | Check `python -c` probes for TensorFlow and PyTorch | Install backend packages and set `TENSORFLOW_ROOT` and `PYTORCH_ROOT` from Python imports. |
| Build appears hung | Expected C++ build duration is several minutes | Compare elapsed time with expected about 164 seconds | Do not cancel early; use a timeout of at least 300 seconds. |
| Python editable install times out | Build can take about 67 seconds | Check timeout setting | Use a timeout of at least 120 seconds. |
| Full test suite is too slow | Suite has hundreds of files | Check whether a targeted test covers the change | Run single tests or subsystem tests instead of the full suite. |
| `ruff` missing | Linter not installed in the environment | Run `ruff --version` | Install ruff in the active environment, then run `ruff check .` and `ruff format .`. |

## Escalation Questions

Ask the user rather than guessing when:

- The LAMMPS executable, MPI launcher, cluster module, or container name is unknown.
- The model type map is unavailable and element/type order cannot be inferred safely.
- A run would require long MD, long training, full-suite testing, or broad dependency installation.
- Repairing an existing environment could upgrade or break user-managed packages.
- GPU rank mapping depends on site scheduler policy.
