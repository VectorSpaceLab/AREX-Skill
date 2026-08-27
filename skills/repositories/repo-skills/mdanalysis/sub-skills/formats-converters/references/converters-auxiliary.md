# Converters, Auxiliary Data, and Fetchers

Use this reference for interoperability workflows. For ordinary loading/writing of MDAnalysis file trajectories, use `../../universe-io/SKILL.md`.

## Converter API Pattern

Converters live under `MDAnalysis.converters` and are reached from normal `Universe(...)` construction or `AtomGroup.convert_to(...)`.

- To convert an external object into MDAnalysis, pass the object to `MDAnalysis.Universe(...)` when the converter supplies a format hint, or pass `format=` explicitly.
- To convert MDAnalysis objects outward, call `atomgroup.convert_to("RDKIT")`, `atomgroup.convert_to("PARMED")`, or the tab-completion style `atomgroup.convert_to.rdkit(...)` / `atomgroup.convert_to.parmed()`.
- Converter format names are case-insensitive in common use, but reference them in uppercase (`RDKIT`, `PARMED`) when documenting recipes.
- Always validate metadata after conversion. Converters are not guaranteed to preserve every topology attribute, force-field parameter, unit, or chemical perception detail.

## RDKit Converter

Capabilities:

- `MDAnalysis.Universe(rdkit_mol)` reads an RDKit `Chem.Mol`; each conformer becomes a trajectory frame through `RDKitReader`.
- `atomgroup.convert_to("RDKIT")` or `atomgroup.convert_to.rdkit(...)` returns an RDKit `Chem.Mol` for the current frame.
- Converted RDKit atoms retain many MDAnalysis attributes as PDB monomer info or `_MDAnalysis_*` properties, including names, resnames, resids, chain IDs, occupancies, tempfactors, charges, indices, segids, and types where present.
- Coordinates are assigned from the current MDAnalysis timestep when they are present and not NaN/empty.
- The converter caches topology conversion for recent AtomGroups; use `cache=False` to bypass caching for debugging.
- `MDAnalysis.converters.RDKit.set_converter_cache_size(maxsize)` changes the cache size.

Common keyword choices:

| Goal | Pattern | Notes |
| --- | --- | --- |
| Disable bond-order/formal-charge inference | `ag.convert_to.rdkit(inferrer=None)` | Useful when explicit hydrogens are missing or the molecule is inorganic/ambiguous. |
| Allow implicit hydrogens | `ag.convert_to.rdkit(implicit_hydrogens=True, inferrer=None)` | Avoids legacy `NoImplicit`; default assumes no implicit hydrogens. |
| Force conversion without hydrogens | `ag.convert_to.rdkit(force=True)` | Emits a warning; verify chemistry afterwards. |
| Use template chemistry | `TemplateInferrer(template=...)` then `ag.convert_to.rdkit(inferrer=inferrer)` | Use when a trusted template should assign bond orders/charges. |
| Avoid stale cache during experiments | `ag.convert_to.rdkit(cache=False)` | Slower but clearer for debugging. |

Required topology conditions:

- `elements` must exist; otherwise the converter raises an error that the `elements` attribute is required.
- Bonds are required conceptually. If `bonds` are absent, the converter tries `ag.guess_bonds()` and warns.
- Explicit hydrogens are expected when the default inferrer is used. If no hydrogen atoms are present, use `inferrer=None`, provide a template/callable inferrer, or explicitly decide that `force=True` is acceptable.
- Coordinate arrays with NaN or all-zero values can produce an RDKit molecule without a valid 3D conformer.

A robust RDKit task response should state what chemistry was inferred versus supplied. For example, distinguish “elements were guessed from names/types before conversion” from “bond orders were inferred by the RDKit converter.” Route detailed element/bond guessing to `../../selections-topology/SKILL.md`.

## OpenMM Object Readers

MDAnalysis can build a `Universe` from selected OpenMM objects when OpenMM is installed:

- `openmm.app.Simulation` uses `OpenMMSimulationReader` with `OPENMMSIMULATION` format semantics.
- `openmm.app.PDBFile`, `openmm.app.Modeller`, and `openmm.app.PDBxFile` use `OpenMMAppReader` with `OPENMMAPP` format semantics.
- Legacy `simtk.openmm` imports are attempted as a fallback in the source.

OpenMM units are converted into MDAnalysis units when `convert_units` is enabled. Simulation objects can expose positions, velocities, forces, energies, time, and periodic box vectors depending on the object and state. Treat the result as a single-frame or current-state import, not a full simulation trajectory unless the object actually provides one.

## ParmEd Converter

