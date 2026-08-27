# Setup and import troubleshooting

Use this matrix to classify the boundary before changing inputs. Keep the
original command, exception class, package versions, source path type, and
cache state. Do not repeatedly retry a network request or overwrite a
suspicious cache hit.

## Installation, imports, and compatibility

| Symptom | Likely boundary | Recovery |
|---|---|---|
| `check_install.py` exits nonzero | The required host, import, or version contract is not proven | Read every `FAIL`; repair the Blender extension or the isolated Python 3.13 environment, then rerun the checker. It performs no installation or fetch. |
| Python is not 3.13.x | The package declares `requires-python = "~=3.13.0"` | Use Blender/bpy 5.2's Python or a separate Python 3.13 environment. Do not infer compatibility from a successful import under another Python. |
| `No module named bpy` | A system Python is being used without the Blender API, or the extension/bpy extra is incomplete | Prefer Blender **Get Extensions**. For package inspection only, install `molecularnodes[bpy]==5.2.0` into a separate Python 3.13 environment. This does not install desktop Blender. |
| `No module named databpy`, `nodebpy`, `biotite`, or `MDAnalysis` | A direct runtime wheel is missing or cannot load for the host | Repair/reinstall the 5.2 extension or its compatible environment. Do not diagnose this as a structure-format error. |
| `pandas` is 3.x | The package declares `pandas<3.0.0` | Use a compatible environment or extension build. An import that succeeds with pandas 3.x is not a verified MolecularNodes runtime. |
| `nodebpy` is below 520.11 | Declared package requirement is unsatisfied | Upgrade the runtime. The current source manifest also lists a 520.10.0 nodebpy wheel while `pyproject.toml` requires >=520.11; treat that as a packaging/release block and verify the built extension. |
| `molecularnodes` imports but the API probe is missing `Molecule`, `StructureDownloader`, or `read_structure` | Wrong package, partial install, or version skew | Confirm the distribution is MolecularNodes 5.2.0 and rerun the checker outside any source checkout. Do not fix this by changing `PYTHONPATH` to an arbitrary checkout. |
| `bpy.app.version` is below 5.2.0 | Host mismatch | Stop and use Blender 5.2 or a declared compatible newer host. The 5.2.0 extension manifest is the package-baseline signal; older tutorial examples are not. |
| The package imports in Python but `bpy.ops.mn.import_fetch` is absent | The add-on is not registered/enabled in that Blender session | Enable or reinstall the extension and start a clean session. A plain package import does not register Blender operators. |
| The package import fails only because `mrcfile`, `starfile`, `imdclient`, `gridData`, Pillow, or SciPy is absent | An eager import or a route dependency is incomplete | Repair the complete extension dependency set. `imdclient` is for IMD, `mrcfile`/`starfile` for ensemble or density paths, and `gridData` for density grids; route-specific absence may nevertheless surface at top-level import time. |

The checker intentionally treats metadata from the current source checkout as
unusable by default. Use its explicit `--repo-root` option only when you want a
read-only `pyproject.toml`/manifest metadata audit; it never imports or runs
code from that root.

## Local files, configuration, and API misuse

| Symptom | Likely boundary | Recovery |
|---|---|---|
| Local path is missing, a directory, unreadable, or zero bytes | Input validation or filesystem permissions | Resolve the path, check `is_file()` and size/read access, and use a known local fixture. Do not invoke the operator until this passes. |
| `InvalidFileError: The file format is not supported` | Suffix dispatch | The structure reader accepts lowercase `.pdb`, `.cif`, `.bcif`, `.sdf`, and `.mol`. It does not inspect magic bytes and does not accept `.mmcif`, `.pdbx`, uppercase suffixes, or `.star` as ordinary molecule input. Rename only when the bytes genuinely match the target format. |
| Blender's file handler accepts `.mmcif` or `.pdbx`, but import fails | UI filter is broader than `read_structure()` | Use `.cif`/`.bcif` with content that matches the suffix, or convert with a trusted structure tool. Do not change only the label on unrelated bytes. |
| `Molecule.load()` receives a STAR, CellPack, or density input | Wrong entity route | Use `StarFile.load()` or `CellPack.load()` for ensembles and hand off to [density-and-ensembles](../../density-and-ensembles/SKILL.md) for ensemble/density semantics. |
| `Molecule.load(topology, coordinates)` fails with topology/trajectory errors | MDAnalysis cannot read one file, or atom count/order is incompatible | Validate each file with the MDAnalysis-supported reader, compare atom count and ordering, and preserve both paths. Do not pass a trajectory as the single-structure topology. Hand off playback or streaming to [trajectories-and-annotations](../../trajectories-and-annotations/SKILL.md). |
| `Molecule.load(path, create_object=False)` still creates an object | `create_object` is honored on the topology-plus-trajectory MD route, not the single-file `from_file` route | Use the MD route when an in-memory/non-object load is required; otherwise expect a Blender object from a single structure. |
| `Molecule.fetch(..., file_format=...)` raises an unexpected keyword error | Python API and Blender operator use different names | `Molecule.fetch()` and `StructureDownloader.download()` use `format=`; `bpy.ops.mn.import_fetch` uses `file_format=`. The UI database enum is `wwpdb`, while the Python downloader's RCSB aliases are `rcsb`, `pdb`, and `wwpdb`. |
| `database="alphafold"` is passed to `_url()` or a raw RCSB helper | AlphaFold is not an RCSB URL alias | Use `Molecule.fetch(..., database="alphafold")`/the operator's AlphaFold route and let Biotite's `afdb.fetch` handle it. Do not call `_url()` as a public API. |
| `BytesIO` BCIF load raises an attribute/suffix error | Known 5.2.0 in-memory reader limitation | Use `StructureDownloader(cache=<dir>)` and pass the resulting `.bcif` `Path` to `Molecule.from_file()`. Preserve the buffer failure as evidence. |
| Biological assembly is empty or absent | The source has no assembly category, or the selected reader cannot provide one | A missing assembly is not a parse failure. Check `reader.assemblies()`/`Molecule.assemblies()` before requesting assembly instancing. |
| `node_setup`, `style`, or `assembly` errors obscure the parser result | Presentation or Blender-object phase failed after parsing | First run a direct local `Molecule.load(path)` without styling, assembly, or network. Once the object and atom count are known, invoke the UI path. |

