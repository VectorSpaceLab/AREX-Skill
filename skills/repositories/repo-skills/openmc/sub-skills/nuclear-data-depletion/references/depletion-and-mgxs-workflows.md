# Depletion and MGXS workflows

This reference turns the public depletion and multigroup APIs into a decision
procedure. For file schemas and the index/data distinction, read
[data-formats.md](data-formats.md). For failures, read
[troubleshooting.md](troubleshooting.md) before rerunning a case.

## 1. Select the operator from the available physics inputs

OpenMC separates the reaction-rate **operator** from the Bateman-equation
**integrator**. The operator turns a composition and a source/normalization
value into an eigenvalue plus reaction rates; the integrator advances nuclide
inventories. This boundary is why the same integrator family can be used with
coupled and independent operators.

### Transport-coupled: `CoupledOperator`

Use `openmc.deplete.CoupledOperator(model, chain_file=...)` when reaction rates
must come from OpenMC continuous-energy transport. The model needs materials,
geometry, settings, and a native transport-capable build. The operator resolves
cross sections from `model.materials.cross_sections` first and otherwise from
`openmc.config['cross_sections']`; a missing value is a data error, not a
geometry error. Its implementation uses `openmc.lib`, so a successful base
`import openmc` does not satisfy this gate.

Before constructing it:

- assign a finite `Material.volume` to every depleted material; for a 2-D model
  this is an area in cm² and power may be W/cm;
- mark non-fissionable materials explicitly with `depletable=True` if they must
  deplete, or leave the default fissionable-material selection when appropriate;
- make chain reaction names and cross-section library material names agree;
- choose `normalization_mode`: `fission-q` uses chain fission Q values,
  `energy-deposition` scores heating/energy deposition, and `source-rate` is for
  fixed-source calculations; and
- decide whether repeated instances of one material need
  `diff_burnable_mats=True`. Differentiation gives locations separate
  compositions and rates; the original volume is divided according to the
  selected volume method, and memory/tally cost increases.

The default `fission-q` normalization can omit indirect neutron/photon heating
and over-deplete when its Q values do not represent the desired recoverable
energy. Use a deliberate fission-Q override or energy-deposition normalization
only when the corresponding data and scoring method are available. Do not
compare results across cases that silently use different normalization modes.

### Transport-independent: `IndependentOperator`

Use `openmc.deplete.IndependentOperator` when flux spectra and microscopic
multigroup cross sections are already supplied. This is useful for a
transport-free depletion calculation or for coupling rates from another
transport code. The constructor requires equal-length `materials`, `fluxes`, and
`micros` lists. `IndependentOperator.from_nuclides()` is a one-material helper;
its concentration input is `atom/b-cm` by default or `atom/cm3`, and it assigns
a volume and marks the material depletable.

For an independent case, verify all of the following before integrating:

- each flux has one entry per energy group represented by its `MicroXS`;
- each `MicroXS.data` has shape `(nuclide, reaction, group)` and values in barns;
- material IDs/order, chain nuclides, and MicroXS axes refer to the same domains;
- `source-rate` means the supplied rate/flux is used directly, whereas
  `fission-q` scales reaction rates so the requested power agrees with fission
  Q and the chain; and
- a zero source rate intentionally creates a decay-only step with zero reaction
  rates. It does not test cross-section availability or transport.

An independent operator does not run OpenMC transport to form rates, but package
imports and helper paths can still touch native bindings in this OpenMC release.
Classify the API, native-library, and data gates separately rather than claiming
that “independent” means “no native dependency anywhere.”

### Decay-only, activation, and R2S

A chain plus zero rates can model decay-only evolution. The transport-free
`deplete_no_transport` and decay-only test patterns are good bounded checks:
load a small explicit chain, use a tiny `MicroXS` or empty MicroXS as
appropriate, integrate short steps, and inspect atoms. They do not validate
continuous-energy transport.

`openmc.deplete.R2SManager` coordinates a rigorous two-step workflow: neutron
transport and flux/MicroXS extraction, activation/depletion, decay photon-source
construction, and photon transport. It requires both neutron and photon models,
spatial domains/volumes, a chain, and native/data gates. Keep R2S as a
transport-dependent workflow; only its object construction and argument checks
are data-free candidates.

## 2. Prepare a chain and operator contract

Use this order:

1. Parse or construct the chain with `Chain.from_xml(path)` or an explicit
   `Chain` object. Inspect `chain.nuclides`, `chain.reactions`, stable/unstable
   sets, and fission-yield entries.
2. Match model material names and chain names, including metastables such as
   `Xe135_m1`. Decide whether a missing daughter, reaction, or fission yield is
   an intentional reduction or a data defect.
