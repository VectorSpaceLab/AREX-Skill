# Downloads, cache, and format dispatch

## Database download contract

The lower-level API is:

```python
from molecularnodes.download import StructureDownloader

downloader = StructureDownloader(cache=cache_dir)
result = downloader.download(code, format="bcif", database="rcsb")
```

`StructureDownloader(cache: str | Path | None = CACHE_DIR)` creates a cache
directory when `cache` is truthy. The package default is
`Path.home() / "MolecularNodesCache"`. Passing `cache=None` disables disk
caching and returns an in-memory buffer.

`download(code: str, format: str = "cif", database: str = "rcsb")` strips
surrounding whitespace from `code` and strips leading/trailing dots from
`format`. It accepts exactly:

| `format` | Remote URL for RCSB aliases | Return with cache | Return with `cache=None` |
|---|---|---|---|
| `cif` | `https://files.rcsb.org/download/{code}.cif` | `Path` | `io.StringIO` |
| `pdb` | `https://files.rcsb.org/download/{code}.pdb` | `Path` | `io.StringIO` |
| `bcif` | `https://models.rcsb.org/{code}.bcif` | `Path` | `io.BytesIO` |

`rcsb`, `pdb`, and `wwpdb` are aliases for these RCSB URL patterns. A cache
hit returns `{cache}/{code}.{format}` immediately and does not call HTTP; the
file's bytes are not revalidated by the downloader. A cache miss uses
`requests.get`, raises for HTTP status, transparently decompresses a gzipped
BCIF response, and writes the result in binary or text mode as appropriate.

The high-level API is:

```python
from molecularnodes import Molecule

mol = Molecule.fetch(
    code="4ozs",
    format=".bcif",       # dot is accepted
    cache=cache_dir,       # use None only when a compatible buffer is intended
    database="rcsb",
)
```

`Molecule.fetch(...)` delegates to the downloader, calls
`Molecule.from_file(...)`, names the entity with the accession, and records
`mol.props.code` and `mol.props.database`. The returned entity is a Blender
object/MDAnalysis Universe workflow, so call it in a Blender/bpy host when the
object must be created.

## Validation and deterministic errors

- Unsupported format: `ValueError` with the supported list `cif`, `pdb`,
  `bcif`. Do not pass SDF/STAR to `StructureDownloader`; those are local input
  routes.
- Unsupported database: `ValueError` from `_url`, with the supported RCSB
  aliases listed above. `alphafold` is handled separately by Biotite's
  `afdb.fetch`; it does not produce an RCSB URL.
- HTTP failure: `FileDownloadPDBError`. The high-level Blender operator reports
  this error and additionally suggests a non-PDB format when `pdb` was chosen.
- New-format accessions beginning with `pdb_`: requesting `pdb` raises
  `ValueError`; use `cif` or `bcif` instead. The restriction is format-specific,
  not a statement that the accession is invalid.
- Text/binary mismatch: a non-string text response or non-bytes BCIF response
  raises `ValueError`; investigate the server/proxy response rather than
  handing it to a parser.

A network error such as DNS failure or connection refusal is outside the
structured `FileDownloadPDBError` path and may surface as a requests exception.
Treat it as an external boundary, use a known local file or a valid cache hit,
and do not loop retries without a stop condition. The source downloader does
not accept API-key parameters and should not be modified to put credentials in
URLs or skill files.

## Local structure dispatch

The public dispatcher is:

```python
from io import BytesIO
from pathlib import Path
from molecularnodes.entities.molecule.reader import read_structure

reader = read_structure(file_path: str | Path | BytesIO)
```

The return type is a `ReaderBase` subclass whose `.array` is a Biotite
`AtomArray` or `AtomArrayStack`. `ReaderBase` adds standard annotations and
exposes `n_models`, `chain_ids()`, `entity_ids()`, and `assemblies(...)`.
Dispatch is based on the exact, lowercase `Path.suffix`:

