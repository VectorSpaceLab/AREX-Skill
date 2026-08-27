# Installation and compatibility

## Runtime contract

MolecularNodes 5.2.0 is a Blender extension and a Python package. The required
execution host is Blender 5.2 with Python 3.13 and the `bpy` 5.2 API. A plain
CPython process can validate parsing helpers, package metadata, and selected
imports, but it is not proof that Blender UI operators, node groups, or file
handlers work.

The current package metadata declares Python `~=3.13.0` and these direct
runtime requirements:

| Component | Baseline | Why setup needs it |
|---|---:|---|
| `bpy` extra | `5.2.*` | Blender host API for the package and operators |
| `databpy` | `>=0.8.0` | Blender data/object helpers |
| `nodebpy` | `>=520.11` | Geometry-node and material builders |
| `biotite` | `>=1.7.1` | PDB, CIF, BCIF, and SDF/MOL parsing |
| `MDAnalysis` | `>=2.10` | Universe and topology-plus-trajectory loading |
| `mrcfile`, `starfile` | package requirements | density/STAR routes; STAR is owned by the ensemble sibling |
| `imdclient`, `pandas<3`, `griddataformats` | package requirements | streaming, tabular ensemble, and density support |

The source declares minimums for databpy 0.8.0, nodebpy 520.11, MDAnalysis
2.10, and Biotite 1.7.1; it also requires `pandas<3.0.0` and Python 3.13.x.
Do not call these versions installed until the checker reports them. The
current source has a packaging inconsistency worth resolving before publishing:
`pyproject.toml` requires `nodebpy>=520.11`, while the extension manifest lists
a `nodebpy-520.10.0` wheel. `check_install.py --repo-root ...` flags that
metadata mismatch without importing or executing the checkout.

## Preferred Blender extension installation

1. Install Blender 5.2 or a compatible later Blender host.
2. Start Blender and open **Edit → Preferences → Get Extensions**.
3. Search for **Molecular Nodes**, then click **Install**. Use the same panel
   for updates; restart Blender if the extension list or operators do not
   refresh.
4. The extension manifest identifies the add-on as `molecularnodes`, version
   5.2.0, and a minimum Blender version of 5.2.0. It targets Windows x64,
   Linux x64, and macOS arm64.
5. The manifest declares network permission for downloading structural data
   from the PDB/AlphaFold sources and file permission for importing files and
   caching downloads. These permissions do not imply arbitrary credential
   access or that a remote service is available.

The project README and installation tutorial still mention Blender 4.2 as the
minimum for the historical Extensions workflow. The current 5.2.0 extension
manifest is the stronger compatibility signal for this package baseline: use a
5.2 host and treat a 4.2 host as unsupported here.

### Route-specific dependencies

The package's direct dependencies are installed by the extension or by the
normal package install; do not install a second copy into Blender's Python.
`imdclient` is needed only for IMD streaming, `mrcfile` and `starfile` are
needed for density/STAR workflows, `griddataformats` is used by density grid
loading, and the `pandas<3` constraint is used by ensemble data handling. The
`jupyter` extra is for notebook use and is not needed for Blender imports. Dev
packages such as `fake-bpy-module` and `pytest` are not runtime substitutes for
`bpy` or the extension. A route-specific missing dependency can still prevent
the eager top-level `molecularnodes` import, so verify the whole runtime before
blaming an input file.

After installation, open the Molecular Nodes panel and check that the add-on's
operators are registered. The useful scripted smoke check is:

```python
import bpy
import molecularnodes as mn

assert bpy.app.version[:2] >= (5, 2)
assert hasattr(mn, "Molecule")
assert hasattr(bpy.ops.mn, "import_fetch")
```

A clean local structure import should be the first end-to-end check. It avoids
confusing missing dependencies with DNS, server, or cache failures.

## Python package inspection

For a separate Python 3.13 inspection or headless parsing environment, install
the package with its Blender API extra using the package manager appropriate to
the user environment, for example:

```bash
python -m pip install "molecularnodes[bpy]==5.2.0"
```

This installs the `bpy==5.2.*` wheel and package dependencies into that
Python environment. It does not install the desktop Blender application and it
does not validate viewport behavior. Keep this environment separate from a
user's existing Blender installation unless the user explicitly requests a
repair.

Use the bundled offline checker before any network operation:

```bash
python path/to/setup-and-import/scripts/check_install.py
python path/to/setup-and-import/scripts/check_install.py --repo-root /path/to/a/checkout
```

The optional `--repo-root` argument is read-only. It checks that the supplied
root has package metadata and the expected source/manifest files; it never
installs, edits, fetches, or executes code from that root.

## Blender-side import entry points

The add-on exposes these setup-relevant operators:

- `bpy.ops.mn.import_fetch`: local structure or database-backed structure. For
  local use, pass `database="local"` and `filepath=...`; for a download pass
  `code`, `database`, `file_format`, and optionally `cache_dir`.
- `bpy.ops.mn.import_molecule`: file-browser route for one or more local
  structure files. The registered file handler advertises `.pdb`, `.cif`,
  `.mmcif`, `.bcif`, and `.pdbx`, but the Python reader's dispatch is narrower;
  see [download-and-formats.md](download-and-formats.md) before using an
  advertised suffix.
- `bpy.ops.mn.import_ensemble`: STAR or CellPack route. It is not a molecule
  parser and is covered only to prevent selecting the wrong entry point.

The UI's structure download formats are `bcif` (default), `cif`, and `pdb`.
The UI's database choices are wwPDB, local file, and AlphaFold. `node_setup`
and `style` affect presentation; they are not needed to diagnose whether the
source parsed. `assembly` requests biological-assembly handling and should be
checked only after the reader has loaded the file.

## Installation acceptance checklist

Record the following observations rather than claiming success from an
unexecuted command:

- Blender or `bpy` version is 5.2-compatible.
- `molecularnodes` reports 5.2.0 and imports.
- `biotite`, `MDAnalysis`, `databpy`, and `nodebpy` import in the same host.
- `bpy.ops.mn.import_fetch` is registered when testing the extension/UI path.
- One small local PDB/CIF/BCIF or SDF fixture loads and has atoms.
- If a database fetch is attempted, network permission and cache destination
  are explicit and the returned file/buffer is inspected.

A missing `bpy` module, an import failure in `biotite`, an unsatisfied direct
requirement (including an installed `pandas` 3.x), or a host-version mismatch is a
required-runtime block. Follow [troubleshooting.md](troubleshooting.md), then
rerun the checker and a local fixture test. Do not downgrade the claim to
“installed” because a pure Python helper imported. Missing route-specific
packages such as `imdclient`, `mrcfile`, or `starfile` block only the routes
that use them, but the package's eager top-level imports can make a missing
runtime dependency surface as an overall `molecularnodes` import failure.