Capabilities:

- `MDAnalysis.Universe(parmed_structure)` imports a `parmed.Structure` through the ParmEd reader/parser path.
- `atomgroup.convert_to("PARMED")` returns a `parmed.Structure`.
- Coordinates, velocities, box dimensions, bonds, angles, dihedrals, impropers, CMAPs, and related attributes are transferred when present and representable.

Important caveats:

- Missing names or resnames are filled with defaults such as `X` or `UNK` and a warning is emitted.
- Atomic numbers are inferred from `element` first, then sometimes from atom type; missing/unknown symbols reduce chemical specificity.
- Force-field parameter details may not survive a subset conversion exactly; inspect the resulting ParmEd structure before writing or simulation setup.
- ParmEd conversion requires the `parmed` optional package.

## Chemfiles Backend

The Chemfiles backend is a coordinate reader/writer, not a general topology converter.

- Use `format="CHEMFILES"` to force MDAnalysis to delegate low-level I/O to Chemfiles.
- Pass `chemfiles_format="..."` when Chemfiles cannot infer the file type from the extension.
- Chemfiles can read/write formats not natively supported by MDAnalysis, but it may use different unit assumptions and topology semantics.
- MDAnalysis currently expects a supported Chemfiles Python version range around `>=0.10,<0.11` in the source evidence.

If a Chemfiles workflow is optional, prefer native MDAnalysis readers for reproducibility and clearer troubleshooting.

## Auxiliary Data

Auxiliary readers attach non-coordinate time series to trajectory timesteps through `u.trajectory.add_auxiliary(...)` and expose values under `u.trajectory.ts.aux`.

### XVG

- `MDAnalysis.auxiliary.XVG.XVGReader` reads all `.xvg` data into memory by default.
- `MDAnalysis.auxiliary.XVG.XVGFileReader` (`format="XVG-F"`) reads step-by-step for lower memory use.
- Time defaults to column 0 in ps; use `time_selector` and `data_selector` to choose columns.
- Lines beginning with Grace directives/comments are ignored; multiple datasets separated by `&` are not supported beyond the first dataset.
- Column counts must be consistent or the reader raises `ValueError`.

Typical attachment:

```python
u.trajectory.add_auxiliary("pullforce", "pull_force.xvg")
value = u.trajectory.ts.aux.pullforce
```

### EDR

- `MDAnalysis.auxiliary.EDR.EDRReader` reads GROMACS `.edr` files through `pyedr`.
- `EDRReader.terms` lists available GROMACS term names.
- `EDRReader.get_data(...)` returns one, many, or all terms plus `Time`.
- Units are converted to MDAnalysis base units where MDAnalysis knows the unit type; unknown units warn and remain as-is.
- Terms with spaces or punctuation may only be convenient through dictionary access unless you map them to safe names.

Typical attachment:

```python
aux = mda.auxiliary.EDR.EDRReader("ener.edr")
u.trajectory.add_auxiliary({"epot": "Potential", "temp": "Temperature"}, aux)
value = u.trajectory.ts.aux.epot
```

When an auxiliary time series is lower frequency than the trajectory, use `iter_as_aux(...)` or check for `np.nan` representative values.

## PDB Fetcher

`MDAnalysis.fetch.from_PDB(...)` downloads RCSB files and caches them using `pooch`.

```python
path = mda.fetch.from_PDB("1AKE", cache_path="pdb-cache", file_format="cif")
u = mda.Universe(path)
```

Key behavior:

- Returns a `pathlib.Path` for one PDB ID and a list of `Path` objects for multiple IDs.
- Default `file_format` is `cif.gz`.
- Supported download formats include `cif`, `cif.gz`, `bcif`, `bcif.gz`, `xml`, `xml.gz`, `pdb`, `pdb.gz`, `pdb1`, and `pdb1.gz`.
- Missing `pooch` raises a dependency error before any network work.
- Invalid `file_format` raises `ValueError`.
- Invalid PDB codes or network failures surface as HTTP/request errors from the downloader.

Do not place `from_PDB` calls in bundled validation scripts or offline smoke tests. Ask before using it in an agent workflow because it requires network access and writes to a cache directory.

## Conversion Validation Checklist

After any converter workflow, inspect:

1. Atom count and atom order.
2. Residue, segment, chain, and atom names.
3. Elements, masses, charges, bond graph, and bond orders.
4. Coordinates for the intended current frame and whether a conformer exists.
5. Unit-cell dimensions and unit conversion assumptions.
6. Whether missing attributes were guessed, defaulted, or omitted.
7. Whether the target package can represent the selected subset and all metadata needed for the next step.
