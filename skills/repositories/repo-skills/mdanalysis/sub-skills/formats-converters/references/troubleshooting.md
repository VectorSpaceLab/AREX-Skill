# Formats and Converters Troubleshooting

Use this page to diagnose failures around MDAnalysis formats, optional dependencies, auxiliary files, fetchers, and converters. For normal loading/writing recipes, route to `../../universe-io/SKILL.md`.

## Unknown or Misguessed Formats

Symptoms:

- `Unknown coordinate trajectory format ...`
- `isn't a valid topology format, nor a coordinate format from which a topology can be minimally inferred`
- A file loads through the wrong parser because its suffix is ambiguous.

Recovery:

1. Identify whether the failing argument is topology or coordinates.
2. Use `topology_format="FORMAT"` for the topology argument and `format="FORMAT"` for coordinate arguments.
3. For XPDB, use `topology_format="XPDB"` or `format="XPDB"` as appropriate; do not rely on plain `.pdb` guessing.
4. For Chemfiles, use `format="CHEMFILES"` and, if needed, `chemfiles_format="Chemfiles Format Name"`.
5. For writer failures, pass a supported extension or explicit writer `format=...` and the correct `n_atoms`.
6. If a coordinate-only file was used as the topology, confirm the minimal topology contains enough attributes for selections, converters, and analyses.

## Missing Optional Packages

Use the narrowest package that matches the failing component.

| Error mentions | Likely package | Recommended guidance |
| --- | --- | --- |
| `Please install h5py` or `H5MDWriter` | `h5py` | Install `h5py`; validate H5MD units and fixed atom count afterwards. |
| `Please install Chemfiles` | `chemfiles` | Install a compatible Chemfiles Python package; retry with `format="CHEMFILES"`. |
| `please install gsd` | `gsd` | Install `gsd`; confirm HOOMD GSD files have fixed particle counts. |
| `please install pytng` | `pytng` | Install `pytng`; remember TNG has a reader but no writer. |
| `please install pyedr` | `pyedr` | Install `pyedr` only for GROMACS `.edr` auxiliary data. |
| `pooch is needed as a dependency for from_PDB()` | `pooch` | Install `pooch`, or avoid network fetch and use a local structure file. |
| `RDKit is required for the RDKitConverter` | `rdkit` | Install RDKit; then check `elements`, bonds, hydrogens, and inferrer options. |
| `ParmEd is required for ParmEdConverter` | `parmed` | Install `parmed`; inspect warnings about defaulted topology attrs. |
| `IMDReader requires the imdclient package` | `imdclient` | Install `imdclient>=0.2.2`; only use for authorized live socket streams. |
| AMBER NetCDF write warns about slow fallback | `netCDF4` | Install `netCDF4` only if faster NCDF writing is needed. |

If the user asks “which extra?”, say the MDAnalysis `extra_formats` optional group includes these packages, but targeted installation is safer than installing all extras.

## H5MD Failures

Common causes:

- `h5py` is missing.
- H5MD units are absent or not recognized while `convert_units=True`.
- The file does not contain at least one of position, velocity, or force groups.
- Particle counts vary across frames.
- The box dimension is not 3D.
- Parallel HDF5 arguments are inconsistent; `comm` requires `driver="mpio"`.
- H5MD writer needs `n_frames` when using contiguous datasets with `chunks=False`.

Recovery:

- Install `h5py` for H5MD support.
- For unitless H5MD files, use `convert_units=False` only if downstream code can handle raw units.
- Reject or preprocess variable-topology H5MD files; MDAnalysis expects fixed atom counts.
- Use only 3D periodic boxes or no periodicity.
- Do not promise parallel H5MD writing; the writer rejects `driver="mpio"`.

## Chemfiles Failures

Common causes:

- `chemfiles` is missing or outside the compatible version window.
- The extension is not enough for Chemfiles to infer a format.
- The number of atoms changes in ways MDAnalysis does not support.
- The Chemfiles format lacks topology metadata expected by the next step.

Recovery:

- Force MDAnalysis delegation with `format="CHEMFILES"`.
- Pass `chemfiles_format="..."` using the Chemfiles format name when needed.
- Compare atom counts, residue data, bonds, and unit assumptions after loading.
- Prefer a native MDAnalysis reader if it supports the same file.

## GSD and TNG Failures

GSD:

- Requires `gsd`.
- The reader supports HOOMD schema GSD and assumes fixed particle count across frames.
- Topology changes, particle identity changes, or changing atom count are not fully supported by MDAnalysis.

TNG:

- Requires `pytng`.
- There is currently no TNG writer in MDAnalysis.
- Special blocks for positions, box, velocities, and forces must have compatible strides and frame counts.
- Additional blocks may be skipped if their stride is incompatible with the main trajectory stride.
- TNG time units are seconds in the reader, unlike many other GROMACS formats.

Recovery:

- Install only the relevant optional package.
- For writing TNG, choose another supported output format such as XTC/TRR/H5MD if appropriate.
- For unsupported variable-topology data, convert upstream to a fixed-topology trajectory or split by compatible segments.

## IMD Stream Failures

IMD is a live socket trajectory reader, not a file reader.

Common causes:

