# Advanced API reference

This reference is for solver-specific operations after the ordinary model has
been built. It deliberately keeps routine model construction and result
analysis in their sibling routes.

## Random ray

Random ray is a multigroup solver. A normal continuous-energy model must first
be converted to multigroup and then to random ray, or be authored as a
multigroup model. The convenience sequence is:

```python
model.convert_to_multigroup()
model.convert_to_random_ray()
```

The multigroup conversion can create an `mgxs.h5` library by running a
coarsely converged continuous-energy calculation. That step is data- and
transport-dependent; do not describe conversion as a data-free smoke test.
`convert_to_random_ray()` initializes solver parameters from the geometry only
when `settings.random_ray` is not already populated.

The `Settings.random_ray` mapping accepts these validated keys:

- `distance_inactive` and `distance_active`: positive distances in cm. The
  inactive distance is the dead zone used to develop the starting angular flux;
  the active distance contributes to estimates.
- `ray_source`: an `IndependentSource`-compatible source that is uniform in
  space and isotropic in angle for the ray sampler. The source box must bound
  the full simulation domain and must not be limited to fissionable regions.
- `volume_estimator`: `naive`, `simulation_averaged`, or `hybrid`.
- `source_shape`: `flat`, `linear`, or `linear_xy`.
- `volume_normalized_flux_tallies`: boolean.
- `adjoint`: boolean and `adjoint_source`: one or more source objects for
  localized adjoint responses.
- `sample_method`: `prng`, `halton`, or `s2`.
- `source_region_meshes`: iterable of `(mesh, domains)` pairs. Domains must be
  materials, cells, or universes. If a tally or weight-window mesh is used for
  source-region subdivision, use the same mesh so the regions and tally bins
  remain consistent.
- `diagonal_stabilization_rho`: nonnegative real value; zero disables the
  stabilization described by the input contract.

In fixed-source random ray mode, provide a particle source in addition to the
ray source. The external source must be an independent isotropic source and
must either be a point source or be constrained by cell, material, or universe
domain IDs. The native solver rejects unsupported combinations rather than
silently treating them as ordinary Monte Carlo.

Random-ray native validation also limits tally scores to flux, total, fission,
nu-fission, kappa-fission, and event, and limits filters to cell,
cell-instance, distribcell, energy, material, mesh, universe, and particle.
The multigroup macroscopic data must be isotropic and have positive total
cross sections in modeled materials. A zero-total-cross-section material is
not a random-ray void; use an empty cell fill for a void region.

Inactive batches are needed in both eigenvalue and fixed-source random-ray
runs because the scattering source must converge. The active ray length and
number of rays trade off angular/spatial sampling against the fixed per-ray
cost. The reported source-region miss rate is the useful observation for
adjustment. The user guide suggests starting with an active length roughly ten
times the inactive length, but that is a tuning heuristic, not a correctness
or convergence guarantee. Long uncollided paths, detector responses, and void
regions may require longer distances.

Random ray does not provide efficient MPI domain decomposition: when multiple
MPI processes are present, the native solver warns that work is performed by
rank 0. Treat an MPI-enabled build as a build fact, not as evidence of random
ray MPI scaling. Only voxel plots are used for random-ray end-of-simulation
plotting.

With a built shared library, the Python binding exposes `openmc.lib.run_random_ray()`.
For ordinary executable runs, keep command construction and cross-section setup
in the setup-runtime route.

## CMFD

CMFD is driven through `openmc.cmfd.CMFDMesh` and `openmc.cmfd.CMFDRun` and
uses the C API. A regular mesh requires `dimension`, `lower_left`, and exactly
one of `upper_right` or `width`; positive dimensions and widths are validated.
A rectilinear mesh requires three grid arrays, each with more than one point.
The mesh energy boundaries are nonnegative; albedo has six values in `-x,+x,
-y,+y,-z,+z` order and each value is in the inclusive range 0 to 1. An
acceleration map contains only 0/1 values and must include every fission-source
region when used.

Important `CMFDRun` controls include:

- positive `tally_begin` and `solver_begin` batch numbers;
- `feedback` to use the diffusion result to adjust the next fission-source
  batch, `downscatter` for the two-group effective downscatter option, and
  `cmfd_ktol`/`stol` for CMFD power-iteration tolerances;
- `window_type` of `none`, `rolling`, or `expanding`; `window_size` matters
  only for `rolling`;
- `run_adjoint` with `adjoint_type` `physical` or `math`;
- `display` keys `balance`, `dominance`, `entropy`, and `source`;
- `write_matrices`, `spectral`, `gauss_seidel_tolerance`, `reset`, and
  `use_all_threads`.

Use the context manager to guarantee the native lifecycle:

```python
from openmc import cmfd

run = cmfd.CMFDRun()
run.mesh = mesh
with run.run_in_memory():
    for _ in run.iter_batches():
        pass
```

`run_in_memory()` enters `openmc.lib.run_in_memory()`, calls `CMFDRun.init()`,
yields for batch iteration, and finalizes CMFD and the native simulation on
exit. `run()` is the bounded convenience form that consumes all batches. CMFD
statepoint data is appended by `statepoint_write`; route interpretation of
that output to tallies-results.

## Weight windows and generators

