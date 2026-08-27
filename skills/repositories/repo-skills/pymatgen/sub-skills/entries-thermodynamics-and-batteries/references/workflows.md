# Workflows: Entries, Compatibility, Batteries, and Borg

## Prepare Entries for Phase Diagrams

Use this when entries originate from local calculations, saved Monty JSON, in-memory calculations, or an external-data handoff.

```python
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility

compat = MaterialsProject2020Compatibility(check_potcar=False)  # keep True when reliable POTCAR metadata exists
processed_entries = compat.process_entries(raw_entries, inplace=False, on_error="warn")

if not processed_entries:
    raise ValueError("No compatible entries remain after compatibility processing.")

phase_diagram = PhaseDiagram(processed_entries)
```

Checklist before correction:

- Confirm entry energies are total eV per represented composition.
- Preserve `parameters["run_type"]`, `parameters["hubbards"]`, `parameters["potcar_spec"]` or `parameters["potcar_symbols"]`, and optional `parameters["software"]`.
- Prefer `ComputedStructureEntry` when anion type, host-framework grouping, volume, or DFT mixing depends on geometry.
- Preserve trusted `data["oxidation_states"]`, `data["oxide_type"]`, or `data["sulfide_type"]` when available.
- Use `inplace=False` while exploring so uncorrected entries remain available for diagnosis.
- Use `on_error="warn"` or `on_error="raise"` when entries disappear unexpectedly; default `"ignore"` silently filters.
- Build `PhaseDiagram` only after checking that enough elemental/reference entries remain for the chemical system.

## Mix GGA/GGA+U with r2SCAN

Use `MaterialsProjectDFTMixingScheme` only when the user really has two functional sets and enough base entries.

```python
from pymatgen.entries.mixing_scheme import MaterialsProjectDFTMixingScheme

mixing = MaterialsProjectDFTMixingScheme(check_potcar=False)
mixed_entries = mixing.process_entries(all_computed_structure_entries, inplace=False, verbose=True)
```

Checklist:

- Pass all relevant entries in one list; do not process functional subsets independently and combine them later.
- Use `ComputedStructureEntry` objects for automatic matching unless a trusted `mixing_state_data` table is supplied.
- Ensure `run_type` distinguishes the functional family, such as `"GGA"`, `"GGA+U"`, and `"r2SCAN"`.
- Confirm the base `run_type_1` entries form a complete phase diagram for the chemical system.
- Keep POTCAR checks enabled only when both functional sets carry reliable POTCAR metadata.
- Report retained and filtered entry counts by `run_type` before interpreting energies.

## Group Entries by Composition

Use composition grouping to inspect duplicates or choose representative entries for summaries.

```python
from pymatgen.entries.entry_tools import group_entries_by_composition

groups = group_entries_by_composition(processed_entries)
for group in groups:
    best = group[0]
    print(best.reduced_formula, best.energy_per_atom, len(group))
```

Good uses:

- Inspect duplicate formulas from multiple sources.
- Find likely ground-state candidates for a user-facing table.
- Check which compositions survived compatibility processing.
- Keep all polymorphs for phase diagrams unless the task explicitly asks for one entry per composition.

## Group Entries by Structure or Host Framework

Use structural grouping when entries have structures and the question depends on topotactic similarity.

```python
from pymatgen.entries.entry_tools import group_entries_by_structure

groups = group_entries_by_structure(
    computed_structure_entries,
    species_to_remove=["Li"],
    ltol=0.2,
    stol=0.4,
    angle_tol=5,
    ncpus=None,
)
```

Checklist:

- Confirm every entry is a `ComputedStructureEntry` or otherwise has `.structure`.
- Use `species_to_remove` for insertion-host comparison, not for conversion reactions where the framework changes.
- Use serial grouping for small interactive tasks; multiprocessing is more useful for large trusted sets.
- If grouping fails, decide whether the mismatch is true framework change, different relaxation/prototype, or overly strict tolerances.

## Estimate Capacity from an Oxidized Structure

Use `BatteryAnalyzer` for quick charge-balance capacity estimates from a structure with oxidation states.

```python
from pymatgen.apps.battery.analyzer import BatteryAnalyzer
from pymatgen.core import Lattice, Structure

structure = Structure(
    Lattice.orthorhombic(10.3, 6.0, 4.7),
    ["Li", "Fe", "P", "O", "O", "O", "O"],
    [
        [0.0, 0.0, 0.0],
        [0.5, 0.5, 0.5],
        [0.25, 0.25, 0.25],
        [0.30, 0.30, 0.30],
        [0.70, 0.30, 0.30],
        [0.30, 0.70, 0.30],
        [0.30, 0.30, 0.70],
    ],
)
structure.add_oxidation_state_by_element({"Li": 1, "Fe": 2, "P": 5, "O": -2})

analyzer = BatteryAnalyzer(structure, working_ion="Li")
print(analyzer.max_ion_removal)
print(analyzer.get_max_capgrav(insert=False))
print(analyzer.get_removals_int_oxid())
```