- Missing or too-old `imdclient`.
- URL is not of the form `imd://host:port`.
- `n_atoms` is missing; MDAnalysis needs the atom count from the topology or explicit argument.
- Simulation engine speaks IMDv2 or otherwise incompatible IMDv3 behavior.
- Stream is consumed once; random access, rewind, and multiple independent readers are not available.

Recovery:

- Use IMD only when the user authorized a live simulation connection.
- Ensure the topology atom count matches the stream.
- Always close the trajectory in `finally` blocks or context-controlled workflows.
- Avoid IMD in notebooks unless cleanup is explicit, because kernel restarts may leave connections open.

## Auxiliary Data Failures

XVG:

- `time_selector` must be a single column index.
- `data_selector` indices must exist in every data row.
- Column counts must be consistent.
- Multiple datasets separated by `&` are not supported beyond the first dataset.
- The default `XVGReader` loads the whole file; use `format="XVG-F"` for lower memory.

EDR:

- Requires `pyedr`.
- Invalid term names raise `KeyError`; inspect `EDRReader.terms`.
- Some units cannot be converted because MDAnalysis does not define their unit type.
- Terms with spaces or punctuation may need dictionary access or user-supplied safe names.

Trajectory alignment:

- If auxiliary data is lower frequency than trajectory frames, representative values can be `np.nan`.
- Use `iter_as_aux(...)`, `next_as_aux(...)`, or a `cutoff` when the user wants only frames with auxiliary data.

## PDB Fetch Failures

Common causes:

- Missing `pooch`.
- Network or HTTP errors for invalid PDB IDs or unavailable services.
- Unsupported downloader `file_format`.
- A downloaded format is supported by RCSB but not readable by the current MDAnalysis workflow.

Recovery:

- Use a local file when offline or reproducibility matters.
- Pass an explicit `cache_path` for predictable cache behavior.
- Catch HTTP/request errors separately from parser errors.
- Use `file_format="pdb"`, `"pdb.gz"`, `"cif"`, or `"cif.gz"` only when the installed MDAnalysis readers support the content needed by the task.

## RDKit Conversion Failures

Symptoms and fixes:

| Symptom | Cause | Fix |
| --- | --- | --- |
| `RDKit is required...` | `rdkit` missing | Install RDKit or avoid RDKit-specific workflow. |
| `elements attribute is required` | Topology lacks `elements` | Add/guess elements before conversion; verify names/types are reliable. |
| Warning about missing `bonds` | Topology lacks bonds | Let `ag.guess_bonds()` run only when distance-based guessing is acceptable, or provide a topology with bonds. |
| Error about explicit hydrogens | Default inferrer needs hydrogens | Use explicit hydrogens, `inferrer=None`, a template inferrer, or `force=True` only after explaining the risk. |
| Bad or missing conformer | NaN/empty coordinates | Fix coordinates or accept a topology-only RDKit molecule. |
| Wrong bond orders/formal charges | Inference ambiguity | Use a trusted template/callable inferrer or disable inference and assign chemistry downstream. |
| Metadata mismatch | Converter stores only supported attrs | Inspect `_MDAnalysis_*` properties and PDB monomer info; do not assume lossless round-trip. |

A safe RDKit answer for missing bonds/elements should explicitly separate preparation steps:

1. Ensure `elements` exists and is chemically correct.
2. Ensure `bonds` exist or consciously allow coordinate-based bond guessing.
3. Decide hydrogens/inference: explicit hydrogens with default inferrer, `inferrer=None`, or template/callable inferrer.
4. Convert the relevant `AtomGroup` for the current trajectory frame.
5. Validate atom order, conformer coordinates, bond graph, charges, and residue metadata.

## ParmEd and OpenMM Metadata Loss

ParmEd:

- Missing names/resnames are defaulted with warnings.
- Atomic numbers may be inferred from element or type; unknowns reduce chemistry fidelity.
- Subset conversion can drop or alter force-field parameter completeness.
- Validate masses, charges, atom types, bonds, angles, dihedrals, impropers, CMAPs, velocities, and box dimensions before simulation setup.

OpenMM:

- Object readers import current OpenMM object state; do not assume a full saved trajectory.
- Unit conversion changes OpenMM native units into MDAnalysis conventions.
- Simulation state reading can include positions, velocities, forces, energy, time, and box vectors only if available from the object/context.

## Unit Cell and Units Limitations

- Different readers store native time/length units differently; MDAnalysis converts to common conventions when `convert_units=True` and units are known.
- H5MD can be unitless or use unit strings MDAnalysis does not recognize; this is a hard error when conversion is requested.
- TNG time is read in seconds before conversion.
- EDR pressure and other less common unit types may not convert because MDAnalysis does not define all base-unit mappings.
- PDB-like formats have limited precision and simplified unit-cell/metadata representation.
- H5MD, GSD, and some Chemfiles workflows reject variable atom counts; split or preprocess variable-topology trajectories.

## Quick Diagnostic Commands

From this sub-skill directory:

```bash
python scripts/format_dependency_check.py
python scripts/format_dependency_check.py --json
```

The script only imports MDAnalysis and uses `importlib.util.find_spec` for optional packages. It does not read molecular data, open network connections, import optional heavy packages directly, or write output files.
