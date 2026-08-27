# API Reference: Entries, Compatibility, Batteries, and Borg

## Installed Baseline

- Verified package facts for this skill generation: `pymatgen==2026.5.4`, `pymatgen-core==2026.5.18`, and Python `>=3.11`.
- Base `pymatgen` is enough for entry classes, compatibility classes, battery classes, and Borg API inspection. Optional extras should be treated as workflow-specific, not assumed.
- `pymatgen-core` owns many core objects; higher-level compatibility, battery, Borg, CLI, and external integrations live in `pymatgen`.

## Entry Classes

Prefer explicit imports that work with the package split:

```python
from pymatgen.core.entries import ComputedEntry, ComputedStructureEntry, PDEntry
from pymatgen.entries.computed_entries import GibbsComputedStructureEntry
from pymatgen.entries.entry_tools import EntrySet, group_entries_by_composition, group_entries_by_structure
```

- `ComputedEntry(composition, energy, correction=0.0, energy_adjustments=None, parameters=None, data=None, entry_id=None)` stores composition, total energy, corrections, provenance parameters, arbitrary data, and optional id.
- `ComputedStructureEntry(structure, energy, correction=0.0, composition=None, energy_adjustments=None, parameters=None, data=None, entry_id=None)` adds a `Structure`; use it when geometry affects anion classification, host-framework matching, volumes, or DFT functional mixing.
- `PDEntry` is lightweight for phase diagrams, but it does not carry the same calculation provenance as `ComputedEntry`.
- `pymatgen.entries.computed_entries` is a backwards-compatible shim for many entry objects; prefer `pymatgen.core.entries` for `ComputedEntry` and `ComputedStructureEntry` in new snippets.
- Energy passed to entry constructors is total energy for the composition represented by the entry, not energy per atom unless the calling code has explicitly normalized the composition.

## Compatibility Classes

Primary imports:

```python
from pymatgen.entries.compatibility import CompatibilityError, MaterialsProject2020Compatibility
from pymatgen.entries.mixing_scheme import MaterialsProjectDFTMixingScheme
```

Important APIs and behavior:

- `MaterialsProject2020Compatibility(compat_type="Advanced", correct_peroxide=True, strict_anions="require_bound", check_potcar=True, check_potcar_hash=False, config_file=None)` implements the MP 2020 energy correction scheme with uncertainty and MP-style GGA/GGA+U mixing.
- `process_entries(entries, clean=True, verbose=False, inplace=True, n_workers=1, on_error="ignore")` returns compatible corrected entries and excludes incompatible entries. It mutates input entries when `inplace=True`.
- `process_entry(entry, inplace=True, **kwargs)` handles one entry and may return `None` when incompatible.
- `explain(entry)` prints uncorrected energy, applied adjustments, and corrected energy; use it after processing a retained entry.
- `MaterialsProjectDFTMixingScheme(structure_matcher=None, run_type_1="GGA(+U)", run_type_2="r2SCAN", compat_1=MaterialsProject2020Compatibility(...), compat_2=None, fuzzy_matching=True, check_potcar=True)` mixes two functional sets and normally needs `ComputedStructureEntry` objects when it generates matching state internally.

Metadata expected before compatibility:

- `entry.parameters["run_type"]`: usually `"GGA"`, `"GGA+U"`, or `"r2SCAN"` depending on scheme.
- `entry.parameters["hubbards"]`: nonzero Hubbard U settings for GGA+U, such as `{"Fe": 5.3}`. Missing `hubbards` is interpreted as a GGA run by MP 2020 compatibility.
- `entry.parameters["potcar_spec"]` or `entry.parameters["potcar_symbols"]`: required when POTCAR checks are enabled.
- `entry.parameters["software"]`: defaults internally as VASP in relevant checks; set it deliberately for non-VASP provenance.
- `entry.data["oxidation_states"]`, `entry.data["oxide_type"]`, or `entry.data["sulfide_type"]`: optional trusted hints that make O/S corrections more reliable.
- Use `check_potcar=False` only when POTCAR metadata is unavailable and the user accepts weaker validation. Never fabricate POTCAR metadata.

## Entry Grouping and Containers

```python
from pymatgen.entries.entry_tools import EntrySet, group_entries_by_composition, group_entries_by_structure
```

- `group_entries_by_composition(entries, sort_by_e_per_atom=True)` groups by reduced formula and sorts each group by `energy_per_atom` when requested.
- `group_entries_by_structure(entries, species_to_remove=None, ltol=0.2, stol=0.4, angle_tol=5, primitive_cell=True, scale=True, comparator=None, ncpus=None)` groups `ComputedStructureEntry` objects using structure-matching semantics.
- `species_to_remove=["Li"]` or another working ion helps compare battery host frameworks after removing mobile ions.
- `EntrySet(entries)` exposes chemical-system, ground-state, and filtering helpers useful before phase-diagram or duplicate-entry review.

## Thermodynamics Handoff

After compatibility processing, use core analysis classes as needed:

