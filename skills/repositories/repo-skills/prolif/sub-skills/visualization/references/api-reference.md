# Visualization API Reference

This reference covers ProLIF plotting APIs that consume completed fingerprints and molecule objects. Plotting methods visualize existing interaction results; they do not calculate fingerprints.

## Convenience Methods on `Fingerprint`

| Method | Purpose | Key Parameters | Returns |
| --- | --- | --- | --- |
| `fp.plot_lignetwork(ligand_mol, *, kind="aggregate", frame=0, display_all=False, threshold=0.3, use_coordinates=False, flatten_coordinates=True, kekulize=False, molsize=35, rotation=0, carbon=0.16, width="100%", height="500px", fontsize=20, show_interaction_data=False)` | Build and display a 2D ligand interaction network. | `kind="aggregate"` summarizes all frames; `kind="frame"` shows one frame. `threshold` applies only to aggregate plots. `display_all` applies to count fingerprints for frame plots. | `LigNetwork` prepared for inline HTML representation. |
| `fp.plot_barcode(*, figsize=(8, 10), dpi=100, interactive=IS_NOTEBOOK, n_frame_ticks=10, residues_tick_location="top", xlabel="Frame", subplots_kwargs=None, tight_layout_kwargs=None)` | Build a per-frame interaction barcode. | `interactive=True` is useful in notebooks; use `False` in batch scripts. | matplotlib `Axes`. |
| `fp.plot_3d(ligand_mol, protein_mol, water_mol=None, *, frame, size=(650, 600), display_all=False, only_interacting=True, remove_hydrogens=True, sanitize="protein")` | Build a `py3Dmol` complex view for one frame. | Requires `frame`. `water_mol` is needed to display water residues involved in `WaterBridge`. `sanitize` helps with molecule rendering/kekulization. | `Complex3D` with an initialized py3Dmol view. |

## `LigNetwork`

Import with:

```python
from prolif.plotting.network import LigNetwork
```

Use `LigNetwork.from_fingerprint(fp, ligand_mol, kind="aggregate", frame=0, display_all=False, threshold=0.3, **kwargs)` when you need separate creation and export control. It raises `RunRequiredError` if `fp.ifp` is absent and `ValueError` if `kind` is not `"aggregate"` or `"frame"`.

Important options passed through `**kwargs`:

| Option | Use |
| --- | --- |
| `use_coordinates=True` | Use the ligand conformer coordinates instead of generated 2D coordinates. |
| `flatten_coordinates=False` | Keep projected coordinates closer to input coordinates when `use_coordinates=True`. |
| `kekulize=True` | Kekulize ligand before drawing; disable if RDKit kekulization fails. |
| `molsize`, `rotation`, `carbon` | Adjust visual scale, orientation, and carbon atom dots. |

Output methods:

| Method | Behavior |
| --- | --- |
| `net.save(path_or_file, **display_kwargs)` | Writes standalone HTML without requiring notebook display. Prefer this in scripts and automation. |
| `net.display(width="100%", height="500px", fontsize=20, show_interaction_data=False)` | Prepares inline iframe HTML; requires IPython display support. |
| `net.show(filename, **kwargs)` | Saves HTML and points the inline iframe to that file; requires IPython display support. |
| `net.save_png()` | Notebook-only PNG export after `display()` or `show()`; legend is not exported. |

`WaterBridge` edges are represented through water residues in the network when the fingerprint metadata includes bridged-interaction records.

## `Barcode`

Import with:

```python
from prolif.plotting.barcode import Barcode
```

`Barcode.from_fingerprint(fp)` converts `fp.to_dataframe()` into a color-coded matrix. It raises `RunRequiredError` if fingerprint results are missing.

Display with:

```python
ax = Barcode.from_fingerprint(fp).display(interactive=False)
ax.figure.savefig("barcode.png", bbox_inches="tight")
```

Use a non-interactive matplotlib backend such as `Agg` in headless scripts. Barcode columns are frames; rows are residue-interaction pairs. Multi-residue ligands combine ligand and protein residue labels so peptide-like ligands remain distinguishable.

## `Complex3D`

Import with:

```python
from prolif.plotting.complex3d import Complex3D
```

`Complex3D.from_fingerprint(fp, lig_mol, prot_mol, water_mol=None, *, frame=0)` selects one frame from `fp.ifp` and stores the molecule objects needed for rendering. `display(...)` creates the py3Dmol view; `compare(other, ...)` creates a two-panel comparison.

Display controls:

| Option | Use |
| --- | --- |
| `display_all=True` | Draw all occurrences for count fingerprints instead of only the shortest interaction per pair. |
| `only_interacting=False` | Add nearby non-interacting pocket residues. |
| `remove_hydrogens=True` | Hide non-polar hydrogens unless they are involved in interactions. Can be scoped to `"ligand"`, `"protein"`, or `"water"`. |
| `sanitize="protein"` | Sanitize molecules used for rendering. Try `False`, `"ligand"`, `"protein"`, or `True` when RDKit reports kekulization issues. |

`Complex3D.save_png()` is notebook-only and requires a prior `display()` or `compare()` call. Outside notebooks, use the py3Dmol HTML representation if available in the active frontend.

## Residue Display

Import with:

```python
from prolif.plotting.residues import display_residues
```

`display_residues(mol, residues_slice=None, *, size=(200, 140), mols_per_row=4, use_svg=True, sanitize=True)` returns an RDKit grid image of molecule residues. Use it to verify residue labels, molecule conversion, or problematic residues before plotting networks or 3D views.