| Suffix/input | Reader | Notes |
|---|---|---|
| `.pdb` | `PDBReader` | PDB records, bonds when available, secondary structure, PDB assemblies |
| `.cif` | `PDBXReader` | mmCIF text, entity/secondary-structure metadata, CIF assemblies |
| `.bcif` | `PDBXReader` | BinaryCIF file |
| `.sdf`, `.mol` | `SDFReader` | Biotite MOL reader; bonds are retained when supplied |
| `BytesIO` | intended BCIF route | use a cached `.bcif` `Path` if the in-memory route fails the suffix check |

An unknown suffix raises Biotite `InvalidFileError("The file format is not
supported.")`. The dispatcher does not inspect magic bytes or content. Uppercase
suffixes and aliases such as `.mmcif`, `.pdbx`, and `.ent` are not accepted by
this reader even though the Blender file handler advertises `.mmcif` and
`.pdbx`. Rename only when the content really is the corresponding format, or
convert it with a trusted structure tool; do not merely change a label for an
unrelated file.

`Molecule.from_file(file_path, name=None)` calls this dispatcher, converts the
Biotite array with `universe_from_atoms`, and stores source metadata on the
Blender object. `Molecule.load(path)` is the convenient single-structure entry
point. A successful load should have a nonzero `universe.atoms.n_atoms`; a
multi-model PDBx/BCIF stack becomes multiple Universe trajectory frames.

## UI import entry points

The add-on's main operator is:

```python
bpy.ops.mn.import_fetch(
    database="local",       # or "wwpdb" / "alphafold"
    filepath=str(path),      # used for local
    code="4ozs",            # used for remote
    file_format="bcif",     # remote wwPDB: bcif, cif, or pdb
    cache_dir=str(cache_dir),
    node_setup=False,
)
```

For a reliable local diagnostic, call `Molecule.load` directly first. The
multi-file file-browser operator catches per-file exceptions and prints them,
which can make a partially completed operation look successful. Once the
parser is known to work, the UI operator is appropriate for creating the
scene object and optional initial node setup.

## Trajectory and ensemble path selection

A standard local topology plus trajectory uses MDAnalysis and bypasses
`read_structure` for the coordinate stream:

```python
mol = Molecule.load(
    topology=topology_path,
    coordinates=trajectory_path,
    name="system",
    create_object=True,
    **universe_kwargs,
)
```

The topology and coordinate paths must describe the same atom count/order.
The resulting Universe owns the trajectory; playback, interpolation, and
selection updates belong to
[the trajectories sibling](../../trajectories-and-annotations/SKILL.md).
`imd://...` streaming endpoints and oxDNA custom readers are not ordinary local
file suffixes and must use that sibling route.

For local STAR and CellPack files, select the ensemble route rather than
`Molecule.load`:

```python
from molecularnodes.entities.ensemble import CellPack, StarFile

ens = StarFile.load(star_path, name=None, node_setup=True)
pack = CellPack.load(cellpack_path, name=None, node_setup=True)
```

STAR parsing expects a supported RELION >=3.1 or cisTEM schema. Its referenced
micrographs may be relative to the STAR file and can require adjacent files;
missing micrographs are a data-layout failure, not a PDB download failure. Use
[density-and-ensembles](../../density-and-ensembles/SKILL.md) for STAR/CellPack
semantics and density inputs.

## Cache-first offline procedure

1. Normalize the requested accession and format, including the format dot.
2. Compute the expected cache path `{cache}/{code}.{format}`.
3. If it exists, use it as a local input and do not request the network.
4. If it does not exist, ask whether network access is permitted. If not,
   report that the input is unavailable offline.
5. After a fetch, verify the file is nonempty and has the expected text/binary
   mode before parsing it.
6. On parser failure, preserve the original file for diagnosis and retry with a
   new cache location or a different format; do not silently overwrite a
   possibly corrupt cache hit.

For a BCIF with `cache=None`, the downloader returns `io.BytesIO`. The
current reader dispatch intends to recognize that as BCIF, but the PDBX reader
implementation still assumes a path-like `.suffix` in its file-read branch.
When that mismatch appears, use `cache=some_directory` and pass the resulting
`.bcif` `Path` to `Molecule.from_file`; record the in-memory-path limitation
rather than pretending the buffer was parsed.
