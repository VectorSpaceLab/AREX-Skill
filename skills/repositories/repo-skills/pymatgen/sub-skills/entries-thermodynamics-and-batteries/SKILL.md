---
name: entries-thermodynamics-and-batteries
description: "Prepare pymatgen computed entries, compatibility-corrected
  thermodynamics, battery electrode objects, and Borg VASP assimilation."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Entries, Thermodynamics, and Batteries

Use this sub-skill when a task mentions `ComputedEntry`, `ComputedStructureEntry`, compatibility corrections, MP 2020 corrections, GGA/GGA+U/r2SCAN mixing, phase-diagram-ready entries, entry grouping, insertion or conversion batteries, voltage pairs, `BatteryAnalyzer`, `VaspToComputedEntryDrone`, or `BorgQueen`.

## Route

- Read [references/api-reference.md](references/api-reference.md) for imports, signatures, metadata expectations, and object relationships.
- Read [references/workflows.md](references/workflows.md) for recipes to prepare entries, preserve correction metadata, group entries, construct battery objects, and assimilate VASP outputs.
- Read [references/troubleshooting.md](references/troubleshooting.md) for predictable failures involving missing metadata, filtered entries, oxidation states, incomplete VASP output, DFT mixing, and working-ion assumptions.
- Run [scripts/entry_battery_smoke.py](scripts/entry_battery_smoke.py) for a safe in-memory import/readiness check; it does not read user calculation directories, fixtures, credentials, or network resources.

## Boundaries

- Use this sub-skill after entries are already local or in memory. Live Materials Project, COD, OPTIMADE, credentials, field names, pagination, and network errors belong to `../external-data-access/SKILL.md`.
- Use this sub-skill for entry and battery Python APIs. `pmg analyze`, persistent configuration, and other CLI syntax belong to `../cli-and-configuration/SKILL.md`.
- Use this sub-skill for phase-diagram-ready entry preparation, then hand core hull, reaction, Pourbaix, surface, and interfacial interpretation to the owning analysis APIs or `../surfaces-interfaces-and-electrochemistry/SKILL.md`.
- Treat Borg assimilation as user-directory-specific and path-sensitive. Do not scan broad filesystems unless the user provides the calculation root and accepts the scan.

## Default Approach

1. Identify the entry source: in-memory values, saved Monty JSON, local VASP outputs, or an external-data handoff.
2. Preserve provenance before corrections: composition, total energy in eV per entry, `parameters["run_type"]`, `parameters["hubbards"]`, `parameters["potcar_spec"]` or `parameters["potcar_symbols"]`, optional `parameters["software"]`, structure, volume, and trusted oxidation-state/anion hints.
3. Apply the compatibility or mixing scheme that matches the calculation provenance before building phase diagrams, reactions, or battery electrodes.
4. Keep exploratory processing non-destructive with `inplace=False`, and debug filtering with `on_error="warn"` or `on_error="raise"`.
5. For battery workflows, verify whether the task is a redox-capacity estimate, an insertion path with a stable topotactic framework, or a conversion path requiring a complete phase diagram.
