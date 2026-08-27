---
name: density-and-ensembles
description: "Operate MolecularNodes density-grid and ensemble workflows in a
  Blender 5.2 host, including local cryo-EM maps, CellPack CIF/BCIF models, and
  RELION or cisTEM STAR metadata."
disable-model-invocation: true
metadata:
  disco-role: operating
license: NOASSERTION
---

# Density and ensembles

Use this sub-skill when the task involves an EM density volume, APBS/DX/MRC data,
cryo-EM map alignment, a CellPack assembly, or a RELION/cisTEM STAR point
ensemble. It assumes a Blender 5.2-compatible `bpy` host with MolecularNodes
5.2.0 and its bundled OpenVDB support. Python-only parsing is useful for
preflight, but cannot create the runtime volume or Geometry Nodes object.

## Scope and routing

- **Density grid:** route to [`references/density-api.md`](references/density-api.md)
  for `Grids.load`, format dispatch, VDB conversion, styles, attributes, and
  annotations.
- **STAR or CellPack:** route to
  [`references/ensemble-formats.md`](references/ensemble-formats.md) for schema
  detection, transforms, metadata, and collection ownership.
- **Map plus atomic model:** route to
  [`references/cryoem-workflows.md`](references/cryoem-workflows.md) for
  alignment, threshold/contour/slice choices, and local-file-first behavior.
- **Any failure or stale scene:** use
  [`references/troubleshooting.md`](references/troubleshooting.md) before
  retrying or downloading data.

Do not use this sub-skill for general molecule styles, trajectory playback, or
Canvas lighting/compositor configuration; hand those parts to sibling skills.

## Required input contract

Collect a real local `file_path` before loading. Accept `str` or `pathlib.Path`.
Record whether the input is a grid (`.dx`, `.mrc`, `.map`, `.ccp4`, `.plt`,
`.pickle`, including supported compressed forms), STAR (`.star`), or CellPack
(`.cif`/`.bcif`). Reject an absent path, directory, unsupported suffix, or
zero-byte file before entering Blender's importer. An EMDB identifier is a
network/data-acquisition request, not a local path; keep it outside the default
runtime route.

For every import, decide explicitly:

1. whether coordinates must remain in source placement or be centered;
2. whether values need inversion (common for tomograms with reversed contrast);
3. whether to create the default Geometry Nodes style (`node_setup=True` for
   ensembles, a named density style for grids); and
4. which local fixture or already-downloaded file is the fallback if validation
   fails.

## Density execution route

```python
import molecularnodes as mn

density = mn.entities.density.Grids.load(
    file_path=local_map,
    name="map-name",                 # optional
    style="density_surface",         # or density_iso_surface/density_wire/None
    invert=False,
    center=False,
    overwrite=False,
)
```

The call parses the grid, writes a neighboring `.vdb` cache, imports that VDB
into the Molecular Nodes collection, sets the object location to `(0, 0, 0)`,
and records the original path in `density.object.mn.filepath`. `center` and
`invert` are part of the VDB cache identity; use `overwrite=True` when a
previous conversion was made with the wrong options or stale data.

Validate `density.object`, `density.grid`, `density.props.entity_type ==
"density"`, `density.object.location`, and the first entry of
`density.object.users_collection`. Use `density.named_attribute("position")`
only after the object and modifier exist. Inspect the density style node's
exposed `Threshold` or `ISO Value` socket rather than assuming a Python property
name. Contours, negative/positive colors, and slicing belong to the ISO style;
see the density reference for the socket-level mapping.

## Ensemble execution route

```python
star = mn.entities.ensemble.StarFile.load(
    local_star, name="particles", node_setup=True
)
cellpack = mn.entities.ensemble.CellPack.load(
    local_cif_or_bcif, name="pack", node_setup=True
)
```

A STAR load creates one point object with numeric/categorical named attributes;
its `entity_type` is `ensemble-star`. A CellPack load creates a transform data
object plus molecule instance objects in a dedicated `cellpack_<name>`
collection under `.MN_data`; its `entity_type` is `ensemble-cellpack`. Keep the
returned entity and its `instance_collection` together when moving, deleting,
or saving a scene. Set `node_setup=False` for parser/ownership checks or when a
caller will build Geometry Nodes itself.

## Acceptance checks

- **Density:** the path is local and readable; the resulting object is in the
  Molecular Nodes collection; positions are non-empty; centered maps have a
  near-zero position centroid; and a selected threshold yields visible geometry.
- **STAR:** the file is recognized as supported RELION or cisTEM; coordinate,
  shift, pixel-size/defocus, rotation, image-id, and categorical attributes have
  expected lengths; and the object has `ensemble-star` metadata.
- **CellPack:** `.cif` and `.bcif` both parse when supplied; molecule IDs and
  transformations are non-empty; `instance_collection` exists; and the data
  object and instance objects are owned by the expected collections.
- **Cryo-EM:** map and structure use the same centering choice, and any color
  transfer samples an atom object rather than a ribbon-only display.

## Recovery discipline

Do not silently switch to an online EMDB request. On a missing or malformed map,
report the path and parser error, preserve the scene, and retry with a known
local fixture. Remove only an orphaned generated object or stale neighboring VDB
after checking that no other scene object references it. For an ensemble parse
failure, first identify the format and required metadata block; do not relabel a
STAR file as CellPack or vice versa. See the troubleshooting reference for
specific recovery branches.