3. For coupled mode, validate the cross-section index and referenced HDF5 files,
   then verify neutron data for the initial and expected transmutation nuclides.
   The chain may contain nuclides for which the continuous-energy library has no
   transport data.
4. For independent mode, verify MicroXS coverage instead of looking for
   `cross_sections.xml`; a MicroXS table is the input rate model. A chain is
   still needed for decay and matrix paths.
5. Record volume, concentration units, normalization mode, fission-yield mode,
   reaction-rate mode, and whether rates will be persisted.

## 3. Choose timesteps, normalization, and solver

Integrator constructors include `PredictorIntegrator`, `CECMIntegrator`,
`CELIIntegrator`, `CF4Integrator`, `EPCRK4Integrator`, `LEQIIntegrator`, and
stochastic-implicit variants. Use the simplest method that meets accuracy and
cost needs; higher-order/predictor-corrector methods call the operator at
intermediate compositions and therefore cost more transport evaluations in
coupled mode. `PredictorIntegrator` is a first-order predictor. `CECMIntegrator`
uses a beginning-rate predictor and a midpoint-rate corrector.

Timesteps are **interval lengths, not cumulative times**. They may be floats with
one `timestep_units` value or `(value, unit)` tuples. Supported units include
seconds (`s`), minutes (`min`), hours (`h`), days (`d`), Julian years (`a`), and
burnup `MWd/kg` where the initial heavy-metal inventory and power determine the
elapsed seconds. Validate that:

- every interval is positive and the number of powers/rates matches the number
  of intervals;
- `power` is W (or W/cm for a 2-D area convention), `power_density` is W/gHM,
  and `source_rates` is neutron/sec or the fixed-source rate expected by the
  operator;
- `source-rate` normalization is paired with `source_rates`, not a power value;
- `fission-q` normalization is paired with `power` or `power_density`; and
- large decay constants times interval lengths are addressed with smaller
  intervals or `substeps > 1`. Substeps subdivide an interval for the matrix
  solve; they do not create new transport tallies in the same way as a
  predictor-corrector stage.

The default CRAM solver is `cram48`; `cram16` is available. A custom solver must
accept `(A, n0, t, substeps=1)` and return an array with the same shape. The
integrator clips negative number densities after a solve, but clipping is not a
substitute for investigating an unstable timestep, bad chain, or bad rates.

A minimal contract is conceptually:

```python
op = openmc.deplete.IndependentOperator(
    materials, fluxes, micros, chain_file="chain.xml",
    normalization_mode="source-rate")
integrator = openmc.deplete.PredictorIntegrator(
    op, timesteps=[10.0, 10.0], source_rates=[1.0, 1.0],
    timestep_units="d", substeps=1)
integrator.integrate(path="depletion_results.h5", write_rates=True)
```

This is a transport-free *shape and semantics* example only. It becomes a
scientific run only after the chain, MicroXS units, material composition,
normalization, and reaction-rate provenance are validated.

## 4. Transfer and external source terms

`Integrator.add_transfer_rate()` models inventory-proportional feed/removal.
Its sign is easy to reverse: positive means removal and negative means feed.
Units can be `1/s`, `1/min`, `1/h`, `1/d`, or `1/a`. Components can be elements
or nuclides, but do not mix an element component with one of its nuclides for the
same material/rate definition. A `destination_material` transfers the selected
inventory into another material; without one, the material leaves the tracked
system.

`Integrator.add_external_source_rate()` adds a constant mass feed/removal term.
Its sign convention is the opposite: positive means feed and negative means
removal. Composition values are element/nuclide weight fractions, units are
`g/s`, `g/min`, `g/h`, `g/d`, or `g/a`, and optional timestep indices restrict
when the term is active. Check source-term units and signs in a small matrix
case before coupling transport.

## 5. Restart versus continuation

A restart and a continuation both consume prior results, but their schedules
have different meanings:

- **Append/restart:** load `previous_results = Results(old_path)` and pass it as
  `prev_results` to a newly created operator. A normal integrator run appends
  new intervals after the stored state. The first beginning-of-step state is
  recovered from the last result, and intermediate integrator state may make
  changing schemes inappropriate for methods that need history.
- **Continuation:** pass the same previous results and set
  `continue_timesteps=True`. The new integrator must receive the complete
  original schedule prefix and matching power/power-density/source-rate prefix;
  OpenMC checks them and executes only the new suffix. A mismatch in interval
  lengths, units after normalization, or source rates is an error, not an
  opportunity to guess.

