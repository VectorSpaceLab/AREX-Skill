# Visualization Troubleshooting

## Optional Dependency Import Errors

Symptoms:

- `ModuleNotFoundError` for `matplotlib`, `py3Dmol`, `IPython`, or notebook display support.
- `LigNetwork.display()`, `LigNetwork.show()`, or `save_png()` fails outside a notebook.

Recovery:

- Use `LigNetwork.save(path)` for non-notebook HTML export; it does not need inline display.
- Install the missing backend for the requested plot type: `matplotlib` for barcode, `py3Dmol` for 3D, and IPython/notebook support for inline HTML/PNG display helpers.
- In headless scripts, set `matplotlib.use("Agg")` before importing `pyplot` and call `Barcode.display(interactive=False)`.
- Run `scripts/plotting_smoke.py --check-imports` to collect backend availability as JSON.

## `RunRequiredError`

Symptoms:

- Error message says to run fingerprint analysis before displaying results.
- `Barcode.from_fingerprint`, `LigNetwork.from_fingerprint`, or `Complex3D.from_fingerprint` fails immediately.

Cause:

- Plotting classes expect `fp.ifp` to exist. They never call `fp.run(...)` or `fp.run_from_iterable(...)` for you.

Recovery:

```python
if not hasattr(fp, "ifp") or not fp.ifp:
    raise ValueError("Run the fingerprint first or load a pickle containing results")
```

Then route to `../fingerprints/` to execute or reload the fingerprint. If a pickle was loaded, verify it was created after running the analysis, not from a fresh `Fingerprint()` object.

## Empty Network or Barcode

Symptoms:

- HTML is created but shows no expected residues or interactions.
- Barcode plot contains only white cells.

Recovery:

- Check `len(fp.ifp)` and inspect `fp.to_dataframe(drop_empty=False)`.
- For aggregate networks, lower `threshold` or use `threshold=0` to verify that rare interactions are present.
- For frame networks or 3D views, confirm the requested `frame` key exists in `fp.ifp`.
- Confirm the ligand/protein molecules match the fingerprint run. Mismatched residue identifiers or molecule atom ordering can make visual outputs misleading.
- If interactions were intentionally filtered or custom interactions were configured, route to `../interactions/` to verify setup.

## Unsupported `LigNetwork` Kind

Symptoms:

- `ValueError` contains `must be "aggregate" or "frame"`.

Recovery:

- Use `kind="aggregate"` to summarize frequencies over all frames.
- Use `kind="frame"` with `frame=<existing frame key>` to show one frame.
- Do not pass workflow labels such as `"all"`, `"pose"`, or `"trajectory"` as `kind`.

## py3Dmol Display Context Problems

Symptoms:

- A `Complex3D` object is created but nothing appears.
- `save_png()` fails or says the view is not initialized.
- HTML rendering works in a notebook but not in a terminal.

Recovery:

- Call `.display()` or `.compare(...)` before accessing py3Dmol view methods.
- Use a notebook or frontend that can render py3Dmol HTML/JavaScript.
- Treat `save_png()` as notebook-only; it relies on browser-side JavaScript.
- In scripts, report that the 3D object was constructed and leave interactive rendering to the user’s notebook/frontend.

## Missing Coordinates or Molecule Mismatch

Symptoms:

- RDKit or py3Dmol errors mention missing conformers, atom positions, or index lookups.
- 3D interactions appear disconnected from the displayed ligand/protein.

Recovery:

- Recreate `lig_mol`, `prot_mol`, and optional `water_mol` from the same frame/source used for fingerprinting.
- For MDAnalysis workflows, convert molecule objects after positioning the trajectory at the intended frame.
- For docked poses, ensure the ligand conformer corresponds to the fingerprint pose.
- Use `display_residues(mol, sanitize=False)` to inspect residue fragmentation before debugging plot settings.

## Kekulization or Sanitization Errors

Symptoms:

- RDKit raises `KekulizeException` during 2D or 3D plotting.
- Protein or ligand residues fail while converting to MolBlock/PDBBlock.

Recovery:

- For `LigNetwork`, try `kekulize=False` first. If the ligand needs clearer aromatic display and can be kekulized safely, use `kekulize=True`.
- For `Complex3D.display`, try `sanitize=False`, `sanitize="protein"`, `sanitize="ligand"`, or `sanitize=True` depending on which molecule is problematic.
- Use `remove_hydrogens=True` to simplify 3D rendering without hiding hydrogens involved in interactions.
- Inspect problematic residues with `display_residues(..., sanitize=False)`.

## Water Interactions and Display Choices

Symptoms:

- `WaterBridge` interactions exist in the fingerprint but water residues are absent from plots.
- Network/3D water labels are confusing or overly dense.

Recovery:

- Confirm `WaterBridge` was configured during fingerprinting with the correct water molecule or selection.
- For `Complex3D`, pass the same `water_mol` to `fp.plot_3d(...)` or `Complex3D.from_fingerprint(...)`.
- For `LigNetwork`, use `kind="frame"` while debugging water-mediated contacts because aggregate thresholds can hide rare water interactions.
- Use `display_all=False` for clarity; switch to `True` only when count fingerprints and all water-mediated occurrences are needed.
