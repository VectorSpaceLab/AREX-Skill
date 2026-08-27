# Format Support

This reference summarizes how to choose and troubleshoot MDAnalysis topology and coordinate formats. For ordinary `Universe(...)`, `Universe.load_new(...)`, and writer recipes, route to `../../universe-io/SKILL.md`; this page focuses on format selection, optional dependencies, and edge cases.

## Dispatch Rules

- `MDAnalysis.Universe(topology, *coordinates, format=None, topology_format=None, ...)` uses `topology_format=` for the first/topology argument and `format=` for coordinate arguments.
- `MDAnalysis.coordinates.core.reader(filename, format=None)` guesses trajectory format from extension unless `format` is passed.
- `MDAnalysis.coordinates.core.writer(filename, n_atoms=None, format=..., multiframe=...)` chooses a writer from the output extension or explicit `format`.
- `MDAnalysis.topology.core.get_parser_for(filename, format=None)` guesses topology parser from extension; if no topology parser exists but a coordinate reader can infer a minimal topology, MDAnalysis falls back to a minimal parser.
- Automatic guessing is disabled by explicit `format=`/`topology_format=`, except that a sequence of coordinate files is handled as a chained trajectory.

Use explicit formats when:

- A suffix is shared by multiple readers, such as PDB vs XPDB or LAMMPS DCD vs standard DCD.
- The input object is not a path, such as an RDKit molecule, OpenMM object, ParmEd structure, NumPy array, or Chemfiles trajectory.
- The filename has a compressed, nonstandard, temporary, or extensionless suffix.
- You want the Chemfiles backend for a format that MDAnalysis does not natively support.

## Coordinate Formats

MDAnalysis supports many coordinate readers/writers through native modules. Common families include:

| Family | Typical formats | I/O | Notes |
| --- | --- | --- | --- |
| CHARMM/NAMD | `DCD`, `CRD`, `NAMDBIN`, `coor` | read/write varies | DCD extension can also be used by LAMMPS; specify `format=` when ambiguous. |
| GROMACS | `XTC`, `TRR`, `TPR`, `TNG`, `GRO`, `TRC` | read/write varies | `TNG` needs `pytng`; `GRO` is single-frame; `TPR` topology support is limited/experimental for some versions. |
| AMBER | `TRJ`, `MDCRD`, `INPCRD`, `RESTRT`, `NCDF`, `NC` | read/write varies | NetCDF read uses SciPy; fast NetCDF write can use `netCDF4` when installed. |
| PDB-like | `PDB`, `ENT`, `XPDB`, `PDBQT`, `PQR`, `MMTF` | read/write varies | PDB can contain multiple MODEL frames; XPDB requires explicit `format="XPDB"` for extended residue numbers. |
| LAMMPS/DL_POLY/Tinker | `DATA`, `LAMMPSDUMP`, `CONFIG`, `HISTORY`, `TXYZ`, `ARC` | mostly read | Some formats provide minimal topology as well as coordinates. |
| Generic or chemistry | `XYZ`, `MOL2`, `GMS`, `FHIAIMS`, `DMS` | read/write varies | Attribute coverage differs by format; validate topology attrs before downstream conversion. |
| Optional backends | `H5MD`, `GSD`, `CHEMFILES`, `IMD` | read/write varies | Require optional packages; see the optional dependency map. |
| In-memory/special | NumPy arrays, `MemoryReader`, `NullReader`, `NullWriter` | internal | Useful for synthetic universes and tests; not a file format interchange guarantee. |

Compressed paths: a number of text-like formats can be read when gzip or bzip2 compressed, such as `.xyz.gz` or `.xyz.bz2`. Do not assume every binary or optional backend supports every compression wrapper; if guessing fails, try explicit `format=` only when the underlying reader supports that content.

Remote paths: native readers generally expect local paths or supported Python objects. Use `MDAnalysis.fetch.from_PDB(...)` for RCSB downloads, or download/cache remote files explicitly before creating a `Universe`. IMD is a streaming socket reader and is not a normal remote-file reader.

## Topology Formats

Topology parsers expose different attribute sets. Common choices:

| Format | Typical attributes | Notes |
| --- | --- | --- |
| `PSF` | names, types, charges, bonds, angles, dihedrals, impropers | Strong topology source for CHARMM/NAMD workflows. |
| `PDB`/`ENT` | names, bonds, resids, chain IDs, occupancies, tempfactors, resnames, segids | Good for structures but not full force-field topology; parser is simplified for MD use. |
| `XPDB` | PDB-like plus extended residue numbering | Use `topology_format="XPDB"`; evidence docs contain a typo-like warning, but the format string used by MDAnalysis is `XPDB`. |
| `PQR`/`PDBQT` | names, types, charges/radii or AutoDock atom types | Useful for electrostatics/docking-derived files; validate charge/radius semantics. |
| `GRO` | names, resids, resnames | Minimal topology; no full bond graph. |
| `PRMTOP`/`TOP`/`PARM7` | AMBER-style names, charges, types, resnames | Supports only a subset of AMBER flags. |
| `TPR`/`ITP` | GROMACS topology attributes | TPR support is limited/experimental for newer versions. |
| `MOL2` | ids, names, types, charges, bonds, resnames | Useful for small molecules and RDKit interoperability when elements/bonds are present or guessable. |
| `LAMMPS DATA` | ids, types, masses, charges, bonds, angles, dihedrals | Check atom style assumptions. |
| `GSD`/`HOOMD XML` | HOOMD particle types, masses, charges, topology where present | `GSD` needs `gsd`; HOOMD XML is deprecated upstream in favor of GSD. |
| Minimal parsers | XYZ, FHIAIMS, GAMESS, coordinate-only inputs | Provide only basic atom labels/indices; downstream workflows may need added topology attributes. |

