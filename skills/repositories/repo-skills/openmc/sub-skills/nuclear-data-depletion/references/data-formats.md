# Data formats and path contracts

Use this reference to distinguish an index, a data library, a depletion chain,
a multigroup library, and a result file. The source repository's format
descriptions are summarized here so a later Researcher does not need the
checkout. For a live file, prefer the bundled
[validator](../scripts/validate_data_paths.py) before loading it through the
Python API.

## 1. `cross_sections.xml` is an index, not cross-section data

A continuous-energy configuration normally points `openmc.config['cross_sections']`
or `OPENMC_CROSS_SECTIONS` at an XML document with a `<cross_sections>` root.
The document lists other files:

```xml
<cross_sections>
  <directory>data/continuous-energy/</directory>
  <library materials="U235 U238" path="U.h5" type="neutron"/>
  <library materials="O16 H1" path="water.h5" type="neutron"/>
  <library materials="c_H_in_H2O" path="lwtr.h5" type="thermal"/>
  <library materials="U" path="U_photon.h5" type="photon"/>
  <library materials="U235" path="U_wmp.h5" type="wmp"/>
  <depletion_chain path="chain.xml"/>
</cross_sections>
```

The required facts are:

- `<directory>` is an optional root for listed paths. Without it, a relative
  path is relative to the directory containing the index. The validator follows
  that documented behavior and resolves all paths to make diagnostics stable
  when invoked from another working directory.
- `<library>` has `path`, `type`, and usually `materials`. The supported type
  labels are `neutron`, `thermal`, `photon`, and `wmp`. The material list is
  metadata used to find which file supplies a nuclide or thermal table; it does
  not replace validation of the HDF5 file.
- `<depletion_chain path="...">` is a chain reference, not an HDF5 library.
  The chain may also be selected independently with
  `openmc.config['chain_file']`/`OPENMC_CHAIN_FILE` or passed to an operator.
- An index can be well-formed XML while a referenced file is absent, unreadable,
  the wrong HDF5 file type, or missing a nuclide used by the model. Those are
  separate failures and should be reported separately.
- `openmc.data.DataLibrary.from_xml(path)` loads the index into dictionaries
  with `path`, `type`, and `materials`; it does not download or repair files.
  `DataLibrary.get_by_material(name, data_type=...)` is useful for checking
  metadata, while `register_file()` inspects an existing `.h5` file and
  `export_to_xml()` writes a new index.

The current inspection has no configured cross-section index. Do not invent a
path or report the continuous-energy data gate as passed.

## 2. Referenced HDF5 files

OpenMC's continuous-energy nuclear-data HDF5 format is versioned. A neutron HDF5
file has root attributes such as `filetype` and `version`, then nuclide groups
with atomic identifiers, an energy grid, temperatures (`kTs`), reactions, and
optional unresolved-resonance/fission-energy data. A photon HDF5 file has
element groups, an energy grid, and photon interaction, relaxation, and
bremsstrahlung data. Thermal-scattering files identify the thermal table, its
nuclides, and temperature-dependent elastic/inelastic distributions. WMP files
carry windowed-multipole data and are not interchangeable with ordinary neutron
files.

The exact datasets are format contracts, not suggestions:

- Neutron reaction cross sections are tabulated against energy in eV, with
  cross sections in barns; reaction groups carry ENDF MT, labels, Q values, and
  product distributions. Temperature groups are named by rounded Kelvin, for
  example `294K`.
- Photon cross sections use element groups and include photon energy grids and
  interaction/relaxation data. Do not use a photon file to satisfy a neutron
  nuclide requirement.
- Thermal scattering tables are named tables (for example a hydrogen-in-water
  table) and apply to their listed nuclides. They are not substitutes for the
  incident-neutron files of the material.
- A referenced file can be opened with `h5py` and still be semantically wrong.
  At minimum inspect the root `filetype`, root `version`, and expected top-level
  groups. For a full transport gate, also check that each model nuclide has a
  compatible temperature and required reaction data.

The bundled validator performs a deliberately lightweight version of this
check: it opens each existing `.h5` reference when `h5py` is available, checks
root `filetype`/two-value `version`, and checks that XML-listed material names
exist as top-level groups. It does not prove that every reaction, temperature,
scattering table, or model nuclide is physically usable. That stronger check
belongs to a prepared-data/transport verification case.

If `h5py` is unavailable, the validator still parses XML and reports path
existence, but it marks HDF5 inspection as skipped. Do not upgrade that result
to “HDF5 valid.”

## 3. ENDF, ACE, and OpenMC HDF5 roles

These formats occur at different stages of a data workflow:

- **ENDF-6** is an evaluated nuclear-data interchange format. OpenMC's
  `openmc.data.endf.Evaluation` reads material evaluations and exposes target,
  projectile, reaction sections, and metadata. `IncidentNeutron.from_endf()` or
  `IncidentPhoton.from_endf()` can construct OpenMC data objects. `Chain.from_endf()`
  combines decay, fission-product-yield, and neutron evaluations into a chain.
  ENDF source files are inputs to processing, not normally the direct runtime
  library for continuous-energy OpenMC transport.
- **ACE** (“A Compact ENDF”) is a processed table format commonly produced by
  NJOY. `openmc.data.ace.Library`/`get_table()` read tables; neutron or photon
  data objects can be created with `from_ace()` and exported to OpenMC HDF5.
  ACE table names and metastable ZAID conventions matter; the API distinguishes
  NNDC and MCNP schemes. Converting ACE does not guarantee the converted data
  covers every temperature or material needed by a model.
