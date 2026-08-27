# Hamiltonian and chemistry troubleshooting

Diagnose the smallest failing layer first: import, input schema, model
construction, persisted data, optional integration, or downstream handoff.
Do not fix a failure by silently changing physical flags or units.

## Install and import

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `ModuleNotFoundError: openfermion` | The runtime environment does not contain the core package. | Install or select the supported OpenFermion environment before running the helper. Verify `import openfermion` and a small `fermi_hubbard` call. |
| `ModuleNotFoundError: h5py` while importing chemistry | Molecular-data persistence dependencies are missing. | Install the core chemistry persistence dependencies or keep the task on lattice-only constructors. Do not replace HDF5 with an invented in-memory schema. |
| `ModuleNotFoundError: pubchempy` only on PubChem call | The environment is an incomplete core install, or the lazily imported dependency is unavailable. PubChem usage itself is optional and online. | Repair the core install if lookup is approved, or provide a literal/local geometry. Hubbard/jellium workflows do not call PubChem. |
| Import fails after adding PySCF/ASE/JAX | Optional plugin/version/backend conflict. | Test core imports in a clean environment, then add one optional integration at a time. Report the plugin boundary instead of changing the core model. |

## Hubbard dimensions, flags, and API misuse

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Unexpected number of modes | Spinful/spinless choice was implicit, or the general lattice has `n_dofs > 1`. | Compute `n_sites * n_dofs * (1 if spinless else 2)` and record the choice. Standard `fermi_hubbard` uses `2*s`/`2*s+1` in the spinful case. |
| Too many/few periodic edges on a 2x2 or 1xN grid | Wraparound edges are deduplicated for dimensions of size two; a one-site dimension can self-wrap in a way that is not a generic graph degree. | Inspect `HubbardSquareLattice.site_pairs_iter(..., ordered=False)` or the operator terms. Never infer from a generic periodic degree formula. |
| Magnetic field appears to do nothing | `spinless=True`; the standard and general models ignore the field for spinless lattices. | Use a spinful model or remove the field from the expected result. |
| Constant or interaction coefficients differ by shifts | `particle_hole_symmetry=True` uses `n - 1/2`, including constant contributions. | Rebuild with the intended flag and compare identity terms separately from non-identity terms. |
| `ValueError` for a general Hubbard parameter | Unknown edge type, out-of-range DOF, wrong tuple length, same-DOF onsite tunneling, or onsite same-spin self-interaction. | Validate `lattice.edge_types`, `n_dofs`, tuple arity, and `SpinPairs` before constructing. |
| A bosonic result is passed to a fermionic transform | `bose_hubbard` returns `BosonOperator`. | Route to a boson-compatible downstream workflow; do not relabel the operator as fermionic. |

## Grid, geometry, and plane-wave failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| `Grid` rejects `scale=1` | A scalar scale must be a positive float in this API. | Use `scale=1.0`, a valid per-axis tuple/list for `length`, or a correctly shaped cell-vector ndarray. |
| Invalid position/momentum/orbital error | An index is out of range, has the wrong dimensionality, or spin was supplied where it is not valid. | Use `list(grid.all_points_indices())`, `grid.orbital_id`, and `grid.grid_indices` as the round-trip contract. |
| Plane-wave geometry is rejected | Coordinate count does not equal `grid.dimensions`, or an element symbol is unknown. | Use 1/2/3 coordinates matching the grid and a recognized periodic-table symbol. Validate before constructing. |
| Molecular geometry works but plane-wave geometry is physically wrong | `MolecularData` geometry is in Angstroms while plane-wave constructors expect atomic units. | Convert explicitly with `angstroms_to_bohr` or provide an atomic-unit geometry and record the conversion. |
| `include_constant=True` fails with nuclei | The plane-wave constructor disallows a Madelung constant for non-uniform geometry. | Omit the constant or construct the terms with a separate, justified nuclear-energy treatment. |
| Dual-basis jellium constant is twice the expected shift | In this package version, `jellium_model(..., plane_wave=False, include_constant=True)` adds the shift in both the dual constructor and wrapper. | Inspect the identity-term difference and use `dual_basis_jellium_model(..., include_constant=True)` when one shift is intended. Record the version-specific choice; do not silently subtract. |
| Jellium call is unexpectedly large/slow | Grid point count, spin multiplicity, or cutoff creates a large term expansion. | Start with one/two dimensions and a tiny grid, set `e_cutoff`, and estimate mode/term growth before scaling. |
| Non-periodic result changes unexpectedly | The non-periodic correction depends on `period_cutoff`; default derives it from cell volume. | Choose an explicit cutoff for a controlled comparison and record it. Do not compare runs with different implicit cells. |

