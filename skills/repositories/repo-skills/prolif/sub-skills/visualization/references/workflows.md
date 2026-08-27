# Visualization Workflows

## Save a Network HTML from a Pickled Fingerprint

Use this when a user has a completed fingerprint pickle and wants a 2D interaction network file without notebook assumptions.

```python
import prolif as plf
from prolif.plotting.network import LigNetwork

fp = plf.Fingerprint.from_pickle("fingerprint.pkl")
# Recreate or load the ligand molecule that matches the fingerprint results.
lig_mol = ...

net = LigNetwork.from_fingerprint(
    fp,
    lig_mol,
    kind="aggregate",
    threshold=0.3,
)
net.save("lignetwork.html", width="100%", height="650px")
```

Checklist:

- Confirm `hasattr(fp, "ifp")` and `fp.ifp` is not empty.
- Use `kind="frame", frame=<frame_number>` for one frame rather than aggregate frequencies.
- Use `display_all=True` only when the fingerprint was created with `count=True` and the user wants all occurrences.
- Use `net.save(...)` for automation; avoid `plot_lignetwork(...)` if there is no notebook display.

## Create a Barcode Image in a Batch Script

```python
import matplotlib
matplotlib.use("Agg")

import prolif as plf
from prolif.plotting.barcode import Barcode

fp = plf.Fingerprint.from_pickle("fingerprint.pkl")
ax = Barcode.from_fingerprint(fp).display(interactive=False)
ax.figure.savefig("barcode.png", bbox_inches="tight", dpi=200)
```

Batch guidance:

- Set `interactive=False` unless running inside an interactive notebook with a compatible matplotlib backend.
- For many frames, increase `figsize`, lower `n_frame_ticks`, or save to a high-DPI image.
- If the barcode is blank, inspect `fp.to_dataframe(drop_empty=False)` before changing plot options.

## Display a 3D Complex for a Frame

```python
import prolif as plf
from prolif.plotting.complex3d import Complex3D

fp = plf.Fingerprint.from_pickle("fingerprint.pkl")
lig_mol = ...
prot_mol = ...

view = Complex3D.from_fingerprint(fp, lig_mol, prot_mol, frame=0).display(
    display_all=False,
    only_interacting=True,
    remove_hydrogens=True,
    sanitize="protein",
)
view
```

For water bridges, pass the water molecule used during fingerprinting:

```python
view = fp.plot_3d(lig_mol, prot_mol, water_mol, frame=0)
```

3D guidance:

- `Complex3D` needs molecule coordinates that correspond to the selected frame.
- Use `only_interacting=False` to show nearby pocket context, but expect a busier view.
- If RDKit reports a kekulization problem, try `sanitize=False` or scope sanitization to the molecule that can be sanitized safely.
- If using `WaterBridge`, pass `water_mol`; otherwise water residues may not be shown even when water interactions exist in metadata.

## Inspect Residues Before Plotting

```python
import prolif as plf

img = plf.display_residues(prot_mol, slice(0, 20), sanitize=False)
img
```

Use residue displays when:

- Residue identifiers in a network or barcode do not match expectations.
- A molecule conversion step produced unexpected residue fragmentation.
- A 3D view fails on one residue and you need a fast RDKit rendering check.

## Use the Bundled Smoke Helper

The helper at `scripts/plotting_smoke.py` is safe for quick checks:

```bash
python scripts/plotting_smoke.py --check-imports
python scripts/plotting_smoke.py --run-tiny --output-html network.html
```

The helper prints JSON, never requires notebook display, and refuses to overwrite an existing HTML output unless `--overwrite` is supplied.