`integrate(path=..., final_step=True, write_rates=False)` writes a
`depletion_results.h5` file. `final_step=False` avoids the final operator
transport evaluation (the implementation uses a zero source rate for that final
record); use this only when the saved final rates/keff semantics are understood.
`write_rates=True` is required if later `Results.get_reaction_rate()` analysis
needs stored rates; omitting it reduces file size and leaves rate arrays empty.
The results file stores times in seconds even when input timesteps use days or
burnup. Use `Results.get_*` unit arguments for presentation, not for altering
the stored data.

A restart case is not valid merely because `Results(path)` opens. Check the
filetype/version, material IDs and volumes, nuclide ordering, last time point,
source rate, and whether the new chain/model describes the same inventory.
Continue with [troubleshooting.md](troubleshooting.md) for mismatch recovery.

## 6. MGXS and MicroXS workflows

### Generate an MGXS library for multigroup transport

Use this when the output is a runtime `mgxs.h5` or multigroup model:

1. Construct a validated continuous-energy model and choose ascending group
   edges with `openmc.mgxs.EnergyGroups`.
2. Configure `openmc.mgxs.Library`: `domain_type` (`material`, `cell`,
   `distribcell`, `universe`, or `mesh`), domains, `mgxs_types`, `by_nuclide`,
   delayed groups, scattering format/order, and angular bins as needed.
3. Build and attach its tallies, run a bounded transport case with a valid
   executable and continuous-energy library, then load the compatible
   statepoint.
4. Export the library to HDF5 or use `create_mg_mode()` to replace material and
   settings inputs. Confirm `energy_mode='multi-group'`, `materials.cross_sections`
   points to the resulting HDF5, and the generated datasets satisfy the MGXS
   format.
5. Test at least group edges, array shapes, fission/chi/scatter requirements,
   and a small input read. A successful MGXS object build before the statepoint
   is not a generated physical library.

The CE-to-MG regression cases exercise two-group structures, material/mesh
 domains, scatter matrices, multiplicity, delayed groups, and HDF5 export, but
 they require native transport and data. Without those gates, stop after API,
 tally-setup, or synthetic HDF5 validation.

### Generate MicroXS for independent depletion

`openmc.deplete.get_microxs_and_flux()` runs transport to tally flux and reaction
rates in selected material/cell/universe/mesh/filter domains, then returns
flux arrays and `MicroXS` objects. `reaction_rate_mode='direct'` returns
energy-group reaction rates; `reaction_rate_mode='flux'` collapses cross sections
to one group and can use selected direct reaction-rate tallies as overrides.
`energies` may be explicit ascending boundaries or a named group structure.
`path_statepoint` and `path_input` preserve intermediate artifacts when needed.
This helper is transport/data/native dependent despite producing transport-
independent inputs.

For a no-transport path, construct `MicroXS` from a small NumPy array, CSV, or
HDF5 file and supply fluxes from an independently documented source. Use
`MicroXS.to_csv()`, `from_csv()`, `to_hdf5()`, and `from_hdf5()` only after
checking axis labels, group count, and barn units. A zero flux is explicitly
handled as zero cross sections; treat that as a deliberate test fixture, not a
physical result.

### Preserve group ordering

`EnergyGroups` edges are low-to-high. OpenMC's group number 1 is the highest
energy group. `convert_flux_groups()` assumes compatible ranges and distributes
flux by lethargy, preserving the total flux. When comparing a MicroXS table,
MGXS HDF5 dataset, and a flux vector, write down:

```text
source group edges -> target group edges -> array order -> domain order -> units
```

Do not use a group conversion as a repair for missing data, a reversed spectrum,
or incompatible reaction definitions.

## 7. Verification ladder

Run only the lowest sufficient rung first:

1. **Data-free:** parser script `--help`; malformed/missing-reference synthetic
   XML; `EnergyGroups` construction and group conversion; `MicroXS` shape/unit
   checks; `Chain.from_xml()` with a tiny explicit chain; integrator input
   validation with a dummy operator; `Results` reader against a known result
   fixture.
2. **Prepared-file:** HDF5 root attribute and dataset/schema checks; chain
   nuclide/reaction coverage; MicroXS CSV/HDF5 round trip; MGXS HDF5 metadata.
3. **Native setup:** executable and `openmc.lib` load/version checks, without
   transport if no data is available.
4. **Data-dependent:** tiny transport, coupled depletion, MGXS tally generation,
   MicroXS extraction, R2S, or CE-to-MG regression, only when all relevant data,
   native, and runtime gates pass.

Record skipped steps and why. An API pass, XML pass, or data-index pass never
stands in for the next rung. For package/build gates, link to
[setup-runtime](../../setup-runtime/SKILL.md); for native-library boundaries,
link to [advanced-solvers](../../advanced-solvers/SKILL.md).
