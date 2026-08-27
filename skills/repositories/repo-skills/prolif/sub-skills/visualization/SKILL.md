---
name: visualization
description: "Create and troubleshoot ProLIF visual outputs from completed
  fingerprints and molecules."
disable-model-invocation: true
metadata:
  disco-role: operating
license: Apache 2.0
---

# Visualization

Use this sub-skill when an agent needs plots or visual exports from an already executed ProLIF fingerprint: ligand interaction networks, barcode plots, 3D complex views, or residue grids. The plotting APIs consume `Fingerprint.ifp`, `Fingerprint.to_dataframe()`, and molecule objects; they do not run fingerprint analysis themselves.

## Preconditions

- Start from a `prolif.Fingerprint` that has already run through `fp.run(...)`, `fp.run_from_iterable(...)`, or `Fingerprint.from_pickle(...)` with saved results.
- Keep the ligand/protein/water molecules that match the fingerprint frame and residue identifiers, especially for `LigNetwork` and `Complex3D`.
- Install the optional plotting backend needed by the output: `matplotlib` for barcode plots, `py3Dmol` for 3D views, and notebook/IPython support for inline display helpers.
- For fingerprint generation and molecule conversion, route to `../fingerprints/` first. For changing interaction definitions or water bridges, route to `../interactions/` first.

## Fast Routing

| Goal | Use | Notes |
| --- | --- | --- |
| Save a standalone 2D network HTML | `LigNetwork.from_fingerprint(...).save(path)` | Preferred for scripts and non-notebook execution. |
| Display a 2D network inline | `fp.plot_lignetwork(...)` or `LigNetwork.display()` | Requires display-capable IPython context. |
| Plot per-frame interaction barcode | `fp.plot_barcode(...)` or `Barcode.from_fingerprint(fp).display(...)` | Returns a matplotlib `Axes`; set a non-interactive backend in batch jobs. |
| Show a 3D complex | `fp.plot_3d(lig_mol, prot_mol, frame=...)` | Requires `py3Dmol` and molecule coordinates for the chosen frame. |
| Inspect residue drawings | `prolif.display_residues(mol, slice(...))` | Useful for checking residue IDs, sanitization, and display readiness. |

## Workflow

1. Validate that the fingerprint has results: `hasattr(fp, "ifp")`, non-empty `fp.ifp`, and the requested `frame` exists.
2. Choose the output path: use `LigNetwork.save()` for durable HTML, matplotlib `savefig()` for barcode images, and notebook display only when the user explicitly wants inline rendering.
3. Pass matching molecule objects: `lig_mol` for networks; `lig_mol`, `prot_mol`, and optional `water_mol` for 3D views.
4. Tune display-only parameters without recomputing interactions: `kind`, `threshold`, `display_all`, `use_coordinates`, `flatten_coordinates`, `sanitize`, and `remove_hydrogens`.
5. If output is empty or raises `RunRequiredError`, verify fingerprint execution and molecule inputs before changing plotting options.

## References

- API details: `references/api-reference.md`
- Plotting workflows: `references/workflows.md`
- Failure recovery: `references/troubleshooting.md`
- Batch smoke helper: `scripts/plotting_smoke.py`
