---
name: setup-and-import
description: "Install and verify MolecularNodes in a Blender 5.2 host, then
  choose safe local, cached, or database-backed structure import paths and
  recover setup failures."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# MolecularNodes setup and import

Use this route when the task is to make MolecularNodes available in Blender,
check its Python package/backend compatibility, import a structure or supported
input file, or diagnose an installation, download, cache, or format error.
This route assumes MolecularNodes 5.2.0 and a Blender/bpy 5.2 Python 3.13 host.

## Route boundaries

This skill owns:

- Blender extension installation and update checks.
- Python package and `bpy` compatibility checks.
- The `MolecularNodes` import panel/operator entry points.
- Database download, cache selection, local structure dispatch, and input
  validation.
- The setup-side choice between a single structure and a topology plus
  trajectory path.

It does not own styling, selections, geometry-node editing, trajectory
playback/analysis, annotations, density styling, or rendering. Route those
parts to [molecules-and-styles](../molecules-and-styles/SKILL.md),
[trajectories-and-annotations](../trajectories-and-annotations/SKILL.md),
[density-and-ensembles](../density-and-ensembles/SKILL.md), and
[scene-and-rendering](../scene-and-rendering/SKILL.md).

For the detailed installation contract, read
[references/installation.md](references/installation.md). For download,
format, and loader behavior read
[references/download-and-formats.md](references/download-and-formats.md).
For diagnosis and recovery read
[references/troubleshooting.md](references/troubleshooting.md).

## Route selection

Use the smallest route that matches the input. Keep the parser check separate
from the Blender presentation step.

| Request or input | Route | Next boundary |
|---|---|---|
| Install, update, or prove the runtime | Extensions panel plus `check_install.py` | [references/installation.md](references/installation.md) |
| One local `.pdb`, `.cif`, `.bcif`, `.sdf`, or `.mol` | `Molecule.load(path)` or the local import operator | This skill owns validation and dispatch |
| One RCSB/wwPDB or AlphaFold accession | `Molecule.fetch(...)` or `mn.import_fetch` | This skill owns cache/network diagnosis |
| MD topology plus coordinates, IMD, or oxDNA | `Molecule.load(topology, coordinates)` only for local MD; otherwise sibling route | [trajectories-and-annotations](../trajectories-and-annotations/SKILL.md) |
| STAR, CellPack, density, or ensemble data | Ensemble/density loader, not `Molecule.load` | [density-and-ensembles](../density-and-ensembles/SKILL.md) |
| Styling, selections, node editing, or rendering after import | Preserve the loaded object and hand off | [molecules-and-styles](../molecules-and-styles/SKILL.md) or [scene-and-rendering](../scene-and-rendering/SKILL.md) |

## Preconditions

1. Confirm that Blender is running as the host, not a system Python shell.
   `bpy.app.version` must be 5.2.0 or newer; the package's Python `bpy` extra
   is specifically `bpy==5.2.*`.
2. Prefer the Blender Extensions **Get Extensions** panel for the add-on. Do
   not silently install packages into a user environment or assume that a
   plain CPU Python import proves Blender UI compatibility.
3. If inspecting from Python, use Python 3.13 and the package's `bpy` extra.
   The runtime package also requires databpy, nodebpy, Biotite, MDAnalysis,
   and the direct dependencies listed in
   [references/installation.md](references/installation.md).
4. Run the bundled, network-free check before attempting a data fetch:
   [scripts/check_install.py](scripts/check_install.py). It reports package
   metadata, imports, and the host `bpy` version without installing, fetching,
   creating a cache, or importing this source checkout by default.

## Installation and first verification

1. Install Blender 5.2 or later for the current extension manifest and start a
   clean Blender session.
2. Open Preferences → **Get Extensions**, search for **Molecular Nodes**, and
   install or update it. The extension supplies its declared Python wheels;
   allow network and file access only for the documented data/import actions.
3. If the extension cannot be installed, stop before importing data. Check
   `bpy`, `biotite`, and Python-version compatibility with the bundled script,
   then follow [references/troubleshooting.md](references/troubleshooting.md).
4. In the 3D View/Scene Properties Molecular Nodes panel, verify that the
   import operators are present. The principal scripted entry point is
   `bpy.ops.mn.import_fetch`; local multi-file import also uses
   `bpy.ops.mn.import_molecule`.
5. Perform a deterministic local import first when a fixture is available.
   This separates parser/backend problems from network and credentials.

## Choose an import path

### Local single structure

Use `Molecule.load(path)` or `Molecule.from_file(path)` for a local
`.pdb`, `.cif`, `.bcif`, `.sdf`, or `.mol`. The result is a Universe-backed
`Molecule`; successful parsing also records chain/entity/assembly metadata
where the file provides it. The dispatcher is suffix-based, so validate the
suffix rather than guessing from file contents. The public type annotation also
mentions `io.BytesIO` for BCIF, but the 5.2.0 `PDBXReader` still accesses
`.suffix`; use a cached `.bcif` `Path` when the in-memory route fails.

