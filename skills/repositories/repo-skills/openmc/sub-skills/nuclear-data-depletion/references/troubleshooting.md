# Nuclear-data and depletion troubleshooting

Start with the smallest failing boundary. Do not respond to a data error by
changing geometry, downloading an unapproved bundle, or running a long
transport case. Use the read-only
[validator](../scripts/validate_data_paths.py) with an explicit
`--cross-sections` path, then classify the failure below.

## Fast classification table

| Observation | Likely boundary | Safe next check |
|---|---|---|
| `import openmc` fails | Python package/dependency gate | Read [setup-runtime](../../setup-runtime/SKILL.md); capture the exception and package version. |
| `import openmc` works but `import openmc.lib` cannot load `libopenmc.so` | native-library gate | Read [advanced-solvers](../../advanced-solvers/SKILL.md); verify the built shared-library path and ABI, without claiming coupled depletion. In this package version, `openmc.deplete` may transitively encounter the same gate. |
| `OPENMC_CROSS_SECTIONS` is unset | configuration/data-index gate | Pass an explicit index path or configure one in the model; do not infer a default. |
| XML parser reports malformed input | index/chain syntax | Fix the indicated line/column; validate again before HDF5 inspection. |
| Index parses but references are missing | filesystem/data installation | Correct `<directory>`/`path` or install the approved data separately; no network action is implied. |
| HDF5 opens but `filetype` is wrong | file-role mismatch | Replace the reference with the intended neutron/thermal/photon/WMP/MGXS file. |
| HDF5 type is right but a nuclide/reaction/temperature is absent | coverage/schema gate | Compare model requirements with library metadata and use a compatible library. |
| Chain parses but daughter/reaction/FPY is missing | chain coverage | Inspect `Chain.nuclides`, `chain.reactions`, and fission yields; select or generate a better chain. |
| Coupled operator raises missing cross sections | coupled data gate | Validate the model material override and configured index; then check HDF5 references and neutron material names. |
| Independent operator has wrong result dimensions | MicroXS/flux contract | Compare `(nuclide, reaction, group)` shape, flux lengths, material order, and group edges. |
| Results load but reaction-rate query is empty | output-file contract | Confirm integration used `write_rates=True`; inspect reaction index and result file type. |
| Restart says timesteps/source rates differ | continuation contract | Reuse the exact normalized prefix and matching power/rate convention, or do an append restart without `continue_timesteps`. |
| MGXS input reads but transport fails | executable/data/model MG gate | Check `energy_mode`, `mgxs.h5` metadata, material/macroscopic names, executable, and data-independent HDF5 schema separately. |

## Index and path failures

### “No cross_sections.xml” or unset configuration

`cross_sections.xml` is not automatically created by importing OpenMC. The
runtime can get it from `OPENMC_CROSS_SECTIONS`, `openmc.config['cross_sections']`,
or a `Materials.cross_sections` override. Prefer the explicit model/materials
path when a case must be reproducible. Verify the value is the intended file,
not merely a non-empty environment variable.

Run:

```bash
python path/to/validate_data_paths.py \
  --cross-sections /explicit/path/cross_sections.xml
```

If the script reports `MISSING_DATA_PATH`, fix the path or data installation. Do not
interpret a missing index as a malformed model. If no index exists, document the
continuous-energy gate as blocked and stop before transport.

### Relative `<directory>` and `<library path>` confusion

The index may contain one `<directory>` root and relative library/chain paths.
The script prints resolved references so a failure from arbitrary cwd is
reproducible. Check for:

- a `<directory>` that points to a parent that no longer exists;
- a typo or case mismatch in `path` (important on case-sensitive systems);
- a path accidentally relative to the invoking shell rather than the index;
- a stale symlink or permission error; and
- an index copied without the data directory it describes.

Do not rewrite all paths to checkout/private absolute paths in a runtime skill.
For a portable case, keep the index and data tree together or make the runtime
path an explicit user input.