```python
from pymatgen.analysis.phase_diagram import PhaseDiagram
from pymatgen.analysis.reaction_calculator import ComputedReaction
```

- Build `PhaseDiagram(processed_entries)` only after filtering incompatible entries and checking that elemental/reference entries exist for the target chemical system.
- Use `ComputedReaction(reactant_entries, product_entries)` for reaction energies from selected entries.
- Keep Pourbaix, interfacial reactivity, slab thermodynamics, and electrochemical surface workflows in the surfaces/electrochemistry sub-skill.

## Battery Analyzer

```python
from pymatgen.apps.battery.analyzer import BatteryAnalyzer
```

Signature: `BatteryAnalyzer(struct_oxid, working_ion="Li", oxi_override=None)`.

- `struct_oxid` must have oxidation states on every site; plain elemental species are rejected.
- `working_ion` can be a string symbol or `Element`.
- Working-ion charge is inferred from elemental oxidation-state extrema unless `oxi_override` supplies a value.
- Useful members include `max_ion_removal`, `max_ion_insertion`, `get_max_capgrav(remove=True, insert=True)`, `get_max_capvol(remove=True, insert=True, volume=None)`, and `get_removals_int_oxid()`.
- Capacity from `BatteryAnalyzer` is a redox/charge-balance estimate; it does not prove voltage, phase stability, diffusion, or site accessibility.

## Insertion Batteries

```python
from pymatgen.apps.battery.insertion_battery import InsertionElectrode, InsertionVoltagePair
```

- Direct dataclass signature: `InsertionElectrode(voltage_pairs, working_ion_entry, framework_formula, stable_entries, unstable_entries)`.
- Prefer `InsertionElectrode.from_entries(entries, working_ion_entry, strip_structures=False)` for normal construction.
- `entries` should be topotactically related entries with a common host framework after removing the working ion.
- `working_ion_entry` must be a single-element entry, for example `ComputedEntry("Li", energy)`.
- Voltage-pair validation requires the working ion to be present in at least one endpoint, different working-ion fractions between endpoints, an elemental working-ion reference, and the same framework after removing the working ion.
- Common outputs include `voltage_pairs`, `max_voltage`, `min_voltage`, `num_steps`, `get_average_voltage()`, `get_capacity_grav()`, `get_capacity_vol()`, `get_specific_energy()`, `get_energy_density()`, `get_sub_electrodes()`, and `get_summary_dict()`.
- If `strip_structures=True`, input entries must carry structures; structures are converted to lighter entries and volumes are stored under `entry.data["volume"]`.

## Conversion Batteries

```python
from pymatgen.apps.battery.conversion_battery import ConversionElectrode, ConversionVoltagePair
```

- Direct dataclass signature: `ConversionElectrode(voltage_pairs, working_ion_entry, framework_formula, initial_comp_formula)`.
- Prefer `ConversionElectrode.from_composition_and_entries(comp, entries_in_chemsys, working_ion_symbol="Li", allow_unstable=False)` or `ConversionElectrode.from_composition_and_pd(comp, pd, working_ion_symbol="Li", allow_unstable=False)`.
- Conversion workflows require a phase diagram for the full relevant chemical system, including the working-ion elemental reference.
- With `allow_unstable=False`, the starting composition must be stable on the phase diagram.
- The constructor may return `None` when the element profile produces fewer than two voltage steps.
- Summary methods mirror the abstract electrode API and include average voltage, capacities, energy density, sub-electrodes, and reaction summaries.

## Borg VASP Assimilation

```python
from pymatgen.apps.borg.hive import SimpleVaspToComputedEntryDrone, VaspToComputedEntryDrone
from pymatgen.apps.borg.queen import BorgQueen
```

- `VaspToComputedEntryDrone(inc_structure=False, parameters=None, data=None)` parses `vasprun.xml*` and returns `ComputedEntry` or `ComputedStructureEntry`.
- The default drone records compatibility-critical parameters: `is_hubbard`, `hubbards`, `potcar_spec`, `potcar_symbols`, and `run_type`.
- `SimpleVaspToComputedEntryDrone(inc_structure=False)` parses smaller VASP files but needs enough files such as `INCAR`, `POTCAR`, `CONTCAR`, `OSZICAR`, and `POSCAR`.
- `BorgQueen(drone, rootpath=None, number_of_drones=1)` scans a directory tree immediately when `rootpath` is provided, or can be instantiated empty for later `load_data`.
- `get_data()` returns assimilated objects; `save_data(filename)` and `load_data(filename)` persist Monty JSON, with compression inferred from suffixes such as `.gz` or `.bz2`.
- Borg is filesystem- and calculation-output-sensitive. Use it only on user-provided calculation directories, never as an implicit broad scan.

## Legacy Import Caution

- Older material may use `pymatgen.borg.hive` or `pymatgen.borg.queen`; current code uses `pymatgen.apps.borg.hive` and `pymatgen.apps.borg.queen`.
- Explicit imports from `pymatgen.core`, `pymatgen.entries`, `pymatgen.analysis`, and `pymatgen.apps` are more robust than root-level imports in modern package layouts.