The UI equivalent is `bpy.ops.mn.import_fetch(database="local",
filepath=str(path), node_setup=...)`. Use an absolute or Blender-resolvable
path and confirm the file exists before invoking it.

### Database structure

Use `Molecule.fetch(code, format=".bcif", cache=..., database="rcsb")` for
RCSB/wwPDB downloads, or the lower-level
`StructureDownloader(cache=...).download(code, format, database)` when the
returned path/buffer must be inspected. Prefer cached BCIF for repeatable
work. A cache hit must be used without an HTTP request; a cache miss requires
network access.

Only `cif`, `pdb`, and `bcif` are downloader formats. New `pdb_...` accession
codes cannot be requested as PDB text; select CIF or BCIF. AlphaFold is a
separate Biotite-backed database route and is not the same as the RCSB URL
builder.

### Topology plus trajectory

Use `Molecule.load(topology, coordinates, ...)` when `coordinates` is a local
MDAnalysis-readable trajectory. Keep topology and coordinates compatible and
preserve both paths. This route constructs an MDAnalysis Universe rather than
using the Biotite structure-file dispatcher. Streaming IMD and oxDNA have
separate loaders; route them through
[trajectories-and-annotations](../trajectories-and-annotations/SKILL.md).

### STAR, CellPack, and other non-molecule inputs

A `.star` file is an ensemble input, not a `Molecule` structure. Use
`entities.ensemble.StarFile.load(path, name=None, node_setup=True)` for
RELION >=3.1 or cisTEM STAR files. CellPack `.cif`/`.bcif` models use
`entities.ensemble.CellPack.load(path, name=None, node_setup=True)`; do not
mistake them for an ordinary atom structure if the file is a packing model.
Detailed ensemble behavior belongs to
[density-and-ensembles](../density-and-ensembles/SKILL.md).

## API contract

- `read_structure(file_path: str | Path | io.BytesIO) -> ReaderBase`: for a
  supported path, returns `PDBReader`, `PDBXReader`, or `SDFReader`, and raises
  Biotite `InvalidFileError` for an unsupported suffix. Although `BytesIO` is
  accepted by the dispatcher annotation, the current BCIF reader can fail
  while reading the buffer because it expects a path suffix.
- `Molecule.from_file(file_path, name=None) -> Molecule`: parses one structure,
  converts the Biotite array to an MDAnalysis Universe, and stores source
  metadata. Use a path for the reliable 5.2.0 path-backed route; do not claim
  an in-memory BCIF load succeeded unless it was actually observed.
- `Molecule.load(topology, coordinates=None, name=None, style=None,
  selection=None, create_object=True, **kwargs) -> Molecule`: selects the
  structure or MD route and optionally adds a style. `create_object=False`
  affects the topology-plus-trajectory MD route; the single-file path goes
  through `from_file` and creates its Blender object.
- `Molecule.fetch(code, format=".bcif", cache=CACHE_DIR,
  database="rcsb") -> Molecule`: downloads/caches, delegates to
  `from_file`, and records `props.code` and `props.database`.
- `StructureDownloader(cache=CACHE_DIR).download(code, format="cif",
  database="rcsb") -> Path | io.BytesIO | io.StringIO`: returns a cached path
  or an in-memory buffer when caching is disabled.

Arguments are inputs; return values and recorded source paths are outputs.
Do not pass a `.star` file to `Molecule.load`, and do not pass a trajectory as
`coordinates` without a compatible topology.

## Validation and recovery loop

After each setup/import attempt, check:

- `bpy.app.version`, package metadata, and imports pass.
- The source path exists and its suffix is supported.
- A local load has nonzero atoms and the expected number of frames.
- A fetched load records the requested code/database. For a cached RCSB/wwPDB
  download, the cache contains the requested `code.format` file; AlphaFold
  cache naming is delegated to Biotite and must be observed rather than
  assumed.
- For CIF/BCIF files, assemblies may be absent; absence is not itself a parse
  failure. If an assembly is requested, verify `Molecule.assemblies()` first.

On failure, classify it before retrying: host/package dependency, unsupported
format/database, local path/content, cache state, or network/server. Use the
specific recovery matrix in
[references/troubleshooting.md](references/troubleshooting.md). Do not retry
network calls indefinitely, add credentials to source files, or bypass an
unsupported format by changing only a UI label.

## Hard cases and stop conditions

- Missing `bpy` or `biotite` is an installation/backend block, not a data
  problem. Repair the Blender extension or compatible Python environment.
- An existing cached BCIF should win over a network fetch. If its bytes are
  invalid, move it aside or choose a new cache and report the corruption; do
  not overwrite it blindly.
- A downloader `ValueError` for a format or database is deterministic. Change
  the input to a supported option or route to the appropriate sibling skill.
- Network service availability and any institutional access restriction are
  external boundaries. A local file or valid cache is the offline fallback;
  report when no local replacement exists. This package's downloader does not
  define a credential argument.

The bundled checker is intentionally read-only and offline: see
[scripts/check_install.py](scripts/check_install.py). Known compatibility and
format caveats are maintained in
[references/troubleshooting.md](references/troubleshooting.md).