### Malformed XML

The validator reports the XML parser's line/column. Repair quoting, closing
tags, duplicate/broken attributes, or truncated files first. A chain XML and a
cross-section index have different roots and schemas; passing one to the other
can produce a parse success followed by a semantic failure. Validate each file
with the API appropriate to its role.

## HDF5 and coverage failures

A path-exists result is not HDF5 validation. The validator's lightweight check
reports root `filetype`, two-value `version`, and listed top-level groups; then
use `h5py` or the corresponding OpenMC class for a prepared file. Typical role checks are:

- neutron: `IncidentNeutron.from_hdf5(path)` and expected nuclide, temperature,
  reaction, and energy-grid coverage;
- photon: `IncidentPhoton.from_hdf5(path)` and expected element/interaction
  coverage;
- thermal: `ThermalScattering.from_hdf5(path)` and expected table/temperature;
- WMP: the WMP data reader and expected nuclides; and
- MGXS: root `filetype='mgxs'`, compatible version/group edges, and the datasets
  required by the selected model and fission/scattering physics.

If `h5py` cannot open a file, report corruption/permissions separately from a
wrong file type. If an HDF5 file's declared type is right but a model nuclide is
absent, do not “fix” the model by silently removing that nuclide. Resolve the
library/model coverage decision with the user or documented case owner.

A chain file is independent of the cross-section index. `DataLibrary` can
register a chain as `type='depletion_chain'`, but the chain remains XML and its
path must exist. A chain containing `U235` does not imply a neutron HDF5 library
contains `U235`.

## ENDF/ACE processing failures

- If `Evaluation(...)` cannot parse an ENDF file, check that the file is a
  complete ENDF-6 evaluation and that the selected material starts at the
  expected record. Do not treat an ACE table as ENDF.
- If `ace.Library` cannot find a table, inspect the table name/ZAID and the
  metastable convention (`nndc` versus `mcnp`).
- If `from_ace()` or `from_endf()` succeeds but transport later fails, inspect
  exported HDF5 metadata and temperatures; successful conversion is not proof
  of complete reaction or thermal coverage.
- If `from_njoy()` is needed, verify an explicitly approved NJOY executable and
  ENDF inputs. It is a processing job that may be expensive and is outside the
  read-only validation path. Do not download ENDF or invoke NJOY as an automatic
  repair.

## Chain, naming, and matrix failures

Chain and material names must match the same nuclide naming convention. Common
failures include `Xe135_m1` versus `Xe135`, a missing daughter, a reaction name
not in the chain's supported reaction map, or an fission product yield table at
the wrong energy. Inspect:

```python
chain = openmc.deplete.Chain.from_xml("chain.xml")
print(len(chain), chain.reactions)
print([n.name for n in chain.unstable_nuclides[:10]])
```

For a synthetic check, create a tiny chain with two nuclides, one decay mode,
and one reaction, then verify `chain.form_matrix()` with a known reaction-rate
array. This catches naming/branching/matrix problems without transport.

If a chain is reduced, record the reduction depth and what paths were omitted.
A missing transmutation cross section can mean “reaction is not simulated,” not
necessarily that the solver crashed. Compare the chain reaction set to the
operator's data/MicroXS reaction set before interpreting atom changes.

## Depletion setup and normalization failures

### Coupled operator

Check in this order:

1. `model.materials.cross_sections` or `openmc.config['cross_sections']` names a
   parsed index.
2. The index's neutron HDF5 files exist and contain all initial/model nuclides
   at the requested temperature.
3. `openmc.lib` and the executable are available and built for the installed
   Python package/version.
4. Every depleted material has a meaningful volume, and repeated-material
   differentiation is intentional.
5. The chain, fission-yield mode, reaction-rate mode, and normalization agree.

`normalization_mode='source-rate'` requires fixed-source settings and source
rates. `fission-q`/power normalization assumes an eigenvalue-style calculation
and relies on chain Q values. `energy-deposition` requires the relevant heating
score/data. A rate of zero may intentionally skip transport for a decay-only
step; it is not proof that coupled transport is healthy.

