# MDAnalysis Cross-cutting Troubleshooting

Use this file for failures that span multiple MDAnalysis workflows. For route-specific issues, read the nearest sub-skill troubleshooting file.

## Import Or Install Fails

Symptoms:
- `ModuleNotFoundError: No module named 'MDAnalysis'`
- compiled-extension import errors
- `pip check` dependency conflicts

Actions:
1. Confirm Python version is supported by the installed MDAnalysis release.
2. Reinstall the base package before optional extras: `python -m pip install -U MDAnalysis`.
3. Run `python -c "import MDAnalysis as mda; print(mda.__version__)"`.
4. If a compiled extension fails, reinstall with a clean wheel/source build matching the active Python and NumPy version.
5. Avoid mixing packages from unrelated environments; run checks through the same `python` that will execute the analysis.

## Optional Dependency Missing

Symptoms:
- an error names `rdkit`, `parmed`, `openmm`, `h5py`, `chemfiles`, `pyedr`, `pytng`, `gsd`, `netCDF4`, `pooch`, or `imdclient`
- a format or converter works on one machine but not another

Actions:
1. Identify the exact failing workflow and read `sub-skills/formats-converters/SKILL.md`.
2. Run `python sub-skills/formats-converters/scripts/format_dependency_check.py` from this skill directory to see which optional imports are available.
3. Install the narrow package named by the failing format or converter when possible.
4. Only use broad extras when the user truly needs many optional formats or converters.
5. Re-run a tiny import or dependency check before executing user data workflows.

## File Loading Fails

Symptoms:
- unsupported or unknown format
- topology and coordinate atom-count mismatch
- missing topology attributes such as masses, charges, bonds, elements, or dimensions
- a trajectory reads but selections or analyses are empty

Actions:
1. Read `sub-skills/universe-io/SKILL.md` for topology/coordinate pairing and explicit `format=` / `topology_format=` decisions.
2. Confirm the topology source contains the attributes needed by the downstream selection or analysis.
3. Check `u.atoms.n_atoms`, `len(u.trajectory)`, `u.trajectory.ts.dimensions`, and representative attribute presence before analysis.
4. If format guessing is wrong, pass explicit format arguments or use a reader/converter-specific route.
5. If the atom count differs, do not force a reader; pair the trajectory with the matching topology or select/write a matching subset first.

## Selection Or Topology Results Are Surprising

Symptoms:
- selections are empty
- returned atom order differs from the input group
- duplicate atoms disappear
- geometric selections differ with/without periodic boxes
- SMARTS selection requires RDKit

Actions:
1. Read `sub-skills/selections-topology/SKILL.md`.
2. Check case sensitivity and available topology attributes before rewriting the selection string.
3. Use `sorted=False` only when order preservation matters and the selection supports it.
4. Use non-selection group operations when duplicates must be preserved.
5. For geometric selections, decide whether periodic wrapping is intended and pass `periodic=` deliberately.

## Analysis Results Look Wrong

Symptoms:
- empty result arrays
- shape does not match selected frames or atom groups
- `frames` conflicts with `start`, `stop`, or `step`
- mass mismatch or alignment warnings
- backend errors for parallel execution

Actions:
1. Read `sub-skills/analysis-workflows/SKILL.md`.
2. Validate selections and frame slicing before running expensive analyses.
3. Inspect `results` attributes documented by the analysis class instead of relying on deprecated aliases.
4. Use serial backend first for debugging; add `parallel` or custom backends only after the serial result is correct.
5. Do not widen RMSD mass tolerances without confirming the reference/mobile selections describe the same atoms.

## Transformations Or Output Writes Fail

Symptoms:
- transformations appear not to apply
- wrap/unwrap/NoJump complains about box dimensions
- writer raises atom-count or unsupported format errors
- transformed output has unexpected coordinates

Actions:
1. Read `sub-skills/transformations-writing/SKILL.md`.
2. Build transformations in the intended order before trajectory iteration.
3. Confirm periodic dimensions exist before wrap/unwrap/NoJump workflows.
4. Validate output `n_atoms` against the writer or selected AtomGroup.
5. Write a temporary tiny output first when changing format, subset, or transformation logic.

## Safe Debug Checklist

Run these from a project using MDAnalysis, not from the source checkout:

```bash
python -c "import MDAnalysis as mda; print(mda.__version__)"
python scripts/check_mdanalysis_install.py
python sub-skills/universe-io/scripts/universe_smoke_check.py
python sub-skills/selections-topology/scripts/selection_probe.py
```

Use deeper sub-skill smoke scripts for route-specific checks.