`openmc.WeightWindows` is a mesh- and energy-bin-indexed object. For a
structured mesh, lower and upper bounds reshape to
`(nx, ny, nz, num_energy_bins)`; an unstructured mesh uses
`(num_elements, num_energy_bins)`. Supply exactly one of `upper_ww_bounds` and
`upper_bound_ratio`, and make the lower and upper arrays the same size. Energy
bounds are in eV. The Python validator only permits neutron and photon weight
windows. `survival_ratio` must be at least 1; `weight_cutoff` must be positive;
`max_split` is an integer; and `max_lower_bound_ratio`, when supplied, is at
least 1.

For generation, `WeightWindowGenerator.method` is `magic` or `fw_cadis`.
`max_realizations` and `update_interval` are positive. FW-CADIS `targets` may
be an `openmc.Tallies` collection or tally IDs, but target tallies must also be
present on the model when exporting model XML; do not use standalone settings
or tally XML export as a substitute for model export in that local workflow.
The generator's optional update parameters are method-validated `value`,
`threshold`, and `ratio` fields. A generator may be `on_the_fly`.

For FW-CADIS with random ray, use the same mesh for weight-window generation
and random-ray source-region subdivision so the window mesh does not split a
source region unexpectedly. A forward solve followed by an adjoint solve
produces `weight_windows.h5`; this requires the multigroup/random-ray and data
prerequisites. For applying an existing file, set the weight-window file,
turn `weight_windows_on` on, and choose collision/surface checkpoints as
needed. A generator is not needed to load an existing file; leaving one in the
settings requests new generation and can overwrite the file.

`WeightWindowsList.from_hdf5()` and `from_wwinp()` are readers. The latter
rejects unsupported time-dependent windows and has mesh-orientation limits;
classify such failures as input-format limits rather than native build failures.

## `openmc.lib` lifecycle and feature queries

Importing `openmc.lib` immediately loads the packaged native shared library.
The base `openmc` import and ordinary XML/API operations do not require this
load. Once the library is available, the safe high-level lifecycle is:

```python
with openmc.lib.run_in_memory(args=None, intracomm=None, output=True):
    openmc.lib.simulation_init()
    for _ in openmc.lib.iter_batches():
        # optional inspection or control between batches
        pass
    openmc.lib.simulation_finalize()
```

`run_in_memory()` calls `init()` before the block and `finalize()` in a
`finally` clause. Direct calls must preserve the same order: `init()` before
native operations; `simulation_init()` before `next_batch()`/`iter_batches()`;
`simulation_finalize()` after batch work; `finalize()` last. `run()` is a
whole-simulation call after `init()`, while `run_random_ray()` enters the
random-ray native entry point. `TemporarySession` additionally exports a model
in an isolated working directory and is useful when a supplied model should
not pollute the caller's directory.

`openmc.lib.feature_enabled()` queries exactly these build features:
`dagmc`, `libmesh`, `strict_fp`, and `uwuw`. An unknown name is an invalid
argument. Feature results describe the loaded library, not a Python package
class or a CMake option from a different build. There is no `random_ray` or
`mpi` feature name in this query; inspect the build configuration and native
behavior separately.

The C API is explicitly experimental. The main sequencing contracts are
`openmc_init`, `openmc_simulation_init`, `openmc_next_batch` or
`openmc_run`, `openmc_simulation_finalize`, and `openmc_finalize`. Native calls
return error status through the C interface; Python bindings install an error
handler and raise a corresponding exception.

## Optional physics, geometry, and restart boundaries

- **DAGMC:** `DAGMCUniverse` points to a DAGMC HDF5 geometry and can carry
  supported material/cell overrides. The native library must have DAGMC
  enabled and the external DAGMC dependency must be present. Inspect
  `feature_enabled('dagmc')` before promising execution.
- **libMesh:** enables unstructured-mesh tally support and is separately gated
  by the native build and libMesh installation. It is not implied by a Python
  unstructured mesh class.
- **UWUW:** is only valid with DAGMC and with a DAGMC installation configured
  with UWUW; the build should reject an inconsistent request.
- **NCrystal:** material creation via `Material.from_ncrystal()` requires the
  Python NCrystal package. Native use loads the NCrystal library at runtime
  when an NCrystal material is actually present. NCrystal materials cannot
  also receive ordinary nuclides, S(a,b), or macroscopic cross-section data.
- **Photon transport:** `Settings.photon_transport = True` is a continuous-
  energy feature in this contract; native settings reject photon transport in
  multigroup mode. Photon data and compatible material data remain separate
  runtime prerequisites.
- **Charged particles:** OpenMC does not spatially transport electrons and
  positrons. It deposits their energy locally and can produce bremsstrahlung
  photons at their birth location. Do not describe `electron_treatment` as a
  charged-particle trajectory solver.
- **Restart/special source interfaces:** statepoint restart requires a
  statepoint matching the input model. Particle-restart mode is for a single
  source particle from a particle-restart file. These are native execution
  workflows; keep ordinary statepoint inspection with tallies-results and
  data-path setup with the neighboring routes.

## Evidence basis

This contract was distilled from the public Python bindings and validators,
random-ray native validation, the C API declarations/documentation, CMFD and
variance-reduction user/method documentation, CMake feature gates, and the
native/advanced test candidates. The named APIs above are the operating
surface; the original source tree is not a runtime dependency.