### Independent operator and MicroXS

For `IndependentOperator`, inspect:

- equal counts of materials, flux arrays, and MicroXS objects;
- flux length equals the MicroXS group count;
- `MicroXS.data.shape[:2]` equals the nuclide/reaction axis lengths;
- every reaction label is recognized by the chain/depletion API;
- values are microscopic cross sections in barns, not macroscopic cm⁻¹; and
- `from_nuclides(..., nuc_units=...)` matches the concentration data.

A zero flux produces zero MicroXS in the documented helper. A missing nuclide
in a MicroXS table can therefore produce a physically zero reaction rate without
an exception. Report the coverage explicitly.

### Timesteps and signs

Timesteps are interval lengths. Convert days/hours/years only through the
integrator's supported units or explicit `(value, unit)` tuples. For `MWd/kg`,
check initial heavy-metal mass and power. Use short steps/substeps when decay
constants are large.

Transfer-rate signs: positive removal, negative feed. External-source signs:
positive feed, negative removal. Confirm both in a one-material synthetic case
before applying a long run. A wrong sign can produce plausible-looking but
incorrect inventories.

## Restart and results failures

To append a new run, pass `Results(old_file)` as `prev_results` and use the new
schedule normally. To continue a partially specified schedule, pass the full
old prefix plus the new suffix and set `continue_timesteps=True`; OpenMC checks
normalized prior interval lengths and source rates. Do not change from
`power` to `source_rates` or alter units/values in the prefix and call it a
continuation.

If an integrator requiring history is changed across a restart, verify its
restart support and saved rates. If a previous file has no reaction rates, a
later result query cannot reconstruct them. If a restart file contains only a
final `[t,t]` point, use the stored beginning time semantics and inspect the
result list before selecting the next interval.

For result queries:

- `get_atoms()` returns times in requested `s`, `min`, `h`, `d`, or Julian `a`
  units and can return atoms, atom/b-cm, or atom/cm³;
- `get_mass()` uses atomic-mass data and needs valid material volume for density;
- `get_activity()` needs half-life data from the selected chain or its fallback
  policy; and
- `get_reaction_rate()` requires stored reaction rates and matching material,
  nuclide, and reaction indexes.

Do not compare a keff/value without its uncertainty, time unit, chain, data
library, normalization, and integrator settings.

## MGXS and multigroup failures

If an MGXS library builds but a generated multigroup input fails:

1. inspect `mgxs.h5` root `filetype`, version, `energy_groups`, delayed groups,
   and ascending group boundaries;
2. check that each material/macroscopic name used by the model has a matching
   library group and temperature;
3. check representation (`isotropic` versus angular), scatter format/order,
   matrix shape/order, and required fission/chi datasets;
4. confirm the model's energy mode and material cross-section path; and
5. only then run a tiny native multigroup input if the executable gate passes.

MGXS tally generation requires a statepoint from transport; HDF5 schema checks
and object/tally construction do not. A group-order mismatch can preserve array
shapes while changing the physical result, so record edges and index convention
in every conversion.

## Escalation and sibling routes

- Build, executable, environment variables, and subprocess execution: use
  [setup-runtime](../../setup-runtime/SKILL.md).
- Materials, geometry, model XML, volumes, and settings object validation: use
  [model-geometry](../../model-geometry/SKILL.md).
- Statepoint, summary, tally, and generic HDF5 outputs: use
  [tallies-results](../../tallies-results/SKILL.md).
- `openmc.lib`, C API, CMake feature flags, MPI, DAGMC, or optional native
  backends: use [advanced-solvers](../../advanced-solvers/SKILL.md).

When escalating, hand off the exact command, package/version, gate statuses,
resolved data paths (without private checkout paths), parser/HDF5 observations,
chain/operator/integrator settings, and the smallest reproducible fixture.