## MolecularData, tensors, and HDF5

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Constructor says geometry/basis/multiplicity are required | A load was intended but `filename` was empty, or a new metadata object omitted a required field. | For new data provide all three fields. For loading use `MolecularData(filename=...)` and ensure the record exists. |
| Multiplicity rejected | It is non-positive or not integer-valued. | Supply a positive integer spin multiplicity. It is not a count of unpaired electrons. |
| `n_orbitals`, integrals, or energies are `None` | The object has metadata only, or the saved record lacks that calculation field. | Treat this as an expected missing-result state. Obtain results through an approved chemistry backend or load a record containing them. |
| `get_integrals()` raises `MissingCalculationError` | One-body or two-body integrals are absent. | Check both lazy properties and the HDF5 record. Do not substitute zero tensors unless the physical model explicitly says they are zero. |
| `get_molecular_hamiltonian()` fails after metadata construction | Metadata does not compute integrals. | Stop and report the required external calculation; do not claim that `MolecularData` ran HF/PySCF. |
| Active-space call rejects an empty selection | `active_indices` must contain at least one spatial orbital. | Supply valid spatial-orbital indices and ensure integral data is present. State occupied/core and active choices. |
| HDF5 save/load permission or path error | The selected filename directory is missing or not writable, or a record is being overwritten unintentionally. | Use a caller-owned temporary/work directory, create it deliberately, check the base filename, and clean up test files. Metadata-only workflows need no save. |
| Arrays have unexpected shape or energy mismatch | Spatial versus spin-orbital tensors or OpenFermion's two-electron ordering was confused with another convention. | Check `(n,n)` and `(n,n,n,n)` spatial shapes, the `2*n` spin-orbital dimension, alpha-even/beta-odd indexing, and the class's one-half two-body convention. |
| Reduced Hamiltonian seems different from the original | One-body terms were folded into two-body terms under a fixed particle-number identity. | Use the same positive `n_electrons` (not one), preserve the constant, and compare only within that number sector. |

## PubChem, plugins, and network boundaries

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| PubChem returns `None` or an empty result | No matching structure, service failure, or unavailable 3-D record. | Use a literal/local geometry, or retry only when network use is approved. Record whether the result was 2-D or 3-D. |
| PubChem rejects `structure` | Value is not `None`, `"2d"`, or `"3d"`. | Choose one of those values. Prefer explicit `"3d"` when a 3-D geometry is required. |
| External chemistry plugin is unavailable | Plugin is not installed, not supported on the platform, or its backend executable is missing. | Keep core metadata construction separate. Ask for plugin installation/backend approval; do not run or emulate the external calculation in a bounded smoke check. |
| Resource-estimation import fails | Optional resource package or accelerator/backend is absent. | Report the optional dependency and hand off the already validated operator/tensor schema. Do not change the Hamiltonian to fit an unavailable estimator. |

## Downstream handoff failures

| Symptom | Likely cause | Recovery |
| --- | --- | --- |
| Mapping stage reports unknown operator family | A `BosonOperator`, `FermionOperator`, and `InteractionOperator` were conflated. | Include `operator_family` and route conversion/mapping to [operators-and-transforms](../../operators-and-transforms/SKILL.md). |
| Qubit count is guessed from term count | Identity/sparse terms do not enumerate all modes. | Supply the model-derived mode count or use a validated operator utility in the mapping stage. |
| Circuit or eigensolver task starts before model choices are fixed | Basis, flags, units, or cutoff were omitted from the handoff. | Return to the model record in [data-formats.md](data-formats.md), fill every relevant field, and then route to the appropriate sibling. |
| A metadata object is reported as a recovered energy | External result provenance was lost. | Label the object as metadata-only, name the backend/record for computed fields, and leave unresolved fields explicit. |