When the input structure has no oxidation states, make a copy and assign documented assumptions before constructing the analyzer. Explain that this result does not establish phase stability or voltage.

## Build an Insertion Electrode

Use this when entries represent topotactically related charge states such as `TiO2`, `Li0.5TiO2`, and `LiTiO2`.

```python
from pymatgen.apps.battery.insertion_battery import InsertionElectrode
from pymatgen.core.entries import ComputedEntry

working_ion_entry = ComputedEntry("Li", -1.9)
electrode = InsertionElectrode.from_entries(topotactic_entries, working_ion_entry)

summary = {
    "framework": electrode.framework_formula,
    "steps": electrode.num_steps,
    "voltage_avg": electrode.get_average_voltage(),
    "capacity_grav": electrode.get_capacity_grav(),
    "capacity_vol": electrode.get_capacity_vol(),
}
```

Validation checklist:

- Entries should preserve the same host framework after removing the working ion.
- At least two stable entries with different working-ion fractions are needed for a voltage path.
- `working_ion_entry` must be a single-element entry with an energy reference on the same energy scale.
- If using plain `ComputedEntry` objects, provide `entry.data["volume"]` when volumetric capacity is needed.
- Use `strip_structures=True` only when entries actually carry structures and the output should be lighter.
- If framework validation fails, use structural grouping or switch to conversion-electrode logic.

## Build a Conversion Electrode

Use this when the framework changes and the voltage path is derived from a phase diagram.

```python
from pymatgen.apps.battery.conversion_battery import ConversionElectrode
from pymatgen.core import Composition

electrode = ConversionElectrode.from_composition_and_entries(
    Composition("FeF3"),
    entries_in_li_fe_f_system,
    working_ion_symbol="Li",
    allow_unstable=False,
)

if electrode is None:
    raise ValueError("The phase diagram produced fewer than two conversion steps.")

print(electrode.get_average_voltage())
print(electrode.get_capacity_grav())
print(electrode.get_summary_dict(print_subelectrodes=False)["reactions"])
```

Validation checklist:

- Entries must span the full chemical system, including elemental references and the working-ion reference.
- Apply compatibility before the phase diagram used by conversion-electrode construction.
- Keep `allow_unstable=False` for production interpretations. Use `allow_unstable=True` only for exploratory comparison and state the metastability assumption.
- If the constructor returns `None`, explain that the provided entries do not define a multi-step conversion path.

## Assimilate Local VASP Outputs with Borg

Run Borg only when the user supplies a calculation directory tree and accepts a filesystem scan.

```python
from pymatgen.apps.borg.hive import VaspToComputedEntryDrone
from pymatgen.apps.borg.queen import BorgQueen

drone = VaspToComputedEntryDrone(inc_structure=True, data=["efermi"])
queen = BorgQueen(drone, rootpath=user_vasp_root, number_of_drones=1)
entries = [entry for entry in queen.get_data() if entry is not None]
```

Safe operating guidance:

- Start with a narrow calculation root, not a home directory or broad project root.
- Start with `number_of_drones=1` for reproducible errors; increase only after the scan is trusted.
- Prefer `VaspToComputedEntryDrone` when `vasprun.xml*` exists and compatibility metadata matters.
- Use `SimpleVaspToComputedEntryDrone` only when the smaller required VASP files are complete and `vasprun.xml*` is unavailable.
- Save expensive scan results with `queen.save_data("entries.json.gz")`; reload with `queen.load_data("entries.json.gz")` instead of rescanning.
- Filter `None` results and report skipped directories.

## Reaction Energy from Entries

After entries are compatibility processed, route reaction calculations to core reaction APIs.

```python
from pymatgen.analysis.reaction_calculator import ComputedReaction

reaction = ComputedReaction(reactant_entries, product_entries)
print(reaction)
print(reaction.calculated_reaction_energy)
```

Checks:

- Use entries from the same correction scheme and energy reference.
- Make sure reactant and product entries are the desired phases, not merely the first formula match.
- If multiple polymorphs exist, decide whether to use phase-diagram ground states or user-specified metastable phases.

## Minimal Smoke Command

Run the bundled smoke script from any checkout or environment where `pymatgen` is installed:

```bash
python ../scripts/entry_battery_smoke.py
```

Expected signal: imports succeed, an unoxidized structure is diagnosed, an oxidized structure supports a positive capacity estimate, a tiny insertion voltage pair can be constructed, compatibility and Borg objects instantiate without touching user directories, and an intentionally underdetermined battery case is reported instead of hidden.
