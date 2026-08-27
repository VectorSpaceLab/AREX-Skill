---
name: prolif
description: "Use ProLIF to prepare molecular inputs, define protein-ligand
  interactions, compute interaction fingerprints, and create visualization
  outputs for chemistry and molecular-simulation workflows."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# ProLIF

Use this repo skill when a user asks for ProLIF, protein-ligand interaction fingerprints, molecular interaction fingerprints from docking poses or MDAnalysis trajectories, residue-level interaction metadata, or ProLIF plots. ProLIF is a Python API package, not a command-line application.

## Start Here

1. Confirm the package imports and optional dependencies with `scripts/prolif_environment_check.py` when the runtime environment is uncertain.
2. Route the task to the focused sub-skill below before writing workflow code.
3. Keep ProLIF input preparation, interaction selection, fingerprint execution, and plotting as separate decisions; most failures come from mixing those stages.
4. Use bundled references and scripts from this skill tree only; do not rely on the original ProLIF repository checkout.

## Route By Task

| User goal | Read |
| --- | --- |
| Convert RDKit, MDAnalysis, SDF, MOL2, PDBQT, PDB, or CIF-backed structures into ProLIF objects | `sub-skills/molecules-and-io/SKILL.md` |
| Choose interaction classes, tune parameters, use implicit hydrogens, water bridges, counts, or direct residue checks | `sub-skills/interactions/SKILL.md` |
| Run `Fingerprint.run`, `run_from_iterable`, or `generate`; export DataFrames, bitvectors, countvectors, and pickles | `sub-skills/fingerprints/SKILL.md` |
| Create 2D ligand networks, barcode plots, 3D complex views, or residue drawings from completed fingerprints | `sub-skills/visualization/SKILL.md` |

## Minimal Environment Check

```bash
python scripts/prolif_environment_check.py
python scripts/prolif_environment_check.py --include-plotting
```

Expected output is JSON with `prolif_version`, available interactions, and optional plotting dependency statuses. Install the base package for fingerprinting and `prolif[tutorials]` or `prolif[plots]` when workflows require RDKit-based tutorials or plotting extras.

## Common Workflow Order

1. **Prepare molecules**: build `prolif.Molecule` objects or MDAnalysis selections with residue labels that will remain stable.
2. **Choose interactions**: decide defaults versus named interaction classes, `parameters`, `count=True`, `implicit_hydrogens=True`, `WaterBridge`, and custom ignore predicates.
3. **Run fingerprints**: choose trajectory, ligand-iterable, or single-pair execution and validate `fp.ifp` before exporting.
4. **Export or plot**: convert results to pandas/RDKit vectors or pass completed fingerprints plus matching molecules to plotting helpers.

## Root References

- `references/package-overview.md` summarizes ProLIF concepts, dependencies, workflow stages, and no-CLI guidance.
- `references/troubleshooting.md` covers cross-cutting install/import, optional dependency, data, and API misuse failures.
- `references/repo-provenance.md` records the source snapshot and evidence used to build this skill.
- `references/repo-routing-metadata.json` is structured router metadata for managed imports.

## Cross-Cutting Warnings

- Do not call export or plotting methods before a fingerprint run has populated `fp.ifp`.
- Do not assume residue strings from one conversion path match another; check `chain` versus `segid` and route label questions to `molecules-and-io`.
- Do not include `WaterBridge` without providing a water selection or water molecule through interaction parameters.
- Do not debug plotting by recomputing interactions first; validate the completed fingerprint and molecule objects, then route to `visualization`.
