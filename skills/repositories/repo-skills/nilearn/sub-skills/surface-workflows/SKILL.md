---
name: surface-workflows
description: "Work with Nilearn surface meshes, surface images,
  volume-to-surface projection, fsaverage helpers, and surface maskers while
  routing plotting and raw image preparation to the right Nilearn skills."
disable-model-invocation: true
metadata:
  disco-role: operating
license: BSD 3-Clause
---

# Surface Workflows

Use this sub-skill when a task involves Nilearn cortical surface objects,
mesh/data contracts, `SurfaceImage` construction, volume-to-surface projection,
fsaverage meshes, or surface-specific maskers.

## Route Here

- Build or validate surface meshes with `InMemoryMesh`, `FileMesh`, `PolyMesh`,
  or `load_surf_mesh`.
- Build or validate surface data with `PolyData`, `load_surf_data`, or
  `SurfaceImage`.
- Project NIfTI volume data to surface vertices with `vol_to_surf` or
  `SurfaceImage.from_volume`.
- Load fsaverage meshes or fsaverage surface data with no-download awareness.
- Use `SurfaceMasker`, `SurfaceLabelsMasker`, or `SurfaceMapsMasker` enough to
  prepare arrays for analysis pipelines.

## Route Elsewhere

- For figure engine choices, `plot_surf`, `view_surf`, report display, Plotly,
  Matplotlib, or optional plotting dependencies, route to `../plotting-reporting/SKILL.md`.
- For raw NIfTI loading, resampling, confounds, signal cleaning, or volume image
  preparation before projection, route to `../data-io-signal/SKILL.md`.
- For deeper shared masker, labels, maps, atlas, and region-extraction behavior,
  route to `../maskers-regions/SKILL.md`; keep this sub-skill focused on
  surface-specific mesh/data contracts.

## Quick Checklist

1. Confirm whether the task is left-only, right-only, or both hemispheres.
2. Keep mesh parts and data parts keyed identically as `left` and/or `right`.
3. Match each data part's first dimension to the corresponding mesh vertex
   count before creating `SurfaceImage`.
4. Treat surface arrays as vertex-major: `(n_vertices,)` for a scalar map or
   `(n_vertices, n_samples_or_regions)` for time series, labels, or maps.
5. Avoid dataset downloads unless the user explicitly requests them; prefer the
   shipped `fsaverage5` helper for no-network examples.
6. Hand visualization choices off to plotting/reporting after producing a valid
   `SurfaceImage` or surface array.

## References

- `references/api-reference.md` summarizes public constructors, helpers, and
  object relationships.
- `references/data-formats.md` describes mesh, data, hemisphere, and file-format
  contracts.
- `references/workflows.md` gives recipes for minimal meshes, projection,
  fsaverage, surface maskers, and plotting handoff.
- `references/troubleshooting.md` maps common surface failures to likely fixes.

## Bundled Script

Run `python scripts/smoke_surface.py --help` for options or
`python scripts/smoke_surface.py` for a no-network sanity check that constructs
left/right in-memory meshes, builds a `SurfaceImage`, and verifies masker-style
array shapes.
