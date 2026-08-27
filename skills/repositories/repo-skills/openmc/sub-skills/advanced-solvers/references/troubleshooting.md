# Advanced troubleshooting

Use the symptom, boundary, and next-check columns together. The goal is to
separate Python/API problems, native build problems, optional dependency
problems, and missing nuclear data.

| Symptom | Likely boundary | Next safe check and recovery |
|---|---|---|
| `import openmc` succeeds but `import openmc.lib` raises an `OSError` about `libopenmc.so` (or the platform shared-library suffix) | The base Python package is usable, but the native shared library has not been built, copied into the binding location, or its loader dependencies are unavailable | Run `scripts/check_native_features.py` with explicit `--library`/`--build-dir` paths. Build the CPU shared library in a disposable build only if a source tree and native dependencies are intentionally available. Do not classify this as a base `openmc` import failure. |
| `openmc.lib.feature_enabled(...)` fails for a name other than `dagmc`, `libmesh`, `strict_fp`, or `uwuw` | The C API rejects unknown feature names | Query only those four names. Random ray, CMFD, MPI, photon, and NCrystal are not valid names for this function; inspect their own build/runtime prerequisites. |
| CMake says MPI/DAGMC/libMesh cannot be found | The requested optional dependency is absent or not discoverable; a Python class cannot supply the native dependency | Inspect the CMake configure result and cache. Provide an explicit dependency prefix to a new configure attempt only when the dependency is already installed. Do not download it or claim support. |
| `OPENMC_USE_DAGMC=ON` fails with an old DAGMC version, or UWUW is enabled without compatible DAGMC UWUW | CMake feature/dependency gate | Use a DAGMC installation at the required supported version and confirm the discovered installation was built with UWUW when requested. Otherwise record DAGMC/UWUW as unavailable. |
| User requests MPI random ray and expects distributed scaling | Random-ray solver limitation, not necessarily a failed MPI build | Explain that the native solver warns that MPI work is performed by rank 0. Verify MPI support separately; do not promise efficient random-ray MPI decomposition. |
| Random ray reports unsupported score/filter | Random-ray native input restrictions | Keep only flux, total, fission, nu-fission, kappa-fission, and event scores, and the supported cell/cell-instance/distribcell/energy/material/mesh/universe/particle filters. Route ordinary tally design to tallies-results. |
| Random ray rejects the ray source | Ray-source contract violation | Use an independent isotropic source with a box spatial distribution covering the model domain, not restricted to fissionable sites. In fixed-source mode also provide an independent isotropic particle source that is a point source or has cell/material/universe domain constraints. |
| Random ray rejects a material with zero total cross section or anisotropic MGXS | Random-ray multigroup data constraint | Use isotropic MGXS with positive total macroscopic cross sections for modeled materials. Represent a void with an empty cell fill, not a zero-total-cross-section material. Route MGXS/data preparation to nuclear-data-depletion. |
| Random ray is unstable, slow, or reports high source-region miss rate | Ray density/length tuning, not automatically a code defect | Increase rays or active length based on miss-rate observations; ensure inactive length is long enough for the relevant mean-free-path and streaming/uncollided path. Remember fixed-source random ray also needs inactive batches. Do not claim convergence from a settings smoke test. |
| `CMFDRun.mesh = ...` raises a validation error | Incomplete or inconsistent CMFD mesh | For a regular mesh set dimensions and lower-left plus exactly one of width/upper-right; for a rectilinear mesh set three grids. Use positive dimensions/widths, six bounded albedos, and a 0/1 map. |
| CMFD batch iteration leaves native state initialized after an exception | Lifecycle not paired | Prefer `with cmfd_run.run_in_memory():`. If using direct calls, pair `openmc.lib.init`/`finalize` and `simulation_init`/`simulation_finalize`; do not call `next_batch` before simulation initialization. |
| Weight-window bounds reshape incorrectly or upper bounds are rejected | Mesh/energy-bin shape or constructor contract | Supply one upper-bound form only. The number of bound values must match mesh bins times energy bins; use structured shape `(nx, ny, nz, ne)` or unstructured `(nelements, ne)`. Keep energy bounds in eV. |
| Weight-window particle type is rejected | Supported particle set | Python weight windows accept neutrons or photons only. Charged particles are not a weight-window particle type in this API. |
| FW-CADIS targets are not recognized during export | Targets are not attached to the model's tally collection, or the wrong export method was used | Put the target tallies on `model.tallies` and export the model XML. Do not rely on standalone settings/tally XML export for local FW-CADIS target validation. Use the same mesh for FW-CADIS and random-ray source-region subdivision. |
| An existing `weight_windows.h5` is unexpectedly replaced | A generator remained configured | Remove the generator when applying an existing file; set the weight-window file and `weight_windows_on` explicitly. Treat generation and application as separate workflows. |
| Native test cannot run because cross sections are missing | Data prerequisite, not necessarily a build failure | Check the data environment through setup-runtime. No `OPENMC_CROSS_SECTIONS` means transport claims are conditional. Do not download data as part of this skill. Pure API/XML and selected C++ tests may still be possible. |
| Photon transport is rejected in a multigroup input | Native physics-mode restriction | Use continuous-energy photon transport with compatible photon data, or keep the model multigroup without photon transport. `electron_treatment` controls local charged-particle treatment; it does not enable spatial electron transport. |
| `Material.from_ncrystal()` raises an import/runtime error | NCrystal Python package or runtime library is unavailable | Verify the NCrystal package/library independently. NCrystal materials cannot be combined with ordinary nuclides, S(a,b), or macroscopic cross sections. Mark NCrystal unverified when the dependency is absent. |
| Restart fails even though a statepoint exists | Statepoint/input mismatch or wrong restart mode | A statepoint restart must match the input model. Particle-restart mode consumes a particle-restart file for a single source particle. Route file inspection to tallies-results and data/path setup to neighboring skills. |

## Verification stop rules

- Stop at `unverified` for DAGMC, libMesh, MPI, NCrystal, photon data, random
  ray transport, CMFD transport, or weight-window generation when the required
  dependency/data/library is absent.
- Mark the base runtime `blocked` only when the ordinary Python import, CPU
  build, or required API check fails. Missing `libopenmc` alone is an expected
  pre-build native limit.
- If CMake configuration and the loaded library disagree, report both. Rebuild
  or point the binding at the intended library; do not choose the favorable
  result silently.
- Do not treat a successful settings/XML construction as a transport or
  numerical-correctness result.

## Evidence boundary

The recovery actions above are adapted from the validated Python setters, C API
lifecycle, native random-ray validation messages, CMake dependency gates, and
public user/method documentation. They are self-contained and do not require a
future Researcher to access the original checkout.