- **OpenMC HDF5** is the versioned runtime representation. The usual conversion
  path is `IncidentNeutron.from_ace()` or `from_endf()` →
  `export_to_hdf5()` → `DataLibrary.register_file()` → `export_to_xml()`.
  `from_njoy()` can invoke an external NJOY executable; that is a processing
  operation with its own dependency and runtime cost, not a data-path check.

The Python data API can inspect small, explicitly supplied ENDF/ACE/HDF5 fixtures
without transport. Large evaluation processing, NJOY execution, and resonance
reconstruction can be expensive; do not run them merely to diagnose a missing
index or absent native library. See [troubleshooting.md](troubleshooting.md)
for the failure split.

## 4. Depletion-chain XML

A chain file has a `<depletion_chain>` root and `<nuclide>` children. A nuclide
can declare:

- `half_life` in seconds, `decay_energy` in eV, and `<decay>` modes with type,
  daughter, and branching ratio;
- `<reaction>` paths such as `(n,gamma)` with Q in eV, a target, and a branching
  ratio; fission has no single target;
- `<neutron_fission_yields>` with energy points, product names, and independent
  yields, or a `parent` from which yields are borrowed; and
- decay source records for emitted photons/electrons when present.

`openmc.deplete.Chain.from_xml()` parses and links the nuclides. A chain can be
created from ENDF decay, FPY, and neutron files with `Chain.from_endf()`; the
selected transmutation reactions affect the matrix. A chain is not a
cross-section index and does not make transport data available. It is required
for most depletion/activation calculations and is also used by data helpers
such as half-life and MicroXS selection.

Check these before running:

- names use the GNDS convention used by materials and HDF5 libraries, including
  metastable forms such as `Am242_m1`;
- daughters and fission products needed by the case are present or intentionally
  handled by the chain's replacement behavior;
- half-lives, branching ratios, reaction Q values, and FPY energy interpolation
  are appropriate to the physics question; and
- the chain's reaction set overlaps the reaction data supplied to the operator.

A chain can parse and still be unsuitable: a missing reaction path may be
silently absent from a reduced calculation, and a nuclide with no chain data may
not evolve as expected. Compare the chain contents with the initial materials,
requested reactions, and cross-section/MicroXS coverage.

## 5. Multigroup files and MGXS metadata

OpenMC has two related multigroup concepts:

1. **An `mgxs.h5` runtime library** contains both metadata and multigroup data.
   Its root identifies `filetype='mgxs'`, a version, number of energy groups,
   optional delayed groups, and monotonically increasing group boundaries in eV.
   Each nuclide/material dataset may declare fissionability, isotropic versus
   angle-dependent representation, scattering format/order, and temperature
   data. Total, absorption, fission, chi, inverse velocity, scattering, and
   related datasets have shape contracts. The model must select multigroup mode
   and point materials at this file.
2. **The `openmc.mgxs` Python workflow** computes multigroup cross sections from
   transport tallies and statepoints. `EnergyGroups` stores ascending low-to-high
   edges, while OpenMC energy-group indices are conventionally numbered from the
   highest-energy group as group 1. `openmc.mgxs.Library` selects domain type,
   `mgxs_types`, group structure, nuclide-wise versus macroscopic data, angular
   representation, and tally settings; it can build tallies, load a statepoint,
   condense data, and export an HDF5 store or create multigroup model inputs.

Do not reverse an array merely because the file's group edges are ascending:
confirm whether an API expects energy group 1 to be the highest-energy group.
`EnergyGroups.get_group_bounds()` and `get_group_indices()` expose that mapping.
`convert_flux_groups()` conserves flux by lethargy and requires compatible group
ranges; it does not generate missing nuclear data.

For depletion, `MicroXS` is a separate in-memory/table representation. Its data
array has shape `(number of nuclides, number of reactions, number of energy
groups)` and cross sections are assumed to be in barns. CSV/HDF5 import/export
preserves the nuclide and reaction axes. A `MicroXS` object and each flux array
must agree on group structure and domain ordering before constructing an
`IndependentOperator`.

## 6. Results are another format

`depletion_results.h5` is not `mgxs.h5` and is not a statepoint. It stores
versioned depletion results including:

- `eigenvalues` with value and uncertainty per stored result;
- atom numbers indexed by result, material, and nuclide;
- optional reaction rates indexed by material, nuclide, and reaction;
- beginning/end `time` in seconds and source rate/power;
- process-time metadata and optional keff-search roots; and
- material volume/name and nuclide/reaction index metadata.

Load it with `openmc.deplete.Results(path)`. Use `get_keff()`, `get_atoms()`,
`get_mass()`, `get_activity()`, `get_decay_heat()`, or `get_reaction_rate()`
only after checking material IDs, nuclide names, volumes, units, and whether
reaction rates were written (`write_rates=True`). For generic statepoint and
summary HDF5 files, use [tallies-results](../../tallies-results/SKILL.md).

## Format checklist

Before a data-dependent claim, record:

- index path and resolved references;
- missing/unreadable references and each HDF5 `filetype`/version observed;
- model nuclides, temperatures, particle type, and data types required;
- chain path/version-equivalent provenance and reaction/FPY coverage;
- MGXS/MicroXS group edges, axis ordering, units, and domain mapping; and
- result-file type/version, time units, optional rate presence, and volumes.

For workflow selection and normalization, continue with
[depletion-and-mgxs-workflows.md](depletion-and-mgxs-workflows.md).