If a downstream task needs selections, bonds, elements, masses, charges, or residues, confirm those attributes are present before analysis or conversion. Route topology attribute manipulation and guessing to `../../selections-topology/SKILL.md`.

## Optional Dependency Map

Install only the missing package for the requested workflow unless the user explicitly wants the whole optional group.

| User-facing failure or task | Package to check/install | MDAnalysis area | Notes |
| --- | --- | --- | --- |
| H5MD `.h5md` read/write fails with missing `h5py` | `h5py>=2.10` | `coordinates.H5MD` | H5MD also has strict unit and fixed-particle-count requirements. |
| Chemfiles backend fails | `chemfiles>=0.10,<0.11` for this code path | `coordinates.chemfiles` | Use `format="CHEMFILES"`; pass `chemfiles_format=` when Chemfiles cannot infer. |
| HOOMD GSD fails | `gsd>3.0.0` | `coordinates.GSD`, `topology.GSDParser` | Fixed particle count is required across frames. |
| TNG read fails | `pytng>=0.2.3` | `coordinates.TNG` | Reader only; no TNG writer currently. Special blocks must share compatible strides. |
| GROMACS EDR auxiliary fails | `pyedr>=0.7.0` | `auxiliary.EDR` | EDR units are converted where MDAnalysis knows the unit type. |
| RCSB PDB fetch fails before network | `pooch` | `fetch.from_PDB` | Network errors are separate; not all downloadable file formats are readable by MDAnalysis. |
| RDKit object or `convert_to("RDKIT")` fails | `rdkit>=2022.09.1` | `converters.RDKit`, selection SMARTS | Requires elements; bonds/hydrogens matter. |
| ParmEd object or `convert_to("PARMED")` fails | `parmed` | `converters.ParmEd` | Missing topology attributes are filled with defaults with warnings. |
| Interactive MD stream fails | `imdclient>=0.2.2` | `coordinates.IMD` | Live socket stream; forward-only, no random access. |
| AMBER NetCDF fast writer unavailable | `netCDF4>=1.0` | `coordinates.TRJ.NCDFWriter` | Reader uses SciPy NetCDF; writer falls back when `netCDF4` is absent but can be slow. |

The MDAnalysis `extra_formats` optional dependency group contains `netCDF4`, `h5py`, `chemfiles`, `parmed`, `pooch`, `pyedr`, `pytng`, `gsd`, `rdkit`, and `imdclient`. Prefer targeted installation guidance unless many optional workflows are explicitly required.

## Fetcher File Formats

`MDAnalysis.fetch.from_PDB(pdb_ids, cache_path=None, progressbar=False, file_format="cif.gz")` downloads and caches RCSB files with `pooch`.

Supported downloader `file_format` values are `cif`, `cif.gz`, `bcif`, `bcif.gz`, `xml`, `xml.gz`, `pdb`, `pdb.gz`, `pdb1`, and `pdb1.gz`. The downloader can fetch more formats than MDAnalysis necessarily reads as a `Universe`; choose `pdb`, `pdb.gz`, `cif`, or `cif.gz` only when the installed readers support the intended content.

Avoid using `fetch.from_PDB` in automated runtime scripts because it requires network access. For reproducible workflows, pass an explicit `cache_path`, catch HTTP errors, and validate the returned `Path` before loading.

## When to Avoid Optional Workflows

Avoid optional readers/converters when:

- The environment does not already have the optional package and the task can be solved with a native format.
- The user needs deterministic offline execution and the proposed path uses `fetch.from_PDB` or IMD streams.
- The target format cannot represent required metadata, such as full force-field terms, residue identity, charges, bond orders, velocities, forces, or unit-cell semantics.
- A converter would require guessing chemically important data, especially RDKit elements, bonds, explicit hydrogens, formal charges, or bond orders.
- The source has variable atom counts/topology across frames; H5MD, GSD, Chemfiles, and TNG readers document limitations around changing atom counts or stride consistency.

## Minimal Decision Checklist

1. Does the topology source carry the attributes the task needs?
2. Does the coordinate reader support the file and compression wrapper?
3. Is format guessing ambiguous enough to require `format=` or `topology_format=`?
4. Is the missing dependency narrow and safe to install, or should the user convert to a native format first?
5. Are units, box dimensions, velocities, forces, and auxiliary timing semantics important for the task?
6. Does the workflow require network access or a live socket, and has the user authorized it?
