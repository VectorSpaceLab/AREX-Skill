---
name: mdanalysis
description: "Use MDAnalysis to load molecular simulation data, select atoms,
  run analyses, transform trajectories, write outputs, and diagnose format or
  optional dependency issues."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MDAnalysis Repo Skill

Use this skill when a task mentions MDAnalysis, `MDAnalysis`, `mda.Universe`, atom selections, molecular dynamics trajectories, topology/coordinate formats, `MDAnalysis.analysis`, on-the-fly transformations, or converter/optional-format errors.

MDAnalysis is a Python toolkit for analyzing molecular simulation systems. Its core pattern is: create a `Universe`, select atoms, iterate or transform trajectories, run analysis classes/functions, and optionally write new coordinate or trajectory outputs.

## First Checks

- Install the public package with `python -m pip install MDAnalysis`; add narrow optional packages only when a workflow requires them.
- Confirm the package imports with `python -c "import MDAnalysis as mda; print(mda.__version__)"`.
- For a self-contained environment check, run `python scripts/check_mdanalysis_install.py` from this skill directory.
- If import fails, read `references/troubleshooting.md` before trying broad optional extras.
- If a file format fails, first identify whether it is a topology parser, coordinate reader, writer, converter, fetcher, or auxiliary-data dependency problem.

## Route By Task

- **Load or construct systems**: read `sub-skills/universe-io/SKILL.md` for `Universe(...)`, `Universe.empty(...)`, topology/trajectory pairing, trajectory iteration, `Merge`, `load_new`, and basic writers.
- **Select atoms or manipulate topology**: read `sub-skills/selections-topology/SKILL.md` for selection strings, sorted/updating selections, topology attributes, groups, fragments, bonds, guessing, and selection exporters.
- **Run analyses**: read `sub-skills/analysis-workflows/SKILL.md` for `AnalysisBase`, RMSD/RMSF, alignment, contacts, distance arrays, RDF, hydrogen bonds, results containers, slicing, and backends.
- **Transform and write trajectories**: read `sub-skills/transformations-writing/SKILL.md` for `translate`, `wrap`, `unwrap`, `center_in_box`, `fit_rot_trans`, `NoJump`, transformation order, and transformed-output writing.
- **Diagnose formats and converters**: read `sub-skills/formats-converters/SKILL.md` for supported format families, explicit `format=` or `topology_format=`, optional dependencies, RDKit/OpenMM/ParmEd converters, auxiliary data, and PDB fetching.

## Common Workflows

- **Basic analysis script**: use `universe-io` to build `u = mda.Universe(topology, trajectory)`, `selections-topology` to form stable AtomGroups, then `analysis-workflows` for module-specific results.
- **Synthetic or test-free examples**: prefer `Universe.empty(..., trajectory=True)` plus bundled smoke scripts when a user wants runnable code without molecular data files.
- **Output trajectory repair**: use `transformations-writing` to define transformations and output safety checks, then use `universe-io` for writer factory and atom-count details.
- **Optional dependency triage**: use `formats-converters` to map the failed format/converter to a narrow package instead of installing every optional extra.
- **Custom per-frame computation**: use `analysis-workflows` when a loop should become an `AnalysisBase` subclass with deterministic `results` and validated frame slicing.

## Root References

- `references/package-overview.md` summarizes the package surface, object model, install variants, and how the sub-skills fit together.
- `references/troubleshooting.md` covers cross-cutting install/import, data, optional dependency, and API-misuse failures.
- `references/repo-provenance.md` records the source evidence baseline for future refresh decisions.
- `references/repo-routing-metadata.json` is structured metadata for the managed repo-skills router.
- `scripts/check_mdanalysis_install.py` verifies import, version, synthetic `Universe.empty`, selection, and a tiny distance calculation.

## Decision Guardrails

- Prefer public MDAnalysis APIs over private modules unless the user is explicitly maintaining MDAnalysis itself.
- Use installed-package inspection or live signatures for exact parameters when the user asks for code-level changes.
- Do not assume optional extras are installed; detect or ask before using RDKit, OpenMM, ParmEd, Chemfiles, H5MD, GSD, TNG, EDR, NetCDF4, or network-backed fetchers.
- Avoid relying on MDAnalysis test-data packages in user-facing examples unless the user explicitly has test fixtures installed; bundled scripts use synthetic data instead.
- Treat selections as case-sensitive and usually sorted/deduplicated unless `sorted=False` or non-selection group operations are intentionally used.
- Validate trajectory and writer atom counts before writing transformed or subset outputs.

## Minimal Example

```python
import MDAnalysis as mda

u = mda.Universe.empty(3, n_residues=1, trajectory=True)
u.add_TopologyAttr("names", ["N", "CA", "C"])
protein_backbone = u.select_atoms("name N CA C")
print(protein_backbone.n_atoms)
```

Use the sub-skills for production recipes, troubleshooting, and format-specific details.
