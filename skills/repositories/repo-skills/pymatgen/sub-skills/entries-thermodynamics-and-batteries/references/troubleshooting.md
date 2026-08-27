# Troubleshooting: Entries, Thermodynamics, Batteries, and Borg

## Compatibility Returns No Entries

Symptoms:

- `process_entries` returns an empty list or fewer entries than expected.
- `process_entry` returns `None`.
- A later `PhaseDiagram` or battery constructor fails because references disappeared.

Likely causes:

- Missing or invalid `entry.parameters["run_type"]`.
- Missing `hubbards` metadata for a workflow that should be GGA+U-aware.
- POTCAR metadata is absent while `check_potcar=True`.
- A GGA entry is supplied for chemistry that the MP 2020 Advanced scheme expects to be GGA+U.
- Existing `energy_adjustments` conflict with newly calculated corrections.

Debug pattern:

```python
from pymatgen.entries.compatibility import MaterialsProject2020Compatibility

compat = MaterialsProject2020Compatibility(check_potcar=False)
processed = compat.process_entries(entries, inplace=False, on_error="warn")
print(len(entries), len(processed))
for entry in processed:
    compat.explain(entry)
```

Use `on_error="raise"` for the first failing entry when warnings are too noisy. Do not assume a filtered entry is physically invalid; it may simply lack required provenance metadata.

## Missing POTCAR Metadata

Symptoms:

- Errors mention `potcar_spec`, `potcar_symbols`, or incompatible POTCARs.
- Hand-built entries fail MP compatibility despite plausible formulas and energies.

Cause:

- MP compatibility checks compare VASP POTCAR metadata to expected input-set settings when enabled.

Fixes:

- Reparse local VASP outputs with `VaspToComputedEntryDrone`, which collects `is_hubbard`, `hubbards`, `potcar_spec`, `potcar_symbols`, and `run_type` by default.
- If metadata truly cannot be supplied, use `MaterialsProject2020Compatibility(check_potcar=False)` and state that POTCAR validation was bypassed.
- Do not invent POTCAR hashes, symbols, or Hubbard settings.
- Route persistent POTCAR library configuration questions to `../cli-and-configuration/SKILL.md`.

## Invalid Run Type or Hubbard Metadata

Symptoms:

- `CompatibilityError` says the run type must be GGA or GGA+U.
- GGA+U entries are excluded or receive unexpected corrections.
- r2SCAN entries disappear during MP 2020 processing.

Cause:

- `MaterialsProject2020Compatibility` handles MP-style GGA/GGA+U corrections, not arbitrary functional mixing. r2SCAN mixing is a separate workflow.

Fixes:

- Set `entry.parameters["run_type"]` from calculation provenance, not from desired output.
- Include `entry.parameters["hubbards"]` for GGA+U runs.
- For r2SCAN plus GGA/GGA+U, use `MaterialsProjectDFTMixingScheme` and pass all entries together.
- If the source is an external database handoff, confirm the returned fields include calculation provenance before applying corrections.

## Oxidation-State or Anion Correction Warnings

Symptoms:

- Warnings mention failed oxidation-state guesses.
- Peroxide/superoxide/sulfide corrections look suspicious.
- Similar O/S entries get different corrections depending on whether structures are present.

Cause:

- MP 2020 compatibility uses composition, optional structure geometry, and optional entry data to classify anion corrections. Without trusted hints, it may infer from formula or structure.

Fixes:

- Prefer `ComputedStructureEntry` when O/S bonding classification matters.
- Populate `entry.data["oxidation_states"]` only from trusted chemistry, such as `{"Fe": 3, "O": -2}`.
- Populate `entry.data["oxide_type"]` or `entry.data["sulfide_type"]` only when a trusted classification exists.
- Use `strict_anions="require_exact"` for conservative behavior or `"no_check"` only when deliberately reproducing legacy assumptions.

## DFT Mixing Is Inconsistent

Symptoms:

- Mixing scheme warns entries do not form a complete phase diagram.
- r2SCAN entries are ignored.
- Matched entries receive surprising energy adjustments.

Cause:

- `MaterialsProjectDFTMixingScheme` depends on clear functional provenance, complete base-functional hull coverage, and structure matching between functional sets.

Fixes:

- Use `ComputedStructureEntry` inputs unless a trusted `mixing_state_data` table is available.
- Confirm `run_type_1` and `run_type_2` values match actual `entry.parameters["run_type"]` values.
- Ensure base entries form a complete phase diagram for the chemical system.
- Do not mix arbitrary local settings with MP-style correction assumptions without documenting the limitation.
- Keep all entries in one process call; do not separately correct subsets and merge them silently.

## Phase Diagram Fails After Entry Processing

Symptoms:

- Convex-hull or Qhull errors.
- Missing terminal elemental entries.
- Conversion electrode cannot find a stable starting compound or working-ion reference.

Cause:

- The processed entry list no longer spans the chemical system, has too few independent compositions, or lacks elemental/reference entries.

Fixes:

- Print reduced formulas and energies of processed entries before constructing the phase diagram.
- Check that each element in the chemical system has an elemental entry.
- Use `group_entries_by_composition` to find missing or duplicate compositions.
- Avoid discarding metastable polymorphs unless the task explicitly asks for a ground-state-only summary.

## BatteryAnalyzer Requires Oxidation States

Symptom:

- `ValueError: BatteryAnalyzer requires oxidation states assigned to structure!`

Cause:

- `BatteryAnalyzer` requires oxidation states on every site. Plain species like `"Li"`, `"Fe"`, and `"O"` are insufficient.

Fix:

```python
structure = structure.copy()
structure.add_oxidation_state_by_element({"Li": 1, "Fe": 2, "P": 5, "O": -2})
analyzer = BatteryAnalyzer(structure, working_ion="Li")
```

If oxidation states are ambiguous, ask for the chemistry or route to a structure/oxidation-state workflow before battery analysis. Do not invent mixed-valence assumptions without stating them.

## Working-Ion Assumptions Are Wrong

Symptoms:

- Capacity sign or magnitude is unexpected.
- Fluoride, proton, Mg, Ca, or other non-Li workflows produce surprising values.
- Ion-removal limits conflict with the user's chemistry.

Cause:

- `BatteryAnalyzer` infers working-ion charge from elemental oxidation-state extrema unless overridden.

Fix:

```python
analyzer = BatteryAnalyzer(structure, working_ion="Mg", oxi_override={"Mg": 2})
```

State the working-ion charge assumption in summaries, especially for multivalent ions, anions, proton insertion, or mixed working ions.

## Insertion Electrode Construction Fails

Symptoms:

- `ValueError: VoltagePair: The working ion specified must be an element`.
- `ValueError: VoltagePair: The working ion must be present in one of the entries`.
- `ValueError: VoltagePair: The working ion atomic percentage cannot be the same in both the entries`.
- `ValueError: VoltagePair: the specified entries must have the same compositional framework`.
- `InsertionElectrode.from_entries` cannot form voltage pairs.

Cause:

- Insertion batteries require a topotactic path: entries differ by working-ion amount while preserving the host framework.

Fixes:

- Verify `working_ion_entry.composition.is_element` is true.
- Compare working-ion fractions for each endpoint.
- Use `group_entries_by_structure(entries, species_to_remove=[working_ion])` to find candidate host-framework families.
- Use conversion-electrode workflows instead when the framework changes.
- Include volume through structures or `entry.data["volume"]` when volumetric capacity is requested.

## Tiny Entry Sets Are Underdetermined for Voltage Curves

Symptoms:

- A toy set with `Li`, `TiO2`, and `LiTiO2` creates at most one insertion pair or fails to define a realistic curve.
- Conversion electrode returns `None` or a single-step/no-step result.

Cause:

- Battery voltage workflows require thermodynamic context, stable states, and a consistent energy reference. A few arbitrary entries can demonstrate API mechanics but cannot determine a physically meaningful voltage path.

Fixes:

- Ask for all relevant topotactic states for insertion batteries.
- Ask for a complete chemical-system entry set for conversion batteries.
- Treat toy outputs as smoke checks only and label them non-scientific.
- When explaining uncertainty, identify the missing data: stable charged/discharged states, working-ion reference, compatible corrections, volumes, or full phase-diagram coverage.

## Conversion Electrode Returns None or Raises Stability Errors

Symptoms:

- `ConversionElectrode.from_composition_and_entries(...)` returns `None`.
- `ValueError: Not stable compound found at composition ...`.
- `ValueError: working_ion_entry is None.`

Cause:

- Conversion electrodes depend on a phase diagram and element profile. The starting composition and working-ion reference must be present and stable unless `allow_unstable=True`.

Fixes:

- Ensure entries cover the full chemical system, including elemental references.
- Apply compatibility before building the phase diagram.
- Use `allow_unstable=True` only for exploratory comparison and state that the start composition is metastable.
- If there are fewer than two element-profile steps, explain that the provided entries do not define a conversion path.

## Borg Finds No Valid Paths

Symptoms:

- `BorgQueen(...).get_data()` is empty.
- `drone.get_valid_paths(...)` finds no directories.

Cause:

- The directory tree lacks `vasprun.xml*`, or the simple drone lacks required files.
- The user selected the wrong root or a broad parent with unrelated folders.

Fixes:

- Ask for the narrow calculation root containing VASP output directories.
- Prefer `VaspToComputedEntryDrone` when `vasprun.xml*` exists.
- For `relax1`/`relax2` layouts, Borg parses the final `relax2` run.
- Start with one small directory before scanning a large tree.

## VASP Output Is Incomplete or Ambiguous

Symptoms:

- `assimilate(path)` returns `None`.
- The simple drone errors on missing core files.
- Warnings say multiple `vasprun.xml.*` files were found.

Cause:

- The output is incomplete, compressed or renamed unexpectedly, or contains multiple restart files.

Fixes:

- Verify complete `vasprun.xml*` files for the full drone.
- Use `SimpleVaspToComputedEntryDrone` only when `INCAR`, `POTCAR`, `CONTCAR`, `OSZICAR`, and `POSCAR` are complete.
- If multiple matching files exist, inspect which one Borg selected before trusting the energy.
- Filter `None` entries from `queen.get_data()` and report skipped directories.

## Borg Is Slow or Path-Dependent

Symptoms:

- Directory scanning takes too long.
- Multiprocessing hides parse errors.
- A broad filesystem root is scanned accidentally.

Fixes:

- Ask for a narrow calculation root and user confirmation before scanning.
- Start with `number_of_drones=1`.
- Save successful scans with `queen.save_data("entries.json.gz")`.
- Reload with `queen.load_data("entries.json.gz")` instead of rescanning.
- Do not run Borg on remote-mounted, home, or broad project roots without explicit approval.

## Old Import Paths Fail

Symptoms:

- `ModuleNotFoundError` for `pymatgen.borg`.
- Root imports such as `from pymatgen import Structure` fail in modern environments.

Fixes:

```python
from pymatgen.apps.borg.hive import VaspToComputedEntryDrone
from pymatgen.apps.borg.queen import BorgQueen
from pymatgen.core import Lattice, Structure
```

Prefer explicit submodule imports in generated snippets.

## Live Data or CLI Requests Are Out of Scope

Symptoms:

- User asks for `MPRester`, API keys, field names, rate limits, or network errors.
- User asks for `pmg analyze`, persistent configuration, or command syntax.

Route:

- Use `../external-data-access/SKILL.md` for live data and credentials.
- Use `../cli-and-configuration/SKILL.md` for CLI syntax and configuration side effects.
- Return to this sub-skill only after entries are local and need correction, grouping, phase-diagram preparation, batteries, or Borg semantics.