Blender-relative paths such as `//file.cif` are resolved by Blender's path
helpers, not by a system shell. In a headless or external Python process use an
absolute path or a path resolved by the host. Keep cache directories explicit;
the source default is `Path.home() / "MolecularNodesCache"`, not the older
hidden-directory wording in some tutorials.

## Download, cache, format, and network failures

| Symptom | Likely boundary | Recovery |
|---|---|---|
| Downloader rejects a format | Deterministic API misuse | `StructureDownloader` accepts only `cif`, `pdb`, and `bcif` (a leading dot is stripped). SDF/MOL and STAR are local routes, not downloader formats. |
| Downloader rejects a database | Unsupported URL route | RCSB aliases are `rcsb`, `pdb`, and `wwpdb`; AlphaFold is handled separately by Biotite. Do not invent another database string. |
| A `pdb_...` accession rejects `format="pdb"` | New-format accession restriction | Request `cif` or `bcif`; the accession itself is not necessarily invalid. |
| A cache hit parses badly | Corrupt, stale, or wrong-format cache content | Do not overwrite it blindly. Preserve or move it aside, check nonzero size and expected text/binary mode, use a new cache directory, and parse locally before allowing a new request. |
| Cache directory cannot be created or written | Filesystem permission/configuration | Choose an explicit writable cache directory in Molecular Nodes preferences or the API. The downloader creates a truthy cache directory; `cache=None` disables disk caching. |
| Cache is enabled but the expected file is absent after a fetch | Fetch failed, AlphaFold chose different naming, or the cache path differs from the active preference | Record the effective cache path and returned object type/path. For RCSB expect `{cache}/{code}.{format}`; do not assume AlphaFold's internal naming. |
| `FileDownloadPDBError` or an HTTP status error | Server rejected the requested accession/format | Check code, database, and format. For PDB text failure, try CIF/BCIF as the operator itself suggests; then use a known local file. |
| DNS failure, connection refusal, proxy error, or timeout | External network boundary | Stop after a bounded attempt, use a valid cache or local replacement, and report that network availability was not verified. The downloader does not accept an API-key parameter and credentials must not be put in URLs or skill files. |
| Downloaded bytes are not parseable, text/binary type check fails, or compressed BCIF is damaged | Proxy/server response or corrupted transfer | Preserve the response/cache file, compare its expected mode and nonzero size, choose another format/cache, and do not pass it to a parser merely because the HTTP request returned. |
| Network is unavailable and no cache/local file exists | No offline source | Report the missing input and stop. This skill does not synthesize a structure or silently switch to another accession. |

The downloader returns a cached `Path` when caching is enabled, `StringIO` for
uncached text, and `BytesIO` for uncached BCIF. The latter is a known limitation
for the current PDBX reader, so a cached path is the reliable diagnostic route.
A cache hit is returned without byte revalidation; parsing is the first content
check.

## Blender UI and headless limits

- `check_install.py` verifies imports, package metadata when available, Python,
  and `bpy.app.version`; it never creates Blender data, registers operators,
  opens a file, reads a fixture, populates a cache, or makes a network request.
- `bpy.ops.mn.import_fetch` and `bpy.ops.mn.import_molecule` are Blender
  operators. They can depend on registration, an active context, file-browser
  state, and a 3D View/Scene setup. A headless `bpy` import does not prove that
  the Extensions panel, viewport redraw, drag-and-drop file handler, or GPU
  rendering works.
- A headless Blender process can be useful for a controlled API smoke check,
  but any operator/context failure must be separated from package parsing and
  from network availability. Do not claim UI success from `import molecularnodes`
  alone.
- The extension's declared network and file permissions permit its documented
  data/import actions; they do not guarantee a remote service, writable cache,
  desktop UI, credentials, or GPU access.

## Bounded diagnostic order

1. Run the bundled checker and keep its complete output.
2. Confirm the Blender host and extension registration if the target is a UI
   operation; repair required imports before touching data.
3. Validate one local file path, exact lowercase suffix, nonzero size, and direct
   `Molecule.load(path)` behavior.
4. For topology plus trajectory, validate both paths and their atom contract.
5. Only after local parsing works, choose a cache path and attempt one bounded
   database fetch. Record code, database, format, returned type/path, and cache
   state.
6. Hand off styling, trajectory analysis/playback, density/ensemble semantics,
   or rendering after setup/import is proven.

Do not run native repository tests or examples as part of this route's install
check. Those are separate verification activities and may require fixtures,
network, a full Blender session, or additional hardware.
