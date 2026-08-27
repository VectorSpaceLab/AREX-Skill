# ProLIF Cross-Cutting Troubleshooting

Use this reference for failures that span multiple ProLIF stages. Route workflow-specific issues to the nearest sub-skill troubleshooting file.

## Install Or Import Fails

Symptoms:
- `ModuleNotFoundError: No module named 'prolif'`
- `ModuleNotFoundError` for `rdkit`, `MDAnalysis`, `dill`, `py3Dmol`, `matplotlib`, or `pyvis`
- ProLIF imports but tutorial or plotting recipes fail

Recovery:
1. Run `python scripts/prolif_environment_check.py --include-plotting`.
2. Install the package and the smallest needed extras for the task: base ProLIF for fingerprints, `prolif[plots]` for plot backends, or `prolif[tutorials]` for notebook/tutorial-style workflows with RDKit and pyvis.
3. Use a Python version compatible with the package metadata and binary wheels. Python 3.10-3.12 is the safest target for many scientific dependencies; Python 3.13 requires compatible MDAnalysis/RDKit wheels.
4. Re-run `python -m pip check` after installing compiled chemistry/scientific packages.

## There Is No ProLIF CLI

ProLIF exposes Python APIs, notebooks, and importable plotting classes rather than a package CLI. If the user asks for a command, write a small Python script that imports ProLIF or use one of the bundled diagnostic scripts in this skill tree.

## Data Parses But Fingerprints Are Empty

Likely causes:
- Ligand/protein selections are empty or wrong.
- Hydrogens or residue templates are missing for the chosen interactions.
- Interaction names/parameters are too restrictive.
- Residues are outside the default vicinity cutoff or were explicitly filtered out.
- Chain/segment labels do not match requested residue strings.

Recovery route:
1. Validate molecule conversion and residue labels in `sub-skills/molecules-and-io/references/troubleshooting.md`.
2. Validate interaction names, hydrogens, `parameters`, `count`, and `WaterBridge` setup in `sub-skills/interactions/references/troubleshooting.md`.
3. Validate `Fingerprint.run`, `fp.ifp`, DataFrame settings, and parallel behavior in `sub-skills/fingerprints/references/troubleshooting.md`.

## Plotting Fails After Fingerprinting

Symptoms:
- `RunRequiredError`
- blank network/barcode/3D output
- notebook-only display assumptions in batch jobs
- missing `py3Dmol`, `matplotlib`, `pyvis`, or IPython display backend

Recovery:
1. Confirm `fp.ifp` exists and contains the requested frame.
2. Confirm the ligand/protein/water molecule objects match the fingerprint that was run.
3. For durable outputs, prefer saved HTML or image files over notebook display.
4. Route plotting-specific details to `sub-skills/visualization/references/troubleshooting.md`.

## MDAnalysis Deprecation Warnings

MDAnalysis may emit deprecation warnings from dependency internals during import or topology loading. Treat warnings as noise if import, `pip check`, and a tiny fingerprint smoke test pass. Do not hide real selection, topology, or converter errors behind warning filters until the workflow is validated.

## Privacy And Portability

Do not copy local environment prefixes, editable-install paths, notebook cache paths, or original repository checkout paths into reusable user code. Keep examples based on installed package imports and user-provided data paths.
